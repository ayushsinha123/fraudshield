
/* =========================================================
   FRAUDSHIELD — NEW TRANSACTION
   Real FastAPI integration
   ========================================================= */

const FRAUDSHIELD_API_BASE = "http://127.0.0.1:8000";


document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("new-transaction-form");

  if (!form) return;

  form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const formData = new FormData(form);

    const transaction = {
      id: generateTransactionId(),
      merchant: String(formData.get("merchant") || "").trim(),
      customer: String(formData.get("customer") || "").trim(),
      amount: Number(formData.get("amount")),
      currency: String(formData.get("currency") || "INR"),
      location: String(formData.get("location") || "").trim(),
      category: String(formData.get("category") || "other"),
      description: String(formData.get("description") || "").trim(),
      date: new Date().toISOString(),
      status: "pending",
      riskLevel: "low"
    };

    await analyzeTransaction(transaction);
  });
});


/* =========================================================
   GENERATE TRANSACTION ID
   ========================================================= */

function generateTransactionId() {
  const randomPart = Math.random()
    .toString(36)
    .substring(2, 8)
    .toUpperCase();

  return `txn_${randomPart}`;
}


/* =========================================================
   BUILD BACKEND REQUEST
   ========================================================= */

function buildRiskPayload(transaction) {
  /*
   * The current UI represents a normal merchant payment.
   *
   * Backend contract requires:
   *   step
   *   type
   *   amount
   *   nameDest
   *   behaviour
   *   device
   *   voice
   *
   * We use PAYMENT for this page because the existing form
   * does not currently expose a UPI transaction-type selector.
   */

  return {
    step: new Date().getHours(),

    type: "PAYMENT",

    amount: transaction.amount,

    /*
     * In this UI the merchant is the payment destination.
     */
    nameDest: transaction.merchant,

    behaviour: {
      new_recipient: 0,
      new_device: 0,
      unusual_hour: 0,
      burst: 0,
      location_jump: 0,
      network_change: 0
    },

    device: {
      new_device: false,
      network_change: false,
      location_jump: false,
      sim_change: false
    },

    voice: null
  };
}


/* =========================================================
   FRAUDSHIELD RISK ANALYSIS
   ========================================================= */

async function analyzeTransaction(transaction) {
  const result = getOrCreateResultContainer();

  setLoadingState(result);

  try {
    const payload = buildRiskPayload(transaction);

    const response = await fetch(
      `${FRAUDSHIELD_API_BASE}/api/v1/risk-score`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      }
    );

    if (!response.ok) {
      let errorMessage = `API request failed (${response.status})`;

      try {
        const errorBody = await response.json();

        if (typeof errorBody.detail === "string") {
          errorMessage = errorBody.detail;
        }
      } catch (_) {
        // Keep the default error message.
      }

      throw new Error(errorMessage);
    }

    const riskResponse = await response.json();

    /*
     * Keep the locally-generated transaction ID because the current
     * backend response may not yet assign a database transaction ID.
     */
    transaction.backendResponse = riskResponse;

    transaction.riskScore = Number(riskResponse.risk_score || 0);

    transaction.riskLevel = String(
      riskResponse.risk_level || "LOW"
    ).toLowerCase();

    transaction.status = getTransactionStatus(
      riskResponse
    );

    transaction.date = new Date().toISOString();

    saveTransaction(transaction);

    showResult(
      transaction,
      riskResponse
    );

  } catch (error) {
    console.error(
      "FraudShield risk analysis failed:",
      error
    );

    showError(
      result,
      error instanceof Error
        ? error.message
        : "Unable to connect to FraudShield API."
    );
  }
}


/* =========================================================
   STATUS MAPPING
   ========================================================= */

function getTransactionStatus(riskResponse) {
  const riskLevel = String(
    riskResponse.risk_level || "LOW"
  ).toUpperCase();

  if (
    riskLevel === "CRITICAL" ||
    riskLevel === "HIGH"
  ) {
    return "flagged";
  }

  if (riskLevel === "MEDIUM") {
    return "review";
  }

  return "approved";
}


/* =========================================================
   SAVE TRANSACTION
   =========================================================
   
   LocalStorage is retained temporarily so the existing frontend
   history pages continue to have something to display.

   This is NOT the final persistence layer.
   The eventual source of truth will be the backend database.
   ========================================================= */

function saveTransaction(transaction) {
  const existingTransactions =
    JSON.parse(
      localStorage.getItem(
        "fraudshield_new_transactions"
      )
    ) || [];

  existingTransactions.push(transaction);

  localStorage.setItem(
    "fraudshield_new_transactions",
    JSON.stringify(existingTransactions)
  );

  console.log(
    "FraudShield transaction saved:",
    transaction
  );
}


/* =========================================================
   RESULT CONTAINER
   ========================================================= */

