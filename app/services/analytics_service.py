from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.audit import AuditEventType, AuditLogEntry
from app.models.product import SalesProduct
from app.models.recipe import RecipeLine

# Purchases of coffee-based products within this window are assumed to share
# the same freshly brewed pot. This is a pure analytics heuristic — it never
# touches inventory and is only used to *estimate* brewing frequency, since
# the system has no explicit "pot brewed" event to log against.
POT_CLUSTERING_WINDOW = timedelta(minutes=20)


async def weekly_product_sales_volume(db: AsyncSession, weeks_back: int = 8) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(weeks=weeks_back)
    result = await db.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.event_type == AuditEventType.PURCHASE, AuditLogEntry.occurred_at >= cutoff)
        .options(selectinload(AuditLogEntry.sales_product))
    )
    entries = result.scalars().all()

    totals: dict[str, dict] = {}
    for entry in entries:
        if entry.sales_product is None:
            continue
        key = entry.sales_product.name
        totals.setdefault(key, {"product_name": key, "units_sold": 0, "revenue": Decimal("0.00")})
        totals[key]["units_sold"] += int(entry.quantity or 0)
        totals[key]["revenue"] += -(entry.amount or Decimal("0.00"))

    return sorted(totals.values(), key=lambda row: row["units_sold"], reverse=True)


async def total_wastage_by_item(db: AsyncSession, weeks_back: int = 8) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(weeks=weeks_back)
    result = await db.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.event_type == AuditEventType.WASTAGE, AuditLogEntry.occurred_at >= cutoff)
        .options(selectinload(AuditLogEntry.inventory_item))
    )
    entries = result.scalars().all()

    totals: dict[str, dict] = {}
    for entry in entries:
        if entry.inventory_item is None:
            continue
        key = entry.inventory_item.name
        totals.setdefault(key, {"item_name": key, "unit": entry.inventory_item.unit.value, "quantity": Decimal("0")})
        totals[key]["quantity"] += -(entry.quantity or Decimal("0"))

    return sorted(totals.values(), key=lambda row: row["quantity"], reverse=True)


async def user_usage_patterns(db: AsyncSession, weeks_back: int = 8) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(weeks=weeks_back)
    result = await db.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.event_type == AuditEventType.PURCHASE, AuditLogEntry.occurred_at >= cutoff)
        .options(selectinload(AuditLogEntry.user))
    )
    entries = result.scalars().all()

    totals: dict[int, dict] = {}
    for entry in entries:
        if entry.user is None:
            continue
        totals.setdefault(
            entry.user.id, {"user_name": entry.user.full_name, "purchase_count": 0, "total_spent": Decimal("0.00")}
        )
        totals[entry.user.id]["purchase_count"] += 1
        totals[entry.user.id]["total_spent"] += -(entry.amount or Decimal("0.00"))

    return sorted(totals.values(), key=lambda row: row["total_spent"], reverse=True)


async def milk_consumption_per_week(db: AsyncSession, weeks_back: int = 8) -> list[dict]:
    """Sums recipe-implied milk usage from purchases, bucketed by ISO week.
    This is derived from PURCHASE quantities and product recipes at query time
    rather than logged inventory deductions, so it stays accurate even if
    recipes changed mid-history is acceptable as an estimate, not ground truth."""
    cutoff = datetime.utcnow() - timedelta(weeks=weeks_back)
    result = await db.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.event_type == AuditEventType.PURCHASE, AuditLogEntry.occurred_at >= cutoff)
        .options(
            selectinload(AuditLogEntry.sales_product)
            .selectinload(SalesProduct.recipe_lines)
            .selectinload(RecipeLine.inventory_item)
        )
    )
    entries = result.scalars().all()

    weekly_totals: dict[str, Decimal] = {}
    for entry in entries:
        product = entry.sales_product
        if product is None:
            continue
        milk_per_unit = next(
            (
                rl.quantity_required
                for rl in product.recipe_lines
                if rl.inventory_item is not None and "maito" in rl.inventory_item.name.lower()
            ),
            None,
        )
        if milk_per_unit is None:
            continue
        iso_year, iso_week, _ = entry.occurred_at.isocalendar()
        week_key = f"{iso_year}-W{iso_week:02d}"
        weekly_totals[week_key] = weekly_totals.get(week_key, Decimal("0")) + milk_per_unit * int(entry.quantity or 0)

    return [{"week": k, "milk_ml": v} for k, v in sorted(weekly_totals.items())]


async def estimate_coffee_pots_brewed(db: AsyncSession, weeks_back: int = 4) -> list[dict]:
    """Clusters coffee-product purchases that occur close together in time and
    treats each cluster as one likely pot of coffee. Purely an analytical
    estimate layered on top of the immutable audit log — it never writes
    anything back and has zero effect on inventory or balances.
    """
    cutoff = datetime.utcnow() - timedelta(weeks=weeks_back)
    result = await db.execute(
        select(AuditLogEntry)
        .where(AuditLogEntry.event_type == AuditEventType.PURCHASE, AuditLogEntry.occurred_at >= cutoff)
        .options(selectinload(AuditLogEntry.sales_product))
        .order_by(AuditLogEntry.occurred_at)
    )
    entries = [
        e
        for e in result.scalars().all()
        if e.sales_product is not None and "kahvi" in e.sales_product.name.lower()
    ]

    clusters: list[dict] = []
    current_cluster: list[AuditLogEntry] = []

    for entry in entries:
        if current_cluster and entry.occurred_at - current_cluster[-1].occurred_at > POT_CLUSTERING_WINDOW:
            clusters.append(_summarize_pot_cluster(current_cluster))
            current_cluster = []
        current_cluster.append(entry)

    if current_cluster:
        clusters.append(_summarize_pot_cluster(current_cluster))

    return clusters


def _summarize_pot_cluster(cluster: list[AuditLogEntry]) -> dict:
    cups = sum(int(e.quantity or 0) for e in cluster)
    return {
        "estimated_brew_time": cluster[0].occurred_at.isoformat(),
        "cups_in_cluster": cups,
        "last_cup_at": cluster[-1].occurred_at.isoformat(),
    }
