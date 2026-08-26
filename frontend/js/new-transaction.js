document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("new-transaction-form");

  if (!form) return;

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    const formData = new FormData(form);

    const transaction = {
      id: generateTransactionId(),
      merchant: formData.get("merchant"),
      customer: formData.get("customer"),
      amount: Number(formData.get("amount")),
      currency: formData.get("currency"),
      location: formData.get("location"),
      category: formData.get("category"),
      description: formData.get("description"),
      date: new Date().toISOString(),
      status: "pending",
      riskLevel: "low"
    };

    analyzeTransaction(transaction);
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
   FRAUDSHIELD RISK ANALYSIS
   ========================================================= */

function analyzeTransaction(transaction) {

  let score = 0;
  const reasons = [];

  /* Amount Risk */

  if (transaction.amount >= 10000) {
    score += 40;
    reasons.push("Extremely high transaction amount");
  } 
  else if (transaction.amount >= 5000) {
    score += 30;
    reasons.push("High transaction amount");
  } 
  else if (transaction.amount >= 2000) {
    score += 15;
    reasons.push("Unusually large transaction amount");
  }


  /* Location Risk */

  const location = transaction.location.trim().toLowerCase();

  if (
    location === "unknown" ||
    location === "nigeria" ||
    location === "russia"
  ) {
    score += 25;
    reasons.push("Suspicious transaction location");
  }


  /* Missing Description */

  if (!transaction.description.trim()) {
    score += 5;
    reasons.push("Transaction description is missing");
  }


  /* Maximum Score */

  score = Math.min(score, 100);


  /* Risk Level */

  let riskLevel = "low";

  if (score >= 70) {
    riskLevel = "critical";
  } 
  else if (score >= 40) {
    riskLevel = "high";
  } 
  else if (score >= 20) {
    riskLevel = "medium";
  }


  if (reasons.length === 0) {
    reasons.push("No significant risk indicators detected");
  }


  /* Update Transaction */

  transaction.riskLevel = riskLevel;


  if (
    riskLevel === "critical" ||
    riskLevel === "high"
  ) {
    transaction.status = "flagged";
  } 
  else if (riskLevel === "medium") {
    transaction.status = "review";
  } 
  else {
    transaction.status = "approved";
  }


  /* Save */

  saveTransaction(transaction);


  /* Display */

  showResult(
    transaction,
    score,
    riskLevel,
    reasons
  );
}


/* =========================================================
   SAVE TRANSACTION
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
    JSON.stringify(
      existingTransactions
    )
  );


  console.log(
    "FraudShield transaction saved:",
    transaction
  );
}


/* =========================================================
   DISPLAY RESULT
   ========================================================= */

function showResult(
  transaction,
  score,
  riskLevel,
  reasons
) {

  let result =
    document.getElementById(
      "transaction-risk-result"
    );


  if (!result) {

    result =
      document.createElement("section");

    result.id =
      "transaction-risk-result";

    result.className =
      "transaction-risk-result";


    const form =
      document.getElementById(
        "new-transaction-form"
      );


    form.parentElement.insertAdjacentElement(
      "afterend",
      result
    );
  }


  /* Badge */

  let badgeClass = "safe";

  if (riskLevel === "medium") {
    badgeClass = "medium";
  }

  if (
    riskLevel === "high" ||
    riskLevel === "critical"
  ) {
    badgeClass = "high";
  }


  /* Result HTML */

  result.innerHTML = `

    <div class="risk-result-card">


      <div class="risk-result-card__header">

        <div>

          <span class="risk-result-card__label">
            FRAUDSHIELD ANALYSIS
          </span>

          <h3>
            Transaction Risk Result
          </h3>

        </div>


        <span
          class="risk-result-badge risk-result-badge--${badgeClass}"
        >
          ${riskLevel.toUpperCase()}
        </span>

      </div>


      <div class="risk-score">

        <span class="risk-score__label">
          Risk Score
        </span>

        <strong>
          ${score}/100
        </strong>

      </div>


      <div class="risk-result-details">


        <div>

          <span>
            Transaction ID
          </span>

          <strong>
            ${transaction.id}
          </strong>

        </div>


        <div>

          <span>
            Merchant
          </span>

          <strong>
            ${transaction.merchant}
          </strong>

        </div>


        <div>

          <span>
            Customer
          </span>

          <strong>
            ${transaction.customer}
          </strong>

        </div>


        <div>

          <span>
            Amount
          </span>

          <strong>
            ${transaction.currency}
            ${transaction.amount.toFixed(2)}
          </strong>

        </div>


        <div>

          <span>
            Location
          </span>

          <strong>
            ${transaction.location}
          </strong>

        </div>


        <div>

          <span>
            Status
          </span>

          <strong>
            ${transaction.status.toUpperCase()}
          </strong>

        </div>


      </div>


      <div class="risk-reasons">

        <h4>
          Risk Indicators
        </h4>


        <ul>

          ${reasons
            .map(
              reason =>
                `<li>${reason}</li>`
            )
            .join("")}

        </ul>

      </div>


    </div>

  `;


  result.scrollIntoView({
    behavior: "smooth",
    block: "start"
  });
}