"use strict";

document.querySelectorAll("[data-toggle]").forEach((button) => {
  const panel = document.getElementById(button.dataset.toggle);
  if (!panel) return;
  button.hidden = false;
  panel.hidden = true;
  button.addEventListener("click", () => {
    const expanded = button.getAttribute("aria-expanded") === "true";
    button.setAttribute("aria-expanded", String(!expanded));
    panel.hidden = expanded;
  });
});
