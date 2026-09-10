// Dark mode: persisted in localStorage, applied via a data-theme attribute
// on <html> so CSS can key off it with a simple selector — no framework
// needed for something this small.
(function () {
  const root = document.documentElement;
  const saved = localStorage.getItem("theme");
  if (saved === "dark") {
    root.setAttribute("data-theme", "dark");
  }

  document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("theme-toggle");
    if (!toggle) return;

    toggle.textContent = root.getAttribute("data-theme") === "dark" ? "☀️" : "🌙";

    toggle.addEventListener("click", () => {
      const isDark = root.getAttribute("data-theme") === "dark";
      if (isDark) {
        root.removeAttribute("data-theme");
        localStorage.setItem("theme", "light");
        toggle.textContent = "🌙";
      } else {
        root.setAttribute("data-theme", "dark");
        localStorage.setItem("theme", "dark");
        toggle.textContent = "☀️";
      }
    });
  });
})();

// Register the service worker so the app becomes installable and its
// shell (styling, icons) loads even with no connection.
if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js");
  });
}