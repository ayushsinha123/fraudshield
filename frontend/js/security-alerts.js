document.addEventListener("DOMContentLoaded", () => {

    // ==============================
    // ALERT ELEMENTS
    // ==============================

    const filterButtons =
        document.querySelectorAll(".alert-filter");

    const alertCards =
        document.querySelectorAll(".alert-card");

    const alertDetails =
        document.querySelector(".alerts-details");


    // ==============================
    // ALERT DATA
    // ==============================

    const alertData = {

        "Suspicious UPI Transaction": {

            type: "HIGH RISK ALERT",
            time: "Detected 2 minutes ago",
            score: "84 / 100",

            amount: "₹30,000",
            transactionType: "UPI",
            recipient: "Rohit Kumar",
            location: "Bengaluru, India",
            device: "Vivo V29",
            transactionTime: "02:17 AM",

            description:
                "FraudShield detected several unusual characteristics that differ significantly from your normal transaction behavior.",

            reasons: [
                "New and untrusted device",
                "Unusually large transaction amount",
                "New recipient with no previous transactions",
                "Transaction occurred at an unusual time"
            ],

            recommendation:
                "Review this transaction immediately. If you do not recognize it, block the transaction and secure your account."
        },


        "Unusual Login Activity": {

            type: "MEDIUM RISK ALERT",
            time: "Detected 18 minutes ago",
            score: "62 / 100",

            amount: "—",
            transactionType: "Login",
            recipient: "—",
            location: "Unknown Location",
            device: "Unknown Device",
            transactionTime: "03:42 AM",

            description:
                "FraudShield detected login activity that differs from your usual account behavior.",

            reasons: [
                "Login from a new location",
                "Unknown device detected",
                "Activity occurred outside your usual hours"
            ],

            recommendation:
                "Verify that this login was made by you. If you do not recognize it, secure your account immediately."
        },


        "Multiple Failed Login Attempts": {

            type: "RESOLVED ALERT",
            time: "Detected 1 hour ago",
            score: "28 / 100",

            amount: "—",
            transactionType: "Account Security",
            recipient: "—",
            location: "Unknown Location",
            device: "Unknown Device",
            transactionTime: "01:15 AM",

            description:
                "Several unsuccessful login attempts were detected and automatically blocked by FraudShield.",

            reasons: [
                "Multiple failed login attempts",
                "Suspicious login pattern detected",
                "Access attempt was automatically blocked"
            ],

            recommendation:
                "No immediate action is required. Continue monitoring your account for unusual activity."
        }

    };


    // ==============================
    // UPDATE DETAILS PANEL
    // ==============================

    function updateAlertDetails(title) {

        const data = alertData[title];

        if (!data || !alertDetails) {
            return;
        }


        // Header

        alertDetails.querySelector(
            ".alert-details__label"
        ).textContent = data.type;

        alertDetails.querySelector(
            ".alert-details__title"
        ).textContent = title;

        alertDetails.querySelector(
            ".alert-details__time"
        ).textContent = data.time;

        alertDetails.querySelector(
            ".alert-details__risk"
        ).textContent = data.score;


        // Details grid

        const detailValues =
            alertDetails.querySelectorAll(
                ".alert-details__grid strong"
            );

        detailValues[0].textContent = data.amount;
        detailValues[1].textContent = data.transactionType;
        detailValues[2].textContent = data.recipient;
        detailValues[3].textContent = data.location;
        detailValues[4].textContent = data.device;
        detailValues[5].textContent = data.transactionTime;


        // Description

        const sections =
            alertDetails.querySelectorAll(
                ".alert-details__section"
            );

        const whySection = sections[1];

        whySection.querySelector("p").textContent =
            data.description;


        // Reasons

        const reasonsList =
            whySection.querySelector(
                ".alert-details__reasons"
            );

        reasonsList.innerHTML = "";

        data.reasons.forEach(reason => {

            const li =
                document.createElement("li");

            li.textContent = reason;

            reasonsList.appendChild(li);

        });


        // Recommendation

        const recommendationSection =
            alertDetails.querySelector(
                ".alert-details__recommendation"
            );

        recommendationSection.querySelector("p").textContent =
            data.recommendation;
    }


    // ==============================
    // ALERT FILTERS
    // ==============================

    filterButtons.forEach(button => {

        button.addEventListener("click", () => {

            filterButtons.forEach(btn => {
                btn.classList.remove("alert-filter--active");
            });

            button.classList.add("alert-filter--active");


            const filter =
                button.textContent.trim().toLowerCase();


            alertCards.forEach(card => {

                const cardType =
                    card.classList.contains("alert-card--high")
                        ? "high risk"
                        : card.classList.contains("alert-card--medium")
                            ? "medium risk"
                            : "resolved";


                if (filter === "all" || cardType === filter) {
                    card.style.display = "";
                } else {
                    card.style.display = "none";
                }

            });

        });

    });


    // ==============================
    // ALERT CARD SELECTION
    // ==============================

    alertCards.forEach(card => {

        card.addEventListener("click", () => {

            alertCards.forEach(item => {
                item.classList.remove("alert-card--selected");
            });

            card.classList.add("alert-card--selected");


            const title =
                card.querySelector(
                    ".alert-card__title"
                ).textContent.trim();


            updateAlertDetails(title);

        });

    });


    // ==============================
    // SELECT FIRST ALERT BY DEFAULT
    // ==============================

    if (alertCards.length > 0) {

        alertCards[0].classList.add(
            "alert-card--selected"
        );

    }


    // ==============================
// ALERT SEARCH
// ==============================

const alertSearch =
    document.querySelector(".alerts-search input");

if (alertSearch) {

    alertSearch.addEventListener("input", () => {

        const searchTerm =
            alertSearch.value.trim().toLowerCase();

        alertCards.forEach(card => {

            const cardText =
                card.textContent.toLowerCase();

            if (cardText.includes(searchTerm)) {

                card.style.display = "";

            } else {

                card.style.display = "none";

            }

        });

    });

}

// ==============================
// MARK ALERT AS RESOLVED
// ==============================

const resolveButton =
    document.querySelector(".alerts-btn--secondary");

if (resolveButton) {

    resolveButton.addEventListener("click", () => {

        const selectedCard =
            document.querySelector(".alert-card--selected");

        if (!selectedCard) {
            return;
        }

        // Change card to resolved
        selectedCard.classList.remove(
            "alert-card--high",
            "alert-card--medium"
        );

        selectedCard.classList.add(
            "alert-card--resolved"
        );

        // Change alert label
        const type =
            selectedCard.querySelector(
                ".alert-card__type"
            );

        if (type) {
            type.textContent = "RESOLVED";
        }

        // Update details panel
        const label =
            alertDetails.querySelector(
                ".alert-details__label"
            );

        if (label) {
            label.textContent = "RESOLVED ALERT";
        }

        // Update recommendation
        const recommendation =
            alertDetails.querySelector(
                ".alert-details__recommendation p"
            );

        if (recommendation) {
            recommendation.textContent =
                "This alert has been resolved. No immediate action is required.";
        }

        // Update button
        resolveButton.textContent =
            "✓ Resolved";

        resolveButton.disabled = true;

        console.log("Alert marked as resolved");

    });

}
});