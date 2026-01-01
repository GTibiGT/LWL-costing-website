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

    // If Flask returned an error, show it
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({}));
      throw new Error(errBody.error || "Failed to save");
    }

    const result = await res.json(); // ✅ result exists only here

    // ✅ USD-only fields (no currency)
    statusEl.textContent =
      `Saved (ID ${result.id}). Cost per ball (USD): ${result.per_ball_usd}`;

    // If you have an output for total
    const totalPriceEl = document.getElementById("totalPrice");
    if (totalPriceEl) {
      totalPriceEl.textContent =
        `Total for ${result.quantity} balls: ${result.total_for_quantity_usd} USD`;
    }

  } catch (err) {
    //do NOT reference "result" here
    statusEl.textContent = "Error: " + err.message;
  }
});

});
