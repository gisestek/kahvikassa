(function () {
  const userGrid = document.getElementById("user-grid");
  const pinPanel = document.getElementById("pin-panel");
  const pinTitle = document.getElementById("pin-panel-title");
  const pinInput = document.getElementById("pin-input");
  const pinError = document.getElementById("pin-error");
  const pinSubmit = document.getElementById("pin-submit");

  let selectedUserId = null;

  userGrid.addEventListener("click", (event) => {
    const button = event.target.closest(".user-button");
    if (!button) return;

    userGrid.querySelectorAll(".user-button").forEach((b) => b.classList.remove("selected"));
    button.classList.add("selected");

    selectedUserId = Number(button.dataset.userId);
    pinTitle.textContent = button.dataset.userName + " — PIN-koodi";
    pinPanel.classList.add("visible");
    pinError.textContent = "";
    pinInput.value = "";
    pinInput.focus();
  });

  async function submitLogin() {
    if (selectedUserId === null) return;

    pinError.textContent = "";
    try {
      const response = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: selectedUserId, pin: pinInput.value }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        pinError.textContent = data.detail || "Kirjautuminen epäonnistui";
        pinInput.value = "";
        pinInput.focus();
        return;
      }
      const data = await response.json();
      window.location.href = data.redirect_to;
    } catch (err) {
      pinError.textContent = "Yhteysvirhe";
    }
  }

  pinInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") submitLogin();
  });

  pinSubmit.addEventListener("click", submitLogin);
})();
