document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("costForm");
  const statusEl = document.getElementById("status");
  const resetBtn = document.getElementById("resetBtn");
  const totalPriceEl = document.getElementById("totalPrice");

  if (!form || !statusEl || !resetBtn || !totalPriceEl) {
    console.error("Missing required DOM elements (costForm/status/resetBtn/totalPrice).");
    return;
  }

  // Restore saved selections (optional)
  const saved = localStorage.getItem("last_costing_selection");
  if (saved) {
    const data = JSON.parse(saved);
    for (const key in data) {
      if (form.elements[key]) {
        form.elements[key].value = data[key];
      }
    }
  }

  // Auto-save on change (optional)
  form.addEventListener("change", () => {
    const data = Object.fromEntries(new FormData(form).entries());
    localStorage.setItem("last_costing_selection", JSON.stringify(data));
  });

  // Reset button (FULL PAGE RESET)
  resetBtn.addEventListener("click", () => {
    localStorage.removeItem("last_costing_selection");
    window.location.reload();
  });

  // Submit to Flask API
  form.addEventListener("submit", async (e) => {
    e.preventDefault();

    const data = Object.fromEntries(new FormData(form).entries());
    statusEl.textContent = "Saving...";

    try {
      const res = await fetch("/api/save", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(data)
      });

      const payload = await res.json().catch(() => ({}));

      if (!res.ok) {
        throw new Error(payload.error || "Failed to save");
      }

      statusEl.textContent = `Saved (ID ${payload.id}). Base USD: ${payload.base_total_usd}`;
      totalPriceEl.textContent = `${payload.total_price} ${payload.currency}`.trim();
    } catch (err) {
      statusEl.textContent = "Error: " + err.message;
    }
  });
});
