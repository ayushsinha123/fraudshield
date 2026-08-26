/**
 * FraudShield — application shell & shared UI behavior
 */

(function () {
  "use strict";

  const ICONS = {
    shield: "assets/icons/shield.svg",
    dashboard: "assets/icons/dashboard.svg",
    "new-transaction": "assets/icons/new-transaction.svg",
    transactions: "assets/icons/transactions.svg",
    "risk-analysis": "assets/icons/analytics.svg",
    "voice-shield": "assets/icons/voice-shield.svg",
    "device-security": "assets/icons/device-security.svg",
    "security-alerts": "assets/icons/alerts.svg",
    "bank-review": "assets/icons/bank-review.svg",
    settings: "assets/icons/settings.svg",
    help: "assets/icons/help.svg",
    logout: "assets/icons/logout.svg",
    bell: "assets/icons/bell.svg",
    menu: "assets/icons/menu.svg",
    close: "assets/icons/close.svg",
  };

  /** Shell navigation — source of truth for sidebar links */
  const SHELL_NAVIGATION = [
    {
      section: "Overview",
      items: [
        { id: "dashboard", label: "Dashboard", href: "pages/dashboard.html", icon: "dashboard" },
        { id: "new-transaction", label: "New Transaction", href: "pages/new-transaction.html", icon: "new-transaction" },
        { id: "transactions", label: "Transactions", href: "pages/transactions.html", icon: "transactions" },
      ],
    },
    {
      section: "Analysis",
      items: [
        { id: "risk-analysis", label: "Risk Analysis", href: "pages/risk-analysis.html", icon: "risk-analysis" },
        { id: "voice-shield", label: "Voice Shield", href: "pages/voice-shield.html", icon: "voice-shield" },
        { id: "device-security", label: "Device Security", href: "pages/device-security.html", icon: "device-security" },
      ],
    },
    {
      section: "Security",
      items: [
        { id: "security-alerts", label: "Security Alerts", href: "pages/security-alerts.html", icon: "security-alerts", badge: 12 },
        { id: "bank-review", label: "Bank Review", href: "pages/bank-review.html", icon: "bank-review" },
      ],
    },
    {
      section: "Account",
      items: [
        { id: "settings", label: "Settings", href: "pages/settings.html", icon: "settings" },
        { id: "help", label: "Help & Support", href: "pages/help.html", icon: "help" },
      ],
    },
  ];

  const LOGOUT_ITEM = {
    id: "logout",
    label: "Logout",
    href: "pages/login.html",
    icon: "logout",
    isLogout: true,
  };

  const PAGE_TITLE_MAP = {
    dashboard: "Dashboard",
    "new-transaction": "New Transaction",
    transactions: "Transactions",
    "risk-analysis": "Risk Analysis",
    "voice-shield": "Voice Shield",
    "device-security": "Device Security",
    "security-alerts": "Security Alerts",
    "bank-review": "Bank Review",
    settings: "Settings",
    help: "Help & Support",
    logout: "Logout",
    home: "Dashboard",
  };

  /**
   * Resolve asset paths for pages in root vs pages/ subdirectory.
   * @param {string} path
   * @returns {string}
   */
  function resolvePath(path) {
    const inPagesDir = window.location.pathname.includes("/pages/");
    return inPagesDir ? "../" + path : path;
  }

  /**
   * Resolve page href — index.html at root maps to dashboard page.
   * @param {string} href
   * @returns {string}
   */
  function resolveHref(href) {
    const atRoot = !window.location.pathname.includes("/pages/");

    if (href === "pages/dashboard.html") {
      return atRoot ? "index.html" : "../index.html";
    }

    return resolvePath(href);
  }

  /**
   * Get the current page identifier from body data attribute or URL.
   * @returns {string}
   */
  function getCurrentPageId() {
    const fromBody = document.body.dataset.page;
    if (fromBody) return fromBody;

    const filename = window.location.pathname.split("/").pop() || "index.html";
    const map = {
      "index.html": "dashboard",
      "dashboard.html": "dashboard",
      "new-transaction.html": "new-transaction",
      "transactions.html": "transactions",
      "risk-analysis.html": "risk-analysis",
      "voice-shield.html": "voice-shield",
      "device-security.html": "device-security",
      "security-alerts.html": "security-alerts",
      "bank-review.html": "bank-review",
      "settings.html": "settings",
      "help.html": "help",
      "login.html": "logout",
    };
    return map[filename] || "";
  }

  /**
   * Get display title for the current page.
   * @returns {string}
   */
  function getPageTitle() {
    const fromBody = document.body.dataset.pageTitle;
    if (fromBody) return fromBody;

    const pageId = getCurrentPageId();
    return PAGE_TITLE_MAP[pageId] || "FraudShield";
  }

  /**
   * Initialize mobile sidebar open/close behavior.
   */
function initSidebar() {
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.querySelector(".sidebar-overlay");
  const menuBtn = document.querySelector(".header__menu-btn");
  const closeBtn = document.querySelector(".sidebar__close-btn");

  if (!sidebar || !menuBtn) return;

  function openSidebar() {
    sidebar.classList.remove("sidebar--closed");
    sidebar.classList.add("sidebar--open");

    overlay?.classList.add("sidebar-overlay--visible");
    document.body.classList.add("sidebar-open");

    menuBtn.setAttribute("aria-expanded", "true");
  }

  function closeSidebar() {
    sidebar.classList.remove("sidebar--open");
    sidebar.classList.add("sidebar--closed");

    overlay?.classList.remove("sidebar-overlay--visible");
    document.body.classList.remove("sidebar-open");

    menuBtn.setAttribute("aria-expanded", "false");
  }

  function toggleSidebar() {
    if (
      sidebar.classList.contains("sidebar--open") ||
      !sidebar.classList.contains("sidebar--closed")
    ) {
      closeSidebar();
    } else {
      openSidebar();
    }
  }

  menuBtn.addEventListener("click", openSidebar);
  closeBtn?.addEventListener("click", closeSidebar);
  overlay?.addEventListener("click", closeSidebar);

  sidebar.addEventListener("click", (e) => {
    const link = e.target.closest(".sidebar__link");

    if (link && window.innerWidth <= 768) {
      closeSidebar();
    }
  });

  window.addEventListener("resize", () => {
    if (window.innerWidth > 768) {
      overlay?.classList.remove("sidebar-overlay--visible");
      document.body.classList.remove("sidebar-open");
    }
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      closeSidebar();
    }
  });
}

  /**
   * Highlight the active sidebar link for the current page.
   */
  function setActiveNavigation() {
    const currentPage = getCurrentPageId();
    if (!currentPage) return;

    document.querySelectorAll(".sidebar__link").forEach((link) => {
      const linkPage = link.dataset.page;
      link.classList.toggle("sidebar__link--active", linkPage === currentPage);
    });
  }

  /**
   * Render a single nav link.
   * @param {object} item
   * @param {string} currentPage
   * @returns {string}
   */
  function renderNavLink(item, currentPage) {
    const isActive = item.id === currentPage;
    const iconPath = resolvePath(ICONS[item.icon] || ICONS.dashboard);
    const href = resolveHref(item.href);
    const logoutClass = item.isLogout ? " sidebar__link--logout" : "";
    const badge = item.badge
      ? `<span class="sidebar__link-badge">${item.badge}</span>`
      : "";

    return `
      <li>
        <a href="${href}"
           class="sidebar__link${isActive ? " sidebar__link--active" : ""}${logoutClass}"
           data-page="${item.id}">
          <img src="${iconPath}" alt="" class="sidebar__link-icon" width="20" height="20">
          <span>${item.label}</span>
          ${badge}
        </a>
      </li>`;
  }

  /**
   * Build sidebar navigation from shell config.
   */
  function renderNavigation() {
    const navContainer = document.querySelector("[data-nav-render]");
    if (!navContainer) return;

    const currentPage = getCurrentPageId();
    let html = "";

    SHELL_NAVIGATION.forEach((section) => {
      html += `<p class="sidebar__section-label">${section.section}</p>`;
      html += `<ul class="sidebar__nav-list" role="list">`;

      section.items.forEach((item) => {
        html += renderNavLink(item, currentPage);
      });

      html += "</ul>";
    });

    html += `<div class="sidebar__divider" role="separator"></div>`;
    html += `<ul class="sidebar__nav-list" role="list">`;
    html += renderNavLink(LOGOUT_ITEM, currentPage);
    html += `</ul>`;

    navContainer.innerHTML = html;
  }

  /**
   * Set the page title in the header and document title.
   */
  function renderPageTitle() {
    const title = getPageTitle();
    const titleEl = document.querySelector("[data-page-title-render]");
    if (titleEl) {
      titleEl.textContent = title;
    }
    document.title = "FraudShield — " + title;
  }

  /**
   * Populate user info in the header from mock data.
   */
  function renderHeaderUser() {
    const userContainer = document.querySelector("[data-header-user-render]");
    if (!userContainer) return;

    const user = window.FraudShieldMockData?.currentUser || {
      name: "Alex Morgan",
      role: "Fraud Analyst",
      initials: "AM",
    };

    userContainer.innerHTML = `
      <div class="header__user-avatar" aria-hidden="true">${user.initials}</div>
      <div class="header__user-info">
        <p class="header__user-name">${user.name}</p>
        <p class="header__user-role">${user.role}</p>
      </div>`;
  }

  /**
   * Initialize dropdown toggle behavior.
   */
  function initDropdowns() {
    document.querySelectorAll("[data-dropdown]").forEach((trigger) => {
      const parent = trigger.closest(".dropdown");
      if (!parent) return;

      trigger.addEventListener("click", (e) => {
        e.stopPropagation();
        const isOpen = parent.classList.contains("dropdown--open");

        document.querySelectorAll(".dropdown--open").forEach((el) => {
          el.classList.remove("dropdown--open");
        });

        if (!isOpen) {
          parent.classList.add("dropdown--open");
        }
      });
    });

    document.addEventListener("click", () => {
      document.querySelectorAll(".dropdown--open").forEach((el) => {
        el.classList.remove("dropdown--open");
      });
    });
  }

  /**
   * Initialize tab switching for elements with data-tabs.
   */
  function initTabs() {
    document.querySelectorAll("[data-tabs]").forEach((tabGroup) => {
      const tabs = tabGroup.querySelectorAll(".tab");
      const panels = tabGroup.querySelectorAll("[data-tab-panel]");

      tabs.forEach((tab) => {
        tab.addEventListener("click", () => {
          const target = tab.dataset.tab;

          tabs.forEach((t) => t.classList.toggle("tab--active", t === tab));
          panels.forEach((panel) => {
            panel.hidden = panel.dataset.tabPanel !== target;
          });
        });
      });
    });
  }

  /**
   * Fix relative paths for icons/images in static HTML when in pages/ dir.
   */
  function fixAssetPaths() {
    if (!window.location.pathname.includes("/pages/")) return;

    document.querySelectorAll("[src^='assets/'], [src^='css/'], [src^='js/']").forEach((el) => {
      el.src = resolvePath(el.getAttribute("src"));
    });

    document.querySelectorAll("[href^='assets/'], [href^='css/']").forEach((el) => {
      el.href = resolvePath(el.getAttribute("href"));
    });
  }

    /**
   * Initialize logout behavior.
   */
  function initLogout() {
    document.addEventListener("click", (event) => {

      const logoutLink = event.target.closest(".sidebar__link--logout");

      if (!logoutLink) return;

      event.preventDefault();

      const confirmed = window.confirm(
        "Are you sure you want to logout?"
      );

      if (!confirmed) return;

      window.location.href = resolveHref(LOGOUT_ITEM.href);
    });
  }


  /**
   * Main entry point — run on DOM ready.
   */
function init() {
    fixAssetPaths();
    renderNavigation();
    renderPageTitle();
    renderHeaderUser();
    setActiveNavigation();
    initSidebar();
    initDropdowns();
    initTabs();
    initLogout();
}

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }

  window.FraudShieldApp = {
    resolvePath,
    resolveHref,
    getCurrentPageId,
    getPageTitle,
    SHELL_NAVIGATION,
    init,
  };
})();
