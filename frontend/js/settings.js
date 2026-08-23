/* =========================================================
   FRAUDSHIELD SETTINGS
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

  /* =======================================================
     ELEMENTS
     ======================================================= */

  const saveProfileBtn = document.getElementById("saveProfile");
  const cancelProfileBtn = document.getElementById("cancelProfile");

  const fullNameInput = document.getElementById("fullName");
  const emailInput = document.getElementById("email");
  const phoneInput = document.getElementById("phone");

  const twoFactorToggle = document.getElementById("twoFactorToggle");
  const loginAlertsToggle = document.getElementById("loginAlertsToggle");

  const fraudAlertsToggle = document.getElementById("fraudAlertsToggle");
  const transactionAlertsToggle =
    document.getElementById("transactionAlertsToggle");
  const securityReportsToggle =
    document.getElementById("securityReportsToggle");

  const themeSelect = document.getElementById("themeSelect");

  const changePasswordBtn =
    document.getElementById("changePasswordBtn");

  const deleteAccountBtn =
    document.getElementById("deleteAccountBtn");

  const logoutBtn =
    document.getElementById("logoutBtn");

  const settingsToast =
    document.getElementById("settingsToast");

  const settingsToastMessage =
    document.getElementById("settingsToastMessage");


  /* =======================================================
     DEFAULT PROFILE DATA
     ======================================================= */

  const defaultProfile = {
    name: "Alex Morgan",
    email: "alex.morgan@fraudshield.com",
    phone: "+91 98765 43210"
  };


  /* =======================================================
     TOAST
     ======================================================= */

  let toastTimer;

  function showToast(message) {

    if (!settingsToast || !settingsToastMessage) {
      return;
    }

    settingsToastMessage.textContent = message;

    settingsToast.classList.add("settings-toast--visible");

    clearTimeout(toastTimer);

    toastTimer = setTimeout(() => {
      settingsToast.classList.remove("settings-toast--visible");
    }, 2500);
  }


  /* =======================================================
     PROFILE SAVE
     ======================================================= */

  if (saveProfileBtn) {

    saveProfileBtn.addEventListener("click", () => {

      const name = fullNameInput.value.trim();
      const email = emailInput.value.trim();
      const phone = phoneInput.value.trim();


      if (!name) {
        showToast("Please enter your full name.");
        fullNameInput.focus();
        return;
      }


      if (!email) {
        showToast("Please enter your email address.");
        emailInput.focus();
        return;
      }


      const emailPattern =
        /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


      if (!emailPattern.test(email)) {
        showToast("Please enter a valid email address.");
        emailInput.focus();
        return;
      }


      const profile = {
        name,
        email,
        phone
      };


      localStorage.setItem(
        "fraudshieldProfile",
        JSON.stringify(profile)
      );


      updateUserName(name);

      showToast("Profile changes saved successfully.");
    });
  }


  /* =======================================================
     CANCEL PROFILE
     ======================================================= */

  if (cancelProfileBtn) {

    cancelProfileBtn.addEventListener("click", () => {

      fullNameInput.value = defaultProfile.name;
      emailInput.value = defaultProfile.email;
      phoneInput.value = defaultProfile.phone;

      showToast("Changes discarded.");
    });
  }


  /* =======================================================
     UPDATE HEADER USER NAME
     ======================================================= */

  function updateUserName(name) {

    const headerName =
      document.querySelector(".header__user-name");

    if (headerName) {
      headerName.textContent = name;
    }
  }


  /* =======================================================
     LOAD PROFILE
     ======================================================= */

  function loadProfile() {

    const savedProfile =
      localStorage.getItem("fraudshieldProfile");

    if (!savedProfile) {
      return;
    }

    try {

      const profile = JSON.parse(savedProfile);

      if (profile.name) {
        fullNameInput.value = profile.name;
        updateUserName(profile.name);
      }

      if (profile.email) {
        emailInput.value = profile.email;
      }

      if (profile.phone) {
        phoneInput.value = profile.phone;
      }

    } catch (error) {

      console.error(
        "Unable to load FraudShield profile:",
        error
      );

    }
  }


  /* =======================================================
     SETTINGS STORAGE
     ======================================================= */

  const settingInputs = [
    twoFactorToggle,
    loginAlertsToggle,
    fraudAlertsToggle,
    transactionAlertsToggle,
    securityReportsToggle
  ];


  function saveSecuritySettings() {

    const settings = {
      twoFactor: twoFactorToggle?.checked ?? false,
      loginAlerts: loginAlertsToggle?.checked ?? false,
      fraudAlerts: fraudAlertsToggle?.checked ?? false,
      transactionAlerts:
        transactionAlertsToggle?.checked ?? false,
      securityReports:
        securityReportsToggle?.checked ?? false
    };


    localStorage.setItem(
      "fraudshieldSettings",
      JSON.stringify(settings)
    );
  }


  function loadSecuritySettings() {

    const savedSettings =
      localStorage.getItem("fraudshieldSettings");

    if (!savedSettings) {
      return;
    }


    try {

      const settings = JSON.parse(savedSettings);


      if (twoFactorToggle && typeof settings.twoFactor === "boolean") {
        twoFactorToggle.checked = settings.twoFactor;
      }


      if (loginAlertsToggle && typeof settings.loginAlerts === "boolean") {
        loginAlertsToggle.checked = settings.loginAlerts;
      }


      if (
        fraudAlertsToggle &&
        typeof settings.fraudAlerts === "boolean"
      ) {
        fraudAlertsToggle.checked = settings.fraudAlerts;
      }


      if (
        transactionAlertsToggle &&
        typeof settings.transactionAlerts === "boolean"
      ) {
        transactionAlertsToggle.checked =
          settings.transactionAlerts;
      }


      if (
        securityReportsToggle &&
        typeof settings.securityReports === "boolean"
      ) {
        securityReportsToggle.checked =
          settings.securityReports;
      }

    } catch (error) {

      console.error(
        "Unable to load FraudShield settings:",
        error
      );

    }
  }


  /* =======================================================
     TOGGLE EVENTS
     ======================================================= */

  settingInputs.forEach((input) => {

    if (!input) {
      return;
    }


    input.addEventListener("change", () => {

      saveSecuritySettings();

      showToast("Security preferences updated.");

    });

  });


  /* =======================================================
     PASSWORD
     ======================================================= */

  if (changePasswordBtn) {

    changePasswordBtn.addEventListener("click", () => {

      openPasswordModal();

    });

  }


  function openPasswordModal() {

    if (document.querySelector(".settings-modal")) {
      return;
    }


    const modal = document.createElement("div");

    modal.className = "settings-modal";

    modal.innerHTML = `
      <div class="settings-modal__box">

        <div class="settings-modal__header">

          <div>
            <div class="settings-modal__title">
              Change Password
            </div>

            <div class="settings-modal__subtitle">
              Create a strong new password for your account.
            </div>
          </div>

          <button
            class="settings-modal__close"
            type="button"
            aria-label="Close"
          >
            ×
          </button>

        </div>


        <div class="form-group">

          <label class="form-label" for="currentPassword">
            Current Password
          </label>

          <input
            class="form-input"
            type="password"
            id="currentPassword"
            placeholder="Enter current password"
          >

        </div>


        <div class="form-group">

          <label class="form-label" for="newPassword">
            New Password
          </label>

          <input
            class="form-input"
            type="password"
            id="newPassword"
            placeholder="Enter new password"
          >

        </div>


        <div class="form-group">

          <label class="form-label" for="confirmPassword">
            Confirm New Password
          </label>

          <input
            class="form-input"
            type="password"
            id="confirmPassword"
            placeholder="Confirm new password"
          >

        </div>


        <div class="settings-modal__actions">

          <button
            class="btn btn--secondary"
            type="button"
            data-password-cancel
          >
            Cancel
          </button>

          <button
            class="btn btn--primary"
            type="button"
            data-password-save
          >
            Update Password
          </button>

        </div>

      </div>
    `;


    document.body.appendChild(modal);


    requestAnimationFrame(() => {
      modal.classList.add("settings-modal--visible");
    });


    const closeModal = () => {

      modal.classList.remove(
        "settings-modal--visible"
      );

      setTimeout(() => {
        modal.remove();
      }, 180);

    };


    modal
      .querySelector(".settings-modal__close")
      .addEventListener("click", closeModal);


    modal
      .querySelector("[data-password-cancel]")
      .addEventListener("click", closeModal);


    modal.addEventListener("click", (event) => {

      if (event.target === modal) {
        closeModal();
      }

    });


    modal
      .querySelector("[data-password-save]")
      .addEventListener("click", () => {

        const currentPassword =
          document.getElementById("currentPassword").value;

        const newPassword =
          document.getElementById("newPassword").value;

        const confirmPassword =
          document.getElementById("confirmPassword").value;


        if (!currentPassword) {
          showToast("Enter your current password.");
          return;
        }


        if (newPassword.length < 8) {
          showToast(
            "New password must contain at least 8 characters."
          );
          return;
        }


        if (newPassword !== confirmPassword) {
          showToast("New passwords do not match.");
          return;
        }


        closeModal();

        showToast("Password updated successfully.");

      });

  }


  /* =======================================================
     THEME
     ======================================================= */

  if (themeSelect) {

    themeSelect.addEventListener("change", () => {

      const selectedTheme =
        themeSelect.value;

      localStorage.setItem(
        "fraudshieldTheme",
        selectedTheme
      );


      if (selectedTheme === "system") {

        document.documentElement.removeAttribute(
          "data-theme"
        );

        showToast("System theme selected.");

      } else {

        document.documentElement.setAttribute(
          "data-theme",
          "dark"
        );

        showToast("Dark theme selected.");

      }

    });

  }


  /* =======================================================
     DELETE ACCOUNT
     ======================================================= */

  if (deleteAccountBtn) {

    deleteAccountBtn.addEventListener("click", () => {

      const confirmed = window.confirm(
        "Are you sure you want to delete Alex Morgan's FraudShield account? This action cannot be undone."
      );


      if (!confirmed) {
        return;
      }


      localStorage.removeItem(
        "fraudshieldProfile"
      );

      localStorage.removeItem(
        "fraudshieldSettings"
      );

      localStorage.removeItem(
        "fraudshieldTheme"
      );


      showToast(
        "Account deletion request submitted."
      );

    });

  }


  /* =======================================================
     LOGOUT
     ======================================================= */

  if (logoutBtn) {

    logoutBtn.addEventListener("click", (event) => {

      event.preventDefault();

      const confirmed = window.confirm(
        "Are you sure you want to logout?"
      );


      if (!confirmed) {
        return;
      }


      window.location.href = "../index.html";

    });

  }


  /* =======================================================
     NOTIFICATION BUTTON
     ======================================================= */

  const notificationBtn =
    document.getElementById("notificationBtn");


  if (notificationBtn) {

    notificationBtn.addEventListener("click", () => {

      showToast("You have 12 security alerts.");

    });

  }


  /* =======================================================
     PROFILE BUTTON
     ======================================================= */

  const profileBtn =
    document.getElementById("profileBtn");


  if (profileBtn) {

    profileBtn.addEventListener("click", () => {

      document
        .getElementById("fullName")
        ?.focus();

    });

  }


  /* =======================================================
     INITIALIZE
     ======================================================= */

  loadProfile();
  loadSecuritySettings();

});