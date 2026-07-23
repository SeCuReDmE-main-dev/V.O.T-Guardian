const root = document.documentElement;
const menuButton = document.querySelector(".menu-button");
const siteNav = document.querySelector("#site-nav");
const themeToggle = document.querySelector("[data-theme-toggle]");
const languageToggle = document.querySelector("[data-lang-toggle]");
const accessToggle = document.querySelector("[data-access-toggle]");

function setTheme(theme) {
  root.dataset.theme = theme;
  if (themeToggle) {
    themeToggle.textContent = theme === "light" ? "Theme: Light" : "Theme: Night";
  }
  localStorage.setItem("vot-guardian-theme", theme);
}

const savedTheme = localStorage.getItem("vot-guardian-theme");
if (savedTheme === "light" || savedTheme === "dark") {
  setTheme(savedTheme);
}

menuButton?.addEventListener("click", () => {
  const open = siteNav?.classList.toggle("is-open") ?? false;
  menuButton.setAttribute("aria-expanded", String(open));
});

siteNav?.addEventListener("click", (event) => {
  if (event.target instanceof HTMLAnchorElement) {
    siteNav.classList.remove("is-open");
    menuButton?.setAttribute("aria-expanded", "false");
  }
});

themeToggle?.addEventListener("click", () => {
  setTheme(root.dataset.theme === "light" ? "dark" : "light");
});

languageToggle?.addEventListener("click", () => {
  const isFrench = languageToggle.textContent?.includes("FR");
  languageToggle.textContent = isFrench ? "Language: EN" : "Language: FR";
});

accessToggle?.addEventListener("click", () => {
  document.body.classList.toggle("access-mode");
  accessToggle.textContent = document.body.classList.contains("access-mode") ? "Access: Calm" : "Access";
});
