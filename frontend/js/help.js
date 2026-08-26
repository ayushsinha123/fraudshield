/**
 * FraudShield — Help & Support
 */

document.addEventListener("DOMContentLoaded", () => {

    // ==============================
    // FAQ ACCORDION
    // ==============================

    const faqQuestions = document.querySelectorAll(".faq-item__question");

    faqQuestions.forEach((question) => {

        question.addEventListener("click", () => {

            const faqItem = question.closest(".faq-item");
            const answer = faqItem.querySelector(".faq-item__answer");
            const icon = question.querySelector("span:last-child");

            const isOpen = answer.style.display === "block";

            // Close all other FAQs
            document.querySelectorAll(".faq-item__answer").forEach((item) => {
                item.style.display = "none";
            });

            document.querySelectorAll(".faq-item__question span:last-child").forEach((item) => {
                item.textContent = "+";
            });

            // Open clicked FAQ
            if (!isOpen) {
                answer.style.display = "block";
                icon.textContent = "−";
            }

        });

    });


    // ==============================
    // HELP SEARCH
    // ==============================

    const searchInput = document.getElementById("help-search-input");
    const faqItems = document.querySelectorAll(".faq-item");

    if (searchInput) {

        searchInput.addEventListener("input", () => {

            const searchTerm = searchInput.value.trim().toLowerCase();
            let visibleResults = 0;

            faqItems.forEach((faqItem) => {

                const question = faqItem
                    .querySelector(".faq-item__question")
                    .textContent
                    .toLowerCase();

                const answer = faqItem
                    .querySelector(".faq-item__answer")
                    .textContent
                    .toLowerCase();

                const matches =
                    question.includes(searchTerm) ||
                    answer.includes(searchTerm);

                if (matches) {
                    faqItem.style.display = "";
                    visibleResults++;
                } else {
                    faqItem.style.display = "none";
                }

            });

            // Show / hide "no results" message
            let noResults = document.querySelector(".help-search__no-results");

            if (!noResults) {
                noResults = document.createElement("p");
                noResults.className = "help-search__no-results";
                noResults.textContent = "No help articles found.";
                noResults.style.display = "none";

                const faqList = document.querySelector(".faq-list");

                if (faqList) {
                    faqList.appendChild(noResults);
                }
            }

            if (searchTerm && visibleResults === 0) {
                noResults.style.display = "block";
            } else {
                noResults.style.display = "none";
            }

        });

    }
    // ==============================
    // CONTACT SUPPORT MODAL
    // ==============================

    const contactSupportButton = document.getElementById("contact-support-btn");
    const supportModal = document.getElementById("support-modal");
    const supportModalClose = document.getElementById("support-modal-close");
    const supportModalOverlay = document.querySelector("[data-modal-close]");

    if (contactSupportButton && supportModal) {

        contactSupportButton.addEventListener("click", () => {
            supportModal.classList.add("is-open");
            supportModal.setAttribute("aria-hidden", "false");
        });

    }

    function closeSupportModal() {

        if (supportModal) {
            supportModal.classList.remove("is-open");
            supportModal.setAttribute("aria-hidden", "true");
        }

    }

    if (supportModalClose) {
        supportModalClose.addEventListener("click", closeSupportModal);
    }

    if (supportModalOverlay) {
        supportModalOverlay.addEventListener("click", closeSupportModal);
    }

        // ==============================
    // SUPPORT FORM
    // ==============================

    const supportForm = document.getElementById("support-form");

    if (supportForm) {

        supportForm.addEventListener("submit", (event) => {

            event.preventDefault();

            alert("Your support request has been submitted successfully.");

            supportForm.reset();

            closeSupportModal();

        });

    }

        // ==============================
    // QUICK HELP OPTIONS
    // ==============================

    const gettingStartedButton =
        document.getElementById("getting-started-btn");

    const securityFraudButton =
        document.getElementById("security-fraud-btn");

    const accountSettingsButton =
        document.getElementById("account-settings-btn");

    const voiceShieldButton =
        document.getElementById("voice-shield-btn");


    if (gettingStartedButton) {

        gettingStartedButton.addEventListener("click", () => {

            document.querySelector(".help-search").scrollIntoView({
                behavior: "smooth"
            });

        });

    }


    if (securityFraudButton) {

        securityFraudButton.addEventListener("click", () => {

            searchInput.value = "fraud";

            searchInput.dispatchEvent(new Event("input"));

            document.querySelector(".faq-list").scrollIntoView({
                behavior: "smooth"
            });

        });

    }


    if (accountSettingsButton) {

        accountSettingsButton.addEventListener("click", () => {

            searchInput.value = "account";

            searchInput.dispatchEvent(new Event("input"));

            document.querySelector(".faq-list").scrollIntoView({
                behavior: "smooth"
            });

        });

    }


    if (voiceShieldButton) {

        voiceShieldButton.addEventListener("click", () => {

            searchInput.value = "voice";

            searchInput.dispatchEvent(new Event("input"));

            document.querySelector(".faq-list").scrollIntoView({
                behavior: "smooth"
            });

        });

    }
});