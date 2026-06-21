(function () {
  const balanceDisplay = document.getElementById("balance-display");
  const productGroups = document.getElementById("product-groups");
  const cartList = document.getElementById("cart-list");
  const cartTotal = document.getElementById("cart-total");
  const kioskError = document.getElementById("kiosk-error");
  const btnOk = document.getElementById("btn-ok");
  const btnCancel = document.getElementById("btn-cancel");
  const btnLogout = document.getElementById("btn-logout");

  // cart: Map productId -> { name, price (number), quantity }
  const cart = new Map();

  async function loadCurrentUser() {
    const response = await fetch("/api/auth/me");
    if (!response.ok) {
      window.location.href = "/";
      return;
    }
    const user = await response.json();
    balanceDisplay.textContent = "Saldo: " + Number(user.balance).toFixed(2) + " €";
  }

  async function loadProducts() {
    const response = await fetch("/api/kiosk/products");
    const groups = await response.json();

    productGroups.innerHTML = "";
    let renderedAnyGroup = false;
    groups.forEach((group) => {
      if (group.products.length === 0) return;

      // Category names are an admin-side grouping concept only; the kiosk
      // shows just a plain divider between groups, not the group's name.
      if (renderedAnyGroup) {
        const separator = document.createElement("hr");
        separator.className = "category-separator";
        productGroups.appendChild(separator);
      }
      renderedAnyGroup = true;

      const block = document.createElement("div");
      block.className = "category-block";

      const grid = document.createElement("div");
      grid.className = "product-grid";

      group.products.forEach((product) => {
        const button = document.createElement("button");
        button.className = "product-button";
        button.innerHTML =
          "<span>" + product.name + "</span><span class='product-price'>" +
          Number(product.price).toFixed(2) + " €</span>";
        button.addEventListener("click", () => addToCart(product));
        grid.appendChild(button);
      });

      block.appendChild(grid);
      productGroups.appendChild(block);
    });
  }

  function addToCart(product) {
    const existing = cart.get(product.id);
    if (existing) {
      existing.quantity += 1;
    } else {
      cart.set(product.id, { name: product.name, price: Number(product.price), quantity: 1 });
    }
    renderCart();
  }

  function removeFromCart(productId) {
    const existing = cart.get(productId);
    if (!existing) return;
    existing.quantity -= 1;
    if (existing.quantity <= 0) cart.delete(productId);
    renderCart();
  }

  function renderCart() {
    cartList.innerHTML = "";
    let total = 0;

    cart.forEach((item, productId) => {
      total += item.price * item.quantity;
      const li = document.createElement("li");
      li.innerHTML =
        "<span>" + item.name + " x " + item.quantity + "</span>" +
        "<span>" + (item.price * item.quantity).toFixed(2) + " € " +
        "<button class='cart-remove-btn' data-product-id='" + productId + "'>Poista</button></span>";
      cartList.appendChild(li);
    });

    cartTotal.textContent = "Yhteensä: " + total.toFixed(2) + " €";
  }

  cartList.addEventListener("click", (event) => {
    const button = event.target.closest(".cart-remove-btn");
    if (!button) return;
    removeFromCart(Number(button.dataset.productId));
  });

  async function endSession(redirectAfter) {
    window.location.href = redirectAfter;
  }

  btnOk.addEventListener("click", async () => {
    kioskError.textContent = "";
    if (cart.size === 0) {
      kioskError.textContent = "Ostoskori on tyhjä";
      return;
    }

    const items = Array.from(cart.entries()).map(([productId, item]) => ({
      sales_product_id: productId,
      quantity: item.quantity,
    }));

    try {
      const response = await fetch("/api/kiosk/checkout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ items }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        kioskError.textContent = data.detail || "Maksu epäonnistui";
        return;
      }
      await endSession("/");
    } catch (err) {
      kioskError.textContent = "Yhteysvirhe";
    }
  });

  btnCancel.addEventListener("click", async () => {
    try {
      await fetch("/api/kiosk/cancel", { method: "POST" });
    } finally {
      await endSession("/");
    }
  });

  btnLogout.addEventListener("click", async () => {
    try {
      await fetch("/api/auth/logout", { method: "POST" });
    } finally {
      await endSession("/");
    }
  });

  loadCurrentUser();
  loadProducts();
})();
