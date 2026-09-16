document.addEventListener("DOMContentLoaded", () => {
  // Dark mode: persisted in localStorage, applied via a data-theme
  // attribute on <html> so CSS can key off it with a simple selector.
  const root = document.documentElement;
  const saved = localStorage.getItem("theme");
  if (saved === "dark") {
    root.setAttribute("data-theme", "dark");
  }
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

  // Downloads: record to localStorage the instant the link is clicked —
  // this fires synchronously, before the browser's own download begins,
  // so it's reliable regardless of how the browser/device handles the
  // actual save. The real file download itself is handled entirely by
  // the browser, following the server's Content-Disposition header
  // (confirmed the reliable approach — a JS-triggered fetch+blob save
  // turned out to be less consistent on Android Chrome specifically).
  document.querySelectorAll(".download-link").forEach((link) => {
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

// Register the service worker so the app becomes installable and its
// shell (styling, icons) loads even with no connection.
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
    li.className = "row";
    const date = new Date(entry.downloadedAt).toLocaleDateString();
    li.innerHTML = `
      <span>${entry.title}</span>
      <span class="muted">${entry.catalogueTitle} &middot; ${date}</span>
      <button type="button" class="link-button row-action" data-remove-index="${index}">${T.remove}</button>
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