function getOrCreateResultContainer() {
  let result =
    document.getElementById(
      "transaction-risk-result"
    );

  if (result) {
    return result;
  }

  result = document.createElement("section");

  result.id = "transaction-risk-result";

  result.className =
    "transaction-risk-result";

  const form =
    document.getElementById(
      "new-transaction-form"
    );

  if (form && form.parentElement) {
    form.parentElement.insertAdjacentElement(
      "afterend",
      result
    );
  }

  return result;
}


/* =========================================================
   LOADING STATE
   ========================================================= */

function setLoadingState(result) {
  result.innerHTML = `
    <div class="risk-result-card">
      <div class="risk-result-card__header">
        <div>
          <span class="risk-result-card__label">
            FRAUDSHIELD ANALYSIS
          </span>

          <h3>
            Analyzing Transaction
          </h3>
        </div>
      </div>

      <div class="risk-result-details">
        <div>
          <span>Status</span>
          <strong>Running risk analysis...</strong>
        </div>
      </div>
    </div>
  `;
}


/* =========================================================
   ERROR STATE
   ========================================================= */

function showError(result, message) {
  result.innerHTML = `
    <div class="risk-result-card">
      <div class="risk-result-card__header">
        <div>
          <span class="risk-result-card__label">
            FRAUDSHIELD
          </span>

          <h3>
            Risk Analysis Failed
          </h3>
        </div>

        <span class="risk-result-badge risk-result-badge--high">
          ERROR
        </span>
      </div>

      <div class="risk-reasons">
        <h4>Unable to analyze transaction</h4>

        <ul>
          <li>${escapeHtml(message)}</li>
        </ul>
      </div>

      <div class="risk-result-details">
        <div>
          <span>API</span>
          <strong>${FRAUDSHIELD_API_BASE}</strong>
        </div>
      </div>
    </div>
  `;

  result.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}


/* =========================================================
   DISPLAY RESULT
   ========================================================= */

function showResult(
  transaction,
  riskResponse
) {
  const result =
    getOrCreateResultContainer();

  const score = Number(
    riskResponse.risk_score || 0
  );

  const riskLevel = String(
    riskResponse.risk_level || "LOW"
  ).toLowerCase();

  const headline =
    riskResponse.headline ||
    `${riskLevel.toUpperCase()} RISK`;

  const summary =
    riskResponse.summary ||
    "";

  const message =
    riskResponse.message ||
    "";

  const reasons =
    Array.isArray(riskResponse.reasons)
      ? riskResponse.reasons
      : [];

  const componentRisks =
    riskResponse.component_risks || {};

  const requiresConfirmation =
    Boolean(
      riskResponse.requires_confirmation
    );

  const highFriction =
    Boolean(
      riskResponse.high_friction
    );

  const normalizedRiskLevel =
    riskLevel.toLowerCase();

  let badgeClass = "safe";

  if (normalizedRiskLevel === "medium") {
    badgeClass = "medium";
  }

  if (
    normalizedRiskLevel === "high" ||
    normalizedRiskLevel === "critical"
  ) {
    badgeClass = "high";
  }

  const safeReasons =
    reasons.length > 0
      ? reasons
      : ["No significant risk indicators detected"];

  const componentHtml = Object.entries(
    componentRisks
  )
    .map(
      ([name, value]) => `
        <div>
          <span>${formatComponentName(name)}</span>
          <strong>${Number(value).toFixed(2)}</strong>
        </div>
      `
    )
    .join("");

  const confirmationHtml =
    requiresConfirmation
      ? `
        <div class="risk-reasons">
          <h4>
            Confirmation Required
          </h4>

          <p>
            ${escapeHtml(
              highFriction
                ? "This transaction requires explicit confirmation because multiple strong risk signals were detected."
                : "Please review the risk indicators before continuing."
            )}
          </p>

          <div
            class="new-transaction-form__actions"
            style="margin-top: 1rem;"
          >
            <button
              type="button"
              class="btn btn--secondary"
              id="fraudshield-cancel-btn"
            >
              Cancel Transaction
            </button>

            <button
              type="button"
              class="btn btn--primary"
              id="fraudshield-confirm-btn"
            >
              I Understand — Continue
            </button>
          </div>
        </div>
      `
      : "";

  result.innerHTML = `
    <div class="risk-result-card">

      <div class="risk-result-card__header">
        <div>

          <span class="risk-result-card__label">
            FRAUDSHIELD ANALYSIS
          </span>

          <h3>
            ${escapeHtml(headline)}
          </h3>

        </div>

        <span
          class="risk-result-badge risk-result-badge--${badgeClass}"
        >
          ${escapeHtml(
            normalizedRiskLevel.toUpperCase()
          )}
        </span>

      </div>


      <div class="risk-score">

        <span class="risk-score__label">
          Risk Score
        </span>

        <strong>
          ${score.toFixed(2)}/100
        </strong>

      </div>


      ${
        summary
          ? `
            <div class="risk-reasons">
              <h4>Assessment</h4>
              <p>
                ${escapeHtml(summary)}
              </p>
            </div>
          `
          : ""
      }


      ${
        message
          ? `
            <div class="risk-reasons">
              <h4>Recommendation</h4>
              <p>
                ${escapeHtml(message)}
              </p>
            </div>
          `
          : ""
      }


      <div class="risk-result-details">

        <div>
          <span>Transaction ID</span>
          <strong>
            ${escapeHtml(transaction.id)}
          </strong>
        </div>

        <div>
          <span>Merchant</span>
          <strong>
            ${escapeHtml(transaction.merchant)}
          </strong>
        </div>

        <div>
          <span>Customer</span>
          <strong>
            ${escapeHtml(transaction.customer)}
          </strong>
        </div>

        <div>
          <span>Amount</span>
          <strong>
            ${escapeHtml(transaction.currency)}
            ${transaction.amount.toFixed(2)}
          </strong>
        </div>

        <div>
          <span>Location</span>
          <strong>
            ${escapeHtml(transaction.location)}
          </strong>
        </div>

        <div>
          <span>Status</span>
          <strong
            id="fraudshield-transaction-status"
          >
            ${escapeHtml(
              transaction.status.toUpperCase()
            )}
          </strong>
        </div>

      </div>


      ${
        Object.keys(componentRisks).length > 0
          ? `
            <div class="risk-result-details">
              ${componentHtml}
            </div>
          `
          : ""
      }


      <div class="risk-reasons">

        <h4>
          Risk Indicators
        </h4>

        <ul>
          ${safeReasons
            .map(
              (reason) =>
                `<li>${escapeHtml(String(reason))}</li>`
            )
            .join("")}
        </ul>

      </div>


      ${confirmationHtml}

    </div>
  `;


  attachConfirmationHandlers(
    transaction,
    result,
    requiresConfirmation
  );


  result.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}


