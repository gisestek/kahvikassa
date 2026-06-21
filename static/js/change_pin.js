(function () {
  const form = document.getElementById("change-pin-form");
  const currentInput = document.getElementById("cp-current");
  const newInput = document.getElementById("cp-new");
  const newRepeatInput = document.getElementById("cp-new-repeat");
  const errorBox = document.getElementById("change-pin-error");
  const successBox = document.getElementById("change-pin-success");

  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    errorBox.textContent = "";
    successBox.textContent = "";

    if (newInput.value !== newRepeatInput.value) {
      errorBox.textContent = "Uudet PIN-koodit eivät täsmää";
      return;
    }

    try {
      const response = await fetch("/api/auth/change-pin", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ current_pin: currentInput.value, new_pin: newInput.value }),
      });
      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        errorBox.textContent = data.detail || "PIN-koodin vaihto epäonnistui";
        return;
      }
      successBox.textContent = "PIN-koodi vaihdettu onnistuneesti.";
      form.reset();
    } catch (err) {
      errorBox.textContent = "Yhteysvirhe";
    }
  });
})();
