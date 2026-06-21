(function () {
  const form = document.getElementById("supply-form");
  const existingFields = document.getElementById("existing-item-fields");
  const newFields = document.getElementById("new-item-fields");
  const itemSelect = document.getElementById("inventory-item-select");
  const newItemName = document.getElementById("new-item-name");
  const newItemUnit = document.getElementById("new-item-unit");
  const quantityInput = document.getElementById("supply-quantity");
  const costInput = document.getElementById("supply-cost");
  const errorBox = document.getElementById("supply-error");

  function enforceDecimalPoint(input) {
    input.addEventListener("input", () => {
      input.value = input.value.replace(",", ".").replace(/[^0-9.]/g, "");
    });
  }
  enforceDecimalPoint(quantityInput);
  enforceDecimalPoint(costInput);

  document.querySelectorAll('input[name="target_mode"]').forEach((radio) => {
    radio.addEventListener("change", () => {
      const isExisting = document.querySelector('input[name="target_mode"]:checked').value === "existing";
      existingFields.style.display = isExisting ? "" : "none";
      newFields.style.display = isExisting ? "none" : "";
    });
  });

  async function loadInventoryItems() {
    const response = await fetch("/api/supply/inventory-items");
    const items = await response.json();
    itemSelect.innerHTML = "";
    items.forEach((item) => {
      const option = document.createElement("option");
      option.value = item.id;
      option.textContent = item.name + " (" + item.unit + ")";
      itemSelect.appendChild(option);
    });
  }

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.textContent = "";

    const isExisting = document.querySelector('input[name="target_mode"]:checked').value === "existing";

    const payload = {
      quantity: quantityInput.value,
      total_cost: costInput.value || "0",
    };

    if (isExisting) {
      payload.inventory_item_id = Number(itemSelect.value);
    } else {
      payload.new_item = { name: newItemName.value, unit: newItemUnit.value };
    }

    try {
      const response = await fetch("/api/supply/ingest", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        errorBox.textContent = data.detail || "Tallennus epäonnistui";
        return;
      }
      window.location.href = "/kioski";
    } catch (err) {
      errorBox.textContent = "Yhteysvirhe";
    }
  });

  loadInventoryItems();
})();