/* =========================================================
   CONFIRMATION / CANCEL
   ========================================================= */

function attachConfirmationHandlers(
  transaction,
  result,
  requiresConfirmation
) {
  if (!requiresConfirmation) {
    return;
  }

  const confirmButton =
    document.getElementById(
      "fraudshield-confirm-btn"
    );

  const cancelButton =
    document.getElementById(
      "fraudshield-cancel-btn"
    );

  const statusElement =
    document.getElementById(
      "fraudshield-transaction-status"
    );


  if (confirmButton) {
    confirmButton.addEventListener(
      "click",
      () => {
        transaction.status = "authorized";

        if (statusElement) {
          statusElement.textContent =
            "AUTHORIZED";
        }

        updateStoredTransaction(
          transaction
        );

        showDecisionMessage(
          result,
          "Transaction continued",
          "The user explicitly acknowledged the warning and continued with the transaction."
        );
      }
    );
  }


  if (cancelButton) {
    cancelButton.addEventListener(
      "click",
      () => {
        transaction.status = "cancelled";

        if (statusElement) {
          statusElement.textContent =
            "CANCELLED";
        }

        updateStoredTransaction(
          transaction
        );

        showDecisionMessage(
          result,
          "Transaction cancelled",
          "The transaction was stopped after the FraudShield warning."
        );
      }
    );
  }
}


/* =========================================================
   DECISION MESSAGE
   ========================================================= */

function showDecisionMessage(
  result,
  title,
  message
) {
  const existing =
    result.querySelector(
      ".fraudshield-decision-message"
    );

  if (existing) {
    existing.remove();
  }

  const section =
    document.createElement("div");

  section.className =
    "risk-reasons fraudshield-decision-message";

  section.innerHTML = `
    <h4>
      ${escapeHtml(title)}
    </h4>

    <p>
      ${escapeHtml(message)}
    </p>
  `;

  result
    .querySelector(".risk-result-card")
    ?.appendChild(section);
}


/* =========================================================
   UPDATE LOCAL TRANSACTION
   ========================================================= */

function updateStoredTransaction(
  transaction
) {
  const transactions =
    JSON.parse(
      localStorage.getItem(
        "fraudshield_new_transactions"
      )
    ) || [];

  const index =
    transactions.findIndex(
      (item) =>
        item.id === transaction.id
    );

  if (index !== -1) {
    transactions[index] = transaction;

    localStorage.setItem(
      "fraudshield_new_transactions",
      JSON.stringify(transactions)
    );
  }
}


/* =========================================================
   FORMAT HELPERS
   ========================================================= */

function formatComponentName(name) {
  return String(name)
    .replace(/_/g, " ")
    .replace(/\b\w/g, (char) =>
      char.toUpperCase()
    );
}


function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
