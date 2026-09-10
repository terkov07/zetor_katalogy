// Dark mode: persisted in localStorage, applied via a data-theme attribute
// on <html> so CSS can key off it with a simple selector.
(function () {
  const root = document.documentElement;
  const saved = localStorage.getItem("theme");
  if (saved === "dark") {
    root.setAttribute("data-theme", "dark");
  }

  document.addEventListener("DOMContentLoaded", () => {
    const toggle = document.getElementById("theme-toggle");
    if (toggle) {
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
    }

    document.querySelectorAll("[data-track-download]").forEach((link) => {
      link.addEventListener("click", () => {
        const entry = {
          title: link.dataset.title || link.href,
          url: link.href,
          catalogueTitle: link.dataset.catalogueTitle || "",
          catalogueId: link.dataset.catalogueId || "",
          downloadedAt: new Date().toISOString(),
        };
        const list = JSON.parse(localStorage.getItem("zetor_downloads") || "[]");
        const filtered = list.filter((e) => e.url !== entry.url);
        filtered.unshift(entry);
        localStorage.setItem("zetor_downloads", JSON.stringify(filtered));
      });
    });
  });
})();

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/static/sw.js");
  });
}

function renderOfflineList(T) {
  const container = document.getElementById("offline-list");
  const clearAllBtn = document.getElementById("offline-clear-all");
  const list = JSON.parse(localStorage.getItem("zetor_downloads") || "[]");

  if (list.length === 0) {
    container.innerHTML = `<p class="muted">${T.noDownloads}</p>`;
    clearAllBtn.style.display = "none";
    return;
  }

  clearAllBtn.style.display = "inline-block";
  const ul = document.createElement("ul");
  ul.className = "section-list";

  list.forEach((entry, index) => {
    const li = document.createElement("li");
    const date = new Date(entry.downloadedAt).toLocaleDateString();
    li.innerHTML = `
      <a href="${entry.url}">${entry.title}</a>
      <span class="muted">${entry.catalogueTitle} &middot; ${date}</span>
      <button type="button" class="link-button" data-remove-index="${index}">${T.remove}</button>
    `;
    ul.appendChild(li);
  });

  container.innerHTML = "";
  container.appendChild(ul);

  container.querySelectorAll("[data-remove-index]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const i = parseInt(btn.dataset.removeIndex, 10);
      const current = JSON.parse(localStorage.getItem("zetor_downloads") || "[]");
      current.splice(i, 1);
      localStorage.setItem("zetor_downloads", JSON.stringify(current));
      renderOfflineList(T);
    });
  });

  clearAllBtn.onclick = () => {
    localStorage.removeItem("zetor_downloads");
    renderOfflineList(T);
  };
}