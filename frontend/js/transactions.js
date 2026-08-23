/* =========================================================
   FRAUDSHIELD - TRANSACTIONS
   ========================================================= */

document.addEventListener("DOMContentLoaded", () => {

    const searchInput =
        document.getElementById("transaction-search");

    const filterButtons =
        document.querySelectorAll(".filter-btn");

    const rows =
        document.querySelectorAll(".transaction-row");

    const totalCount =
        document.getElementById("total-count");

    const previousButton =
        document.getElementById("prev-btn");

    const nextButton =
        document.getElementById("next-btn");

    const analysisButton =
        document.getElementById("full-analysis-btn");


    /* =====================================================
       RISK FILTER
       ===================================================== */

    filterButtons.forEach(button => {

        button.addEventListener("click", () => {

            filterButtons.forEach(btn => {
                btn.classList.remove("active");
            });

            button.classList.add("active");

            const selectedRisk =
                button.dataset.risk;

            rows.forEach(row => {

                const rowRisk =
                    row.dataset.risk;

                if (
                    selectedRisk === "all" ||
                    rowRisk === selectedRisk
                ) {

                    row.style.display = "grid";

                } else {

                    row.style.display = "none";

                }

            });

        });

    });


    /* =====================================================
       SEARCH
       ===================================================== */

    if (searchInput) {

        searchInput.addEventListener("input", () => {

            const searchValue =
                searchInput.value
                    .toLowerCase()
                    .trim();


            rows.forEach(row => {

                const text =
                    row.textContent
                        .toLowerCase();

                if (text.includes(searchValue)) {

                    row.style.display = "grid";

                } else {

                    row.style.display = "none";

                }

            });

        });

    }


    /* =====================================================
       PAGINATION
       ===================================================== */

    if (previousButton) {

        previousButton.addEventListener(
            "click",
            () => {

                alert(
                    "You are already viewing the first page."
                );

            }
        );

    }


    if (nextButton) {

        nextButton.addEventListener(
            "click",
            () => {

                alert(
                    "Next transaction page loaded."
                );

            }
        );

    }


    /* =====================================================
       FULL RISK ANALYSIS
       ===================================================== */

    if (analysisButton) {

        analysisButton.addEventListener(
            "click",
            () => {

                alert(
                    "Full Risk Analysis\n\n" +
                    "Risk Score: 84/100\n" +
                    "New Device: +24\n" +
                    "Unusual Amount: +21\n" +
                    "Time Anomaly: +18\n" +
                    "Biometric Match: +12"
                );

            }
        );

    }


    /* =====================================================
       SUMMARY
       ===================================================== */

    if (totalCount) {

        totalCount.textContent = "128";

    }

});