from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditEventType, AuditLogEntry
from app.models.product import ProductCategory, SalesProduct
from app.models.recipe import RecipeLine
from app.models.settings import AppSettings
from app.models.user import User
from app.security import hash_pin
from app.services.notification_service import format_monthly_fee_message, send_signal_message

# id of the singleton app_settings row, seeded by migration 0003.
APP_SETTINGS_ROW_ID = 1


async def list_all_users(db: AsyncSession) -> list[User]:
    result = await db.execute(select(User).order_by(User.full_name))
    return list(result.scalars().all())


async def create_user(db: AsyncSession, full_name: str, pin: str, is_admin: bool = False) -> User:
    user = User(full_name=full_name, pin_hash=hash_pin(pin), is_admin=is_admin)
    db.add(user)
    await db.commit()
    return user


async def update_user(
    db: AsyncSession, user_id: int, full_name: str, is_active: bool, is_admin: bool, new_pin: str | None
) -> User:
    user = await db.get(User, user_id)
    if user is None:
        raise ValueError("Käyttäjää ei löytynyt")
    user.full_name = full_name
    user.is_active = is_active
    user.is_admin = is_admin
    if new_pin:
        user.pin_hash = hash_pin(new_pin)
    await db.commit()
    return user


async def adjust_user_balance(
    db: AsyncSession, admin_user: User, user_id: int, amount: Decimal, description: str
) -> User:
    """Manually credits or debits a user's balance (e.g. cash handed over in
    person, or correcting a mistake). Always logged as ADMIN_ADJUSTMENT so the
    audit trail shows who authorized it and why."""
    user = await db.get(User, user_id)
    if user is None:
        raise ValueError("Käyttäjää ei löytynyt")

    user.balance += amount
    db.add(
        AuditLogEntry(
            user_id=user.id,
            event_type=AuditEventType.ADMIN_ADJUSTMENT,
            amount=amount,
            description=description or f"Ylläpidon saldokorjaus ({admin_user.full_name})",
        )
    )
    await db.commit()
    return user


async def get_app_settings(db: AsyncSession) -> AppSettings:
    settings = await db.get(AppSettings, APP_SETTINGS_ROW_ID)
    if settings is None:
        settings = AppSettings(id=APP_SETTINGS_ROW_ID, monthly_fee_amount=Decimal("0.00"), monthly_fee_active=False)
        db.add(settings)
        await db.commit()
    return settings


async def update_app_settings(
    db: AsyncSession,
    monthly_fee_amount: Decimal,
    monthly_fee_active: bool,
    signal_sender_number: str | None,
    signal_group_id: str | None,
) -> AppSettings:
    settings = await get_app_settings(db)
    settings.monthly_fee_amount = monthly_fee_amount
    settings.monthly_fee_active = monthly_fee_active
    settings.signal_sender_number = signal_sender_number or None
    settings.signal_group_id = signal_group_id or None
    await db.commit()
    return settings


async def charge_monthly_fee_to_all_active_users(db: AsyncSession, admin_user: User) -> int:
    """Charges the configured monthly fee once to every active user. There is
    no automatic scheduler — an admin triggers this manually (e.g. once a
    month), which keeps the trust-based system simple and avoids silently
    double-charging if triggered twice. Returns the number of users charged.
    """
    settings = await get_app_settings(db)
    if not settings.monthly_fee_active or settings.monthly_fee_amount <= 0:
        raise ValueError("Kuukausimaksu ei ole käytössä")

    result = await db.execute(select(User).where(User.is_active.is_(True)))
    users = list(result.scalars().all())

    for user in users:
        user.balance -= settings.monthly_fee_amount
        db.add(
            AuditLogEntry(
                user_id=user.id,
                event_type=AuditEventType.MONTHLY_FEE,
                amount=-settings.monthly_fee_amount,
                description=f"Kuukausimaksu ({admin_user.full_name} veloitti)",
            )
        )

    await db.commit()
    await send_signal_message(db, format_monthly_fee_message(len(users), settings.monthly_fee_amount))
    return len(users)


async def list_categories(db: AsyncSession) -> list[ProductCategory]:
    result = await db.execute(select(ProductCategory).order_by(ProductCategory.sort_order))
    return list(result.scalars().all())


async def upsert_category(db: AsyncSession, category_id: int | None, name: str, sort_order: int) -> ProductCategory:
    if category_id is not None:
        category = await db.get(ProductCategory, category_id)
        if category is None:
            raise ValueError("Tuoteryhmää ei löytynyt")
        category.name = name
        category.sort_order = sort_order
    else:
        category = ProductCategory(name=name, sort_order=sort_order)
        db.add(category)
    await db.commit()
    return category


async def list_sales_products(db: AsyncSession) -> list[SalesProduct]:
    result = await db.execute(
        select(SalesProduct).options(
            selectinload(SalesProduct.category),
            selectinload(SalesProduct.recipe_lines).selectinload(RecipeLine.inventory_item),
        ).order_by(SalesProduct.name)
    )
    return list(result.scalars().all())


async def upsert_sales_product(
    db: AsyncSession,
    product_id: int | None,
    name: str,
    category_id: int,
    price: Decimal,
    is_active: bool,
    is_on_sale: bool,
    recipe_lines: list[tuple[int, Decimal]],
) -> SalesProduct:
    """Creates or fully replaces a sales product and its recipe. Recipe lines
    are replaced wholesale on every save rather than diffed, since recipes are
    small and this keeps the admin UI simple and avoids partial-update bugs."""
    if product_id is not None:
        product = await db.get(SalesProduct, product_id, options=[selectinload(SalesProduct.recipe_lines)])
        if product is None:
            raise ValueError("Tuotetta ei löytynyt")
        for existing_line in list(product.recipe_lines):
            await db.delete(existing_line)
        await db.flush()
    else:
        product = SalesProduct(name=name, category_id=category_id, price=price)
        db.add(product)

    product.name = name
    product.category_id = category_id
    product.price = price
    product.is_active = is_active
    product.is_on_sale = is_on_sale

    for inventory_item_id, quantity_required in recipe_lines:
        db.add(
            RecipeLine(
                sales_product=product, inventory_item_id=inventory_item_id, quantity_required=quantity_required
            )
        )

    await db.commit()
    return product
