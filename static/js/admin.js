(function () {
  function enforceDecimalPoint(input) {
    input.addEventListener("input", () => {
      input.value = input.value.replace(",", ".").replace(/[^0-9.]/g, "");
    });
  }

  function enforceSignedDecimal(input) {
    input.addEventListener("input", () => {
      input.value = input.value.replace(",", ".").replace(/[^0-9.\-]/g, "");
    });
  }

  async function getJson(url) {
    const response = await fetch(url);
    if (!response.ok) throw new Error("Pyyntö epäonnistui: " + url);
    return response.json();
  }

  async function postJson(url, body) {
    const response = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Tallennus epäonnistui");
    }
    return response.json();
  }

  async function putJson(url, body) {
    const response = await fetch(url, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!response.ok) {
      const data = await response.json().catch(() => ({}));
      throw new Error(data.detail || "Tallennus epäonnistui");
    }
    return response.json();
  }

  // ---------------- Users ----------------
  async function initUsersPage() {
    const table = document.getElementById("users-table");
    if (!table) return;
    const tbody = table.querySelector("tbody");
    const form = document.getElementById("new-user-form");
    const errorBox = document.getElementById("users-error");

    async function refresh() {
      const users = await getJson("/api/admin/users");
      tbody.innerHTML = "";
      users.forEach((u) => {
        const tr = document.createElement("tr");
        tr.innerHTML =
          "<td>" + u.full_name + "</td><td>" + u.balance + " €</td>" +
          "<td><input type='checkbox' data-field='is_active' " + (u.is_active ? "checked" : "") + " /></td>" +
          "<td><input type='checkbox' data-field='is_admin' " + (u.is_admin ? "checked" : "") + " /></td>" +
          "<td><button data-action='save' data-id='" + u.id + "'>Tallenna</button></td>" +
          "<td style='display:flex; gap:0.3em;'>" +
          "<input type='text' inputmode='decimal' data-field='adjustment-amount' placeholder='+5.00 / -5.00' style='width:7em;' />" +
          "<button type='button' data-action='adjust'>Lisää</button></td>";

        tr.querySelector("[data-action='save']").addEventListener("click", async () => {
          const isActive = tr.querySelector("[data-field='is_active']").checked;
          const isAdmin = tr.querySelector("[data-field='is_admin']").checked;
          await putJson("/api/admin/users/" + u.id, {
            full_name: u.full_name,
            is_active: isActive,
            is_admin: isAdmin,
            new_pin: null,
          });
          await refresh();
        });

        const adjustmentInput = tr.querySelector("[data-field='adjustment-amount']");
        enforceSignedDecimal(adjustmentInput);
        tr.querySelector("[data-action='adjust']").addEventListener("click", async () => {
          if (!adjustmentInput.value) return;
          errorBox.textContent = "";
          try {
            await postJson("/api/admin/users/" + u.id + "/adjust-balance", {
              amount: adjustmentInput.value,
              description: "Ylläpidon saldon muutos",
            });
            await refresh();
          } catch (err) {
            errorBox.textContent = err.message;
          }
        });

        tbody.appendChild(tr);
      });
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.textContent = "";
      try {
        await postJson("/api/admin/users", {
          full_name: document.getElementById("nu-name").value,
          pin: document.getElementById("nu-pin").value,
          is_admin: document.getElementById("nu-admin").checked,
        });
        form.reset();
        await refresh();
      } catch (err) {
        errorBox.textContent = err.message;
      }
    });

    await refresh();
  }

  // ---------------- Categories ----------------
  async function initCategoriesPage() {
    const table = document.getElementById("categories-table");
    if (!table) return;
    const tbody = table.querySelector("tbody");
    const form = document.getElementById("new-category-form");
    const errorBox = document.getElementById("categories-error");

    async function refresh() {
      const categories = await getJson("/api/admin/categories");
      tbody.innerHTML = "";
      categories.forEach((c) => {
        const tr = document.createElement("tr");
        tr.innerHTML =
          "<td><input type='text' data-field='name' value='" + c.name.replace(/'/g, "&#39;") + "' /></td>" +
          "<td><input type='number' data-field='sort_order' value='" + c.sort_order + "' style='width:5em;' /></td>" +
          "<td><button type='button' data-action='save'>Tallenna</button></td>";

        tr.querySelector("[data-action='save']").addEventListener("click", async () => {
          errorBox.textContent = "";
          try {
            await putJson("/api/admin/categories/" + c.id, {
              name: tr.querySelector("[data-field='name']").value,
              sort_order: Number(tr.querySelector("[data-field='sort_order']").value),
            });
            await refresh();
          } catch (err) {
            errorBox.textContent = err.message;
          }
        });

        tbody.appendChild(tr);
      });
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.textContent = "";
      try {
        await postJson("/api/admin/categories", {
          name: document.getElementById("nc-name").value,
          sort_order: Number(document.getElementById("nc-order").value),
        });
        form.reset();
        await refresh();
      } catch (err) {
        errorBox.textContent = err.message;
      }
    });

    await refresh();
  }

  // ---------------- Products + recipes ----------------
  async function initProductsPage() {
    const table = document.getElementById("products-table");
    if (!table) return;
    const tbody = table.querySelector("tbody");
    const form = document.getElementById("product-form");
    const categorySelect = document.getElementById("pf-category");
    const recipeLinesContainer = document.getElementById("pf-recipe-lines");
    const addLineButton = document.getElementById("pf-add-line");
    const errorBox = document.getElementById("product-error");

    let inventoryOptions = [];

    function addRecipeLineRow(inventoryItemId, quantity) {
      const row = document.createElement("div");
      row.style.display = "flex";
      row.style.gap = "0.5em";
      row.style.marginBottom = "0.4em";

      const select = document.createElement("select");
      select.style.flex = "2";
      inventoryOptions.forEach((opt) => {
        const optionEl = document.createElement("option");
        optionEl.value = opt.id;
        optionEl.textContent = opt.name + " (" + opt.unit + ")";
        select.appendChild(optionEl);
      });
      if (inventoryItemId) select.value = inventoryItemId;

      const qtyInput = document.createElement("input");
      qtyInput.type = "text";
      qtyInput.inputMode = "decimal";
      qtyInput.placeholder = "määrä";
      qtyInput.style.flex = "1";
      qtyInput.value = quantity != null ? quantity : "";
      enforceDecimalPoint(qtyInput);

      const removeBtn = document.createElement("button");
      removeBtn.type = "button";
      removeBtn.textContent = "Poista";
      removeBtn.addEventListener("click", () => row.remove());

      row.appendChild(select);
      row.appendChild(qtyInput);
      row.appendChild(removeBtn);
      row.dataset.recipeLine = "true";
      recipeLinesContainer.appendChild(row);
    }

    addLineButton.addEventListener("click", () => addRecipeLineRow(null, null));

    function resetForm() {
      document.getElementById("pf-id").value = "";
      document.getElementById("pf-name").value = "";
      document.getElementById("pf-price").value = "";
      document.getElementById("pf-active").checked = true;
      document.getElementById("pf-on-sale").checked = true;
      recipeLinesContainer.innerHTML = "";
    }
    document.getElementById("pf-reset").addEventListener("click", resetForm);

    async function refresh() {
      const [products, categories, inventoryItems] = await Promise.all([
        getJson("/api/admin/products"),
        getJson("/api/admin/categories"),
        getJson("/api/admin/recipes/inventory-options"),
      ]);
      inventoryOptions = inventoryItems;

      categorySelect.innerHTML = "";
      categories.forEach((c) => {
        const opt = document.createElement("option");
        opt.value = c.id;
        opt.textContent = c.name;
        categorySelect.appendChild(opt);
      });

      tbody.innerHTML = "";
      products.forEach((p) => {
        const tr = document.createElement("tr");
        const recipeSummary = p.recipe_lines
          .map((rl) => rl.inventory_item_name + " " + rl.quantity_required + rl.unit)
          .join(", ");
        tr.innerHTML =
          "<td>" + p.name + "</td><td>" + p.category_name + "</td><td>" + p.price + " €</td>" +
          "<td>" + (p.is_active ? "Kyllä" : "Ei") + "</td><td>" + (p.is_on_sale ? "Kyllä" : "Ei") + "</td>" +
          "<td>" + recipeSummary + " <button data-action='edit'>Muokkaa</button></td>";
        tr.querySelector("[data-action='edit']").addEventListener("click", () => {
          document.getElementById("pf-id").value = p.id;
          document.getElementById("pf-name").value = p.name;
          categorySelect.value = p.category_id;
          document.getElementById("pf-price").value = p.price;
          document.getElementById("pf-active").checked = p.is_active;
          document.getElementById("pf-on-sale").checked = p.is_on_sale;
          recipeLinesContainer.innerHTML = "";
          p.recipe_lines.forEach((rl) => addRecipeLineRow(rl.inventory_item_id, rl.quantity_required));
          window.scrollTo({ top: form.offsetTop, behavior: "smooth" });
        });
        tbody.appendChild(tr);
      });
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.textContent = "";

      const recipeRows = Array.from(recipeLinesContainer.querySelectorAll("[data-recipe-line]"));
      const recipeLines = recipeRows.map((row) => {
        const select = row.querySelector("select");
        const qtyInput = row.querySelector("input");
        return { inventory_item_id: Number(select.value), quantity_required: qtyInput.value };
      });

      const payload = {
        name: document.getElementById("pf-name").value,
        category_id: Number(categorySelect.value),
        price: document.getElementById("pf-price").value,
        is_active: document.getElementById("pf-active").checked,
        is_on_sale: document.getElementById("pf-on-sale").checked,
        recipe_lines: recipeLines,
      };

      const productId = document.getElementById("pf-id").value;
      try {
        if (productId) {
          await putJson("/api/admin/products/" + productId, payload);
        } else {
          await postJson("/api/admin/products", payload);
        }
        resetForm();
        await refresh();
      } catch (err) {
        errorBox.textContent = err.message;
      }
    });

    await refresh();
  }

  // ---------------- Recipes overview ----------------
  async function initRecipesPage() {
    const table = document.getElementById("recipes-table");
    if (!table) return;
    const tbody = table.querySelector("tbody");

    const products = await getJson("/api/admin/recipes/products-with-recipes");
    tbody.innerHTML = "";
    products.forEach((p) => {
      const tr = document.createElement("tr");
      const recipeSummary = p.recipe_lines
        .map((rl) => rl.inventory_item_name + ": " + rl.quantity_required + " " + rl.unit)
        .join(", ");
      tr.innerHTML = "<td>" + p.name + "</td><td>" + (recipeSummary || "—") + "</td>";
      tbody.appendChild(tr);
    });
  }

  // ---------------- Inventory ----------------
  async function initInventoryPage() {
    const table = document.getElementById("inventory-table");
    if (!table) return;
    const tbody = table.querySelector("tbody");
    const newItemForm = document.getElementById("new-inventory-item-form");
    const correctionForm = document.getElementById("correction-form");
    const wastageForm = document.getElementById("wastage-form");
    const cfItemSelect = document.getElementById("cf-item");
    const wfItemSelect = document.getElementById("wf-item");
    const errorBox = document.getElementById("inventory-error");

    document.getElementById("cf-counted") && enforceDecimalPoint(document.getElementById("cf-counted"));
    document.getElementById("wf-quantity") && enforceDecimalPoint(document.getElementById("wf-quantity"));

    async function refresh() {
      const items = await getJson("/api/admin/inventory");
      tbody.innerHTML = "";
      cfItemSelect.innerHTML = "";
      wfItemSelect.innerHTML = "";
      items.forEach((i) => {
        const tr = document.createElement("tr");
        tr.innerHTML =
          "<td>" + i.name + "</td><td>" + i.unit + "</td><td>" + i.quantity_in_stock + "</td>" +
          "<td><input type='text' inputmode='decimal' data-field='threshold' value='" +
          (i.low_stock_threshold || "") + "' style='width:6em;' placeholder='ei käytössä' /></td>" +
          "<td><button type='button' data-action='save-threshold'>Tallenna</button></td>";

        const thresholdInput = tr.querySelector("[data-field='threshold']");
        enforceDecimalPoint(thresholdInput);
        tr.querySelector("[data-action='save-threshold']").addEventListener("click", async () => {
          errorBox.textContent = "";
          try {
            await putJson("/api/admin/inventory/" + i.id + "/low-stock-threshold", {
              threshold: thresholdInput.value || null,
            });
            await refresh();
          } catch (err) {
            errorBox.textContent = err.message;
          }
        });

        tbody.appendChild(tr);

        [cfItemSelect, wfItemSelect].forEach((select) => {
          const opt = document.createElement("option");
          opt.value = i.id;
          opt.textContent = i.name + " (" + i.unit + ")";
          select.appendChild(opt);
        });
      });
    }

    newItemForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.textContent = "";
      try {
        await postJson("/api/admin/inventory", {
          name: document.getElementById("ni-name").value,
          unit: document.getElementById("ni-unit").value,
        });
        newItemForm.reset();
        await refresh();
      } catch (err) {
        errorBox.textContent = err.message;
      }
    });

    correctionForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.textContent = "";
      try {
        await postJson("/api/admin/inventory/correction", {
          inventory_item_id: Number(cfItemSelect.value),
          counted_quantity: document.getElementById("cf-counted").value,
          description: document.getElementById("cf-description").value,
        });
        correctionForm.reset();
        await refresh();
      } catch (err) {
        errorBox.textContent = err.message;
      }
    });

    wastageForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.textContent = "";
      try {
        await postJson("/api/admin/inventory/wastage", {
          inventory_item_id: Number(wfItemSelect.value),
          quantity: document.getElementById("wf-quantity").value,
          description: document.getElementById("wf-description").value,
        });
        wastageForm.reset();
        await refresh();
      } catch (err) {
        errorBox.textContent = err.message;
      }
    });

    await refresh();
  }

  // ---------------- Audit log ----------------
  async function initAuditPage() {
    const table = document.getElementById("audit-table");
    if (!table) return;
    const tbody = table.querySelector("tbody");
    const userSelect = document.getElementById("af-user");
    const productSelect = document.getElementById("af-product");
    const inventorySelect = document.getElementById("af-inventory");

    const [users, products, inventoryItems] = await Promise.all([
      getJson("/api/admin/users"),
      getJson("/api/admin/products"),
      getJson("/api/admin/inventory"),
    ]);

    users.forEach((u) => {
      const opt = document.createElement("option");
      opt.value = u.id;
      opt.textContent = u.full_name;
      userSelect.appendChild(opt);
    });
    products.forEach((p) => {
      const opt = document.createElement("option");
      opt.value = p.id;
      opt.textContent = p.name;
      productSelect.appendChild(opt);
    });
    inventoryItems.forEach((i) => {
      const opt = document.createElement("option");
      opt.value = i.id;
      opt.textContent = i.name;
      inventorySelect.appendChild(opt);
    });

    async function refresh() {
      const params = new URLSearchParams();
      if (userSelect.value) params.set("user_id", userSelect.value);
      if (document.getElementById("af-event-type").value) params.set("event_type", document.getElementById("af-event-type").value);
      if (productSelect.value) params.set("sales_product_id", productSelect.value);
      if (inventorySelect.value) params.set("inventory_item_id", inventorySelect.value);
      if (document.getElementById("af-date-from").value) params.set("date_from", document.getElementById("af-date-from").value);
      if (document.getElementById("af-date-to").value) params.set("date_to", document.getElementById("af-date-to").value);

      const entries = await getJson("/api/admin/audit?" + params.toString());
      tbody.innerHTML = "";
      entries.forEach((e) => {
        const tr = document.createElement("tr");
        tr.innerHTML =
          "<td>" + e.occurred_at.replace("T", " ").slice(0, 19) + "</td>" +
          "<td>" + (e.user_name || "—") + "</td>" +
          "<td>" + e.event_type + "</td>" +
          "<td>" + (e.sales_product_name || "—") + "</td>" +
          "<td>" + (e.inventory_item_name || "—") + "</td>" +
          "<td>" + (e.quantity || "—") + "</td>" +
          "<td>" + (e.amount || "—") + "</td>" +
          "<td>" + (e.description || "") + "</td>";
        tbody.appendChild(tr);
      });
    }

    document.getElementById("af-apply").addEventListener("click", refresh);
    await refresh();
  }

  // ---------------- Analytics ----------------
  async function initAnalyticsPage() {
    const salesTable = document.getElementById("sales-volume-table");
    if (!salesTable) return;

    function fillTable(tableId, rows, rowBuilder) {
      const tbody = document.getElementById(tableId).querySelector("tbody");
      tbody.innerHTML = "";
      rows.forEach((row) => {
        const tr = document.createElement("tr");
        tr.innerHTML = rowBuilder(row);
        tbody.appendChild(tr);
      });
    }

    const [salesVolume, wastage, userUsage, milk, coffeePots] = await Promise.all([
      getJson("/api/admin/analytics/sales-volume"),
      getJson("/api/admin/analytics/wastage"),
      getJson("/api/admin/analytics/user-usage"),
      getJson("/api/admin/analytics/milk-consumption"),
      getJson("/api/admin/analytics/coffee-pots"),
    ]);

    fillTable("sales-volume-table", salesVolume, (r) => "<td>" + r.product_name + "</td><td>" + r.units_sold + "</td><td>" + r.revenue + " €</td>");
    fillTable("wastage-table", wastage, (r) => "<td>" + r.item_name + "</td><td>" + r.unit + "</td><td>" + r.quantity + "</td>");
    fillTable("user-usage-table", userUsage, (r) => "<td>" + r.user_name + "</td><td>" + r.purchase_count + "</td><td>" + r.total_spent + " €</td>");
    fillTable("milk-table", milk, (r) => "<td>" + r.week + "</td><td>" + r.milk_ml + "</td>");
    fillTable("coffee-pots-table", coffeePots, (r) => "<td>" + r.estimated_brew_time.replace("T", " ").slice(0, 19) + "</td><td>" + r.cups_in_cluster + "</td><td>" + r.last_cup_at.replace("T", " ").slice(0, 19) + "</td>");
  }

  // ---------------- Settings (monthly fee + Signal) ----------------
  async function initSettingsPage() {
    const form = document.getElementById("settings-form");
    if (!form) return;
    const activeCheckbox = document.getElementById("sf-active");
    const amountInput = document.getElementById("sf-amount");
    const errorBox = document.getElementById("settings-error");
    const resultBox = document.getElementById("settings-result");
    const chargeNowButton = document.getElementById("charge-now-button");

    const signalForm = document.getElementById("signal-form");
    const sigNumberInput = document.getElementById("sig-number");
    const sigGroupInput = document.getElementById("sig-group");
    const signalErrorBox = document.getElementById("signal-error");

    enforceDecimalPoint(amountInput);

    async function refresh() {
      const settings = await getJson("/api/admin/settings");
      activeCheckbox.checked = settings.monthly_fee_active;
      amountInput.value = settings.monthly_fee_amount;
      sigNumberInput.value = settings.signal_sender_number || "";
      sigGroupInput.value = settings.signal_group_id || "";
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      errorBox.textContent = "";
      try {
        await putJson("/api/admin/settings", {
          monthly_fee_amount: amountInput.value || "0",
          monthly_fee_active: activeCheckbox.checked,
          signal_sender_number: sigNumberInput.value || null,
          signal_group_id: sigGroupInput.value || null,
        });
        await refresh();
      } catch (err) {
        errorBox.textContent = err.message;
      }
    });

    chargeNowButton.addEventListener("click", async () => {
      errorBox.textContent = "";
      resultBox.textContent = "";
      try {
        const result = await postJson("/api/admin/settings/charge-monthly-fee", {});
        resultBox.textContent = "Kuukausimaksu veloitettu " + result.charged_count + " käyttäjältä.";
      } catch (err) {
        errorBox.textContent = err.message;
      }
    });

    signalForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      signalErrorBox.textContent = "";
      try {
        await putJson("/api/admin/settings", {
          monthly_fee_amount: amountInput.value || "0",
          monthly_fee_active: activeCheckbox.checked,
          signal_sender_number: sigNumberInput.value || null,
          signal_group_id: sigGroupInput.value || null,
        });
        await refresh();
      } catch (err) {
        signalErrorBox.textContent = err.message;
      }
    });

    // ---- QR-code linking widget ----
    const qrDeviceNameInput = document.getElementById("qr-device-name");
    const generateQrButton = document.getElementById("generate-qr-button");
    const qrErrorBox = document.getElementById("qr-error");
    const qrImageWrapper = document.getElementById("qr-image-wrapper");
    let currentQrObjectUrl = null;

    generateQrButton.addEventListener("click", async () => {
      qrErrorBox.textContent = "";
      qrImageWrapper.innerHTML = "Ladataan…";
      try {
        const params = new URLSearchParams({ device_name: qrDeviceNameInput.value || "Kahvikassa-Bot" });
        const response = await fetch("/api/admin/settings/signal-qrcode?" + params.toString());
        if (!response.ok) {
          const data = await response.json().catch(() => ({}));
          throw new Error(data.detail || "QR-koodin luonti epäonnistui");
        }
        const blob = await response.blob();
        if (currentQrObjectUrl) URL.revokeObjectURL(currentQrObjectUrl);
        currentQrObjectUrl = URL.createObjectURL(blob);
        qrImageWrapper.innerHTML = "";
        const img = document.createElement("img");
        img.src = currentQrObjectUrl;
        img.alt = "Signal-linkitys QR-koodi";
        img.style.maxWidth = "240px";
        qrImageWrapper.appendChild(img);
        const note = document.createElement("p");
        note.className = "muted";
        note.textContent = "Skannaa nyt — koodi vanhenee noin minuutissa.";
        qrImageWrapper.appendChild(note);
      } catch (err) {
        qrImageWrapper.innerHTML = "";
        qrErrorBox.textContent = err.message;
      }
    });

    // ---- Account / group lookup helpers ----
    const lookupAccountsButton = document.getElementById("lookup-accounts-button");
    const accountsResult = document.getElementById("accounts-result");
    const groupsNumberSelect = document.getElementById("groups-number-select");
    const lookupGroupsButton = document.getElementById("lookup-groups-button");
    const groupsResult = document.getElementById("groups-result");
    const lookupErrorBox = document.getElementById("lookup-error");

    lookupAccountsButton.addEventListener("click", async () => {
      lookupErrorBox.textContent = "";
      accountsResult.innerHTML = "Haetaan…";
      try {
        const numbers = await getJson("/api/admin/settings/signal-accounts");
        accountsResult.innerHTML = "";
        groupsNumberSelect.innerHTML = "";
        numbers.forEach((numberValue) => {
          const row = document.createElement("div");
          const useButton = document.createElement("button");
          useButton.type = "button";
          useButton.textContent = "Käytä";
          useButton.addEventListener("click", () => {
            sigNumberInput.value = numberValue;
          });
          row.textContent = numberValue + " ";
          row.appendChild(useButton);
          accountsResult.appendChild(row);

          const opt = document.createElement("option");
          opt.value = numberValue;
          opt.textContent = numberValue;
          groupsNumberSelect.appendChild(opt);
        });
        if (numbers.length === 0) accountsResult.textContent = "Ei linkitettyjä numeroita.";
      } catch (err) {
        accountsResult.innerHTML = "";
        lookupErrorBox.textContent = err.message;
      }
    });

    lookupGroupsButton.addEventListener("click", async () => {
      lookupErrorBox.textContent = "";
      if (!groupsNumberSelect.value) {
        lookupErrorBox.textContent = "Hae ensin linkitetyt numerot.";
        return;
      }
      groupsResult.innerHTML = "Haetaan…";
      try {
        const groups = await getJson(
          "/api/admin/settings/signal-groups?number=" + encodeURIComponent(groupsNumberSelect.value)
        );
        groupsResult.innerHTML = "";
        groups.forEach((group) => {
          const row = document.createElement("div");
          const useButton = document.createElement("button");
          useButton.type = "button";
          useButton.textContent = "Käytä";
          useButton.addEventListener("click", () => {
            sigGroupInput.value = group.id;
          });
          row.textContent = (group.name || "(nimetön ryhmä)") + " ";
          row.appendChild(useButton);
          groupsResult.appendChild(row);
        });
        if (groups.length === 0) groupsResult.textContent = "Ei ryhmiä.";
      } catch (err) {
        groupsResult.innerHTML = "";
        lookupErrorBox.textContent = err.message;
      }
    });

    await refresh();
  }

  // ---------------- Version display (admin front page) ----------------
  async function initVersionDisplay() {
    const versionDisplay = document.getElementById("version-display");
    if (!versionDisplay) return;
    try {
      const info = await getJson("/api/admin/version");
      let text = "Versio: " + info.current;
      if (info.update_available) {
        text += " — uusi versio saatavilla (" + info.latest + "), päivitä palvelimella.";
      }
      versionDisplay.textContent = text;
    } catch (err) {
      versionDisplay.textContent = "Versio: ei saatavilla";
    }
  }

  // ---------------- Theme selector ----------------
  // New themes only need a new <option> here plus a matching
  // [data-theme="..."] block in style.css — nothing else changes.
  function initThemeToggle() {
    const select = document.getElementById("theme-select");
    if (!select) return;

    function applyTheme(theme) {
      if (theme && theme !== "gootti") {
        document.documentElement.setAttribute("data-theme", theme);
      } else {
        document.documentElement.removeAttribute("data-theme");
      }
    }

    const current = localStorage.getItem("kahvikassa-theme") || "gootti";
    select.value = current;
    applyTheme(current);

    select.addEventListener("change", () => {
      localStorage.setItem("kahvikassa-theme", select.value);
      applyTheme(select.value);
    });
  }

  initUsersPage();
  initCategoriesPage();
  initProductsPage();
  initRecipesPage();
  initInventoryPage();
  initAuditPage();
  initAnalyticsPage();
  initSettingsPage();
  initVersionDisplay();
  initThemeToggle();
})();
