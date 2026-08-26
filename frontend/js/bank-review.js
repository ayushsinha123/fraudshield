document.addEventListener("DOMContentLoaded", () => {

    const tableBody =
        document.querySelector(".bank-review-table tbody");

    if (!tableBody) return;


    /* =========================================================
       LOAD NEW TRANSACTIONS FROM NEW TRANSACTION PAGE
       ========================================================= */

    const newTransactions =
        JSON.parse(
            localStorage.getItem(
                "fraudshield_new_transactions"
            )
        ) || [];


    newTransactions.forEach(transaction => {

        // Don't add approved transactions
        if (transaction.status === "approved") {
            return;
        }


        // Prevent duplicate rows
        const existingRow =
            tableBody.querySelector(
                `[data-transaction-id="${transaction.id}"]`
            );

        if (existingRow) {
            return;
        }


        /* Risk class */

        let riskClass = "medium";

        if (transaction.riskLevel === "high") {
            riskClass = "high";
        }

        if (transaction.riskLevel === "critical") {
            riskClass = "critical";
        }


        /* Risk label */

        const riskLabel =
            transaction.riskLevel
                ? transaction.riskLevel.charAt(0).toUpperCase() +
                  transaction.riskLevel.slice(1)
                : "Medium";


        /* Reason */

        const reason =
            transaction.description ||
            "Transaction flagged by FraudShield risk engine.";


        /* Create row */

        const row =
            document.createElement("tr");


        row.dataset.transactionId =
            transaction.id;

        row.dataset.merchant =
            transaction.merchant;

        row.dataset.customer =
            transaction.customer;

        row.dataset.amount =
            `${transaction.currency} ${Number(
                transaction.amount
            ).toFixed(2)}`;

        row.dataset.risk =
            riskLabel;

        row.dataset.location =
            transaction.location;

        row.dataset.reason =
            reason;


        row.innerHTML = `

            <td>
                <strong>
                    ${transaction.id}
                </strong>

                <small>
                    ${transaction.merchant}
                </small>
            </td>


            <td>
                ${transaction.customer}
            </td>


            <td>
                ${transaction.currency}
                ${Number(
                    transaction.amount
                ).toFixed(2)}
            </td>


            <td>
                <span
                    class="risk-badge risk-badge--${riskClass}"
                >
                    ${riskLabel}
                </span>
            </td>


            <td>
                <span
                    class="review-status review-status--pending"
                >
                    Pending
                </span>
            </td>


            <td>
                <button
                    class="review-action"
                    type="button"
                >
                    Review
                </button>
            </td>

        `;


        // Newest transaction goes to the top
        tableBody.prepend(row);

    });


    /* =========================================================
       REVIEW BUTTON
       ========================================================= */

    tableBody.addEventListener("click", (event) => {

        const button =
            event.target.closest(".review-action");

        if (!button) return;


        const row =
            button.closest("tr");

        if (!row) return;


        const transactionId =
            row.dataset.transactionId || "TXN-001";

        const merchant =
            row.dataset.merchant || "Unknown Merchant";

        const customer =
            row.dataset.customer || "Unknown Customer";

        const amount =
            row.dataset.amount || "₹0";

        const risk =
            row.dataset.risk || "Medium";

        const location =
            row.dataset.location || "Unknown";

        const reason =
            row.dataset.reason ||
            "Suspicious transaction activity";


        /* Remove old panel */

        const oldPanel =
            document.querySelector(
                ".review-details-panel"
            );

        if (oldPanel) {
            oldPanel.remove();
        }


        /* =====================================================
           CREATE REVIEW PANEL
           ===================================================== */

        const panel =
            document.createElement("div");

        panel.className =
            "review-details-panel";


        panel.innerHTML = `

            <div class="review-details-header">

                <h2>
                    Review Details
                </h2>

                <button
                    class="close-review"
                    type="button"
                >
                    &times;
                </button>

            </div>


            <div class="review-details-content">

                <div class="detail-item">

                    <span>
                        Transaction ID
                    </span>

                    <strong>
                        ${transactionId}
                    </strong>

                </div>


                <div class="detail-item">

                    <span>
                        Merchant
                    </span>

                    <strong>
                        ${merchant}
                    </strong>

                </div>


                <div class="detail-item">

                    <span>
                        Customer
                    </span>

                    <strong>
                        ${customer}
                    </strong>

                </div>


                <div class="detail-item">

                    <span>
                        Amount
                    </span>

                    <strong>
                        ${amount}
                    </strong>

                </div>


                <div class="detail-item">

                    <span>
                        Risk Level
                    </span>

                    <strong>
                        ${risk}
                    </strong>

                </div>


                <div class="detail-item">

                    <span>
                        Location
                    </span>

                    <strong>
                        ${location}
                    </strong>

                </div>


                <div class="detail-item reason">

                    <span>
                        Reason for Flag
                    </span>

                    <strong>
                        ${reason}
                    </strong>

                </div>

            </div>


            <div class="review-actions">

                <button
                    class="approve-btn"
                    type="button"
                >
                    Approve
                </button>


                <button
                    class="block-btn"
                    type="button"
                >
                    Block
                </button>


                <button
                    class="pending-btn"
                    type="button"
                >
                    Keep Pending
                </button>

            </div>

        `;


        document.body.appendChild(panel);


        /* =====================================================
           CLOSE
           ===================================================== */

        panel
            .querySelector(".close-review")
            .addEventListener("click", () => {

                panel.remove();

            });


        /* =====================================================
           APPROVE
           ===================================================== */

        panel
            .querySelector(".approve-btn")
            .addEventListener("click", () => {

                alert("Transaction approved.");

                panel.remove();

            });


        /* =====================================================
           BLOCK
           ===================================================== */

        panel
            .querySelector(".block-btn")
            .addEventListener("click", () => {

                alert("Transaction blocked.");

                panel.remove();

            });


        /* =====================================================
           KEEP PENDING
           ===================================================== */

        panel
            .querySelector(".pending-btn")
            .addEventListener("click", () => {

                alert("Transaction kept pending.");

                panel.remove();

            });

    });

});