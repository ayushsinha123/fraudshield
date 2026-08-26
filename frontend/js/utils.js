/**
 * FraudShield — shared utilities
 */

const FraudShieldUtils = {
  /**
   * Format a number as currency.
   * @param {number} amount
   * @param {string} currency
   * @returns {string}
   */
  formatCurrency(amount, currency = "USD") {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency,
      minimumFractionDigits: 2,
    }).format(amount);
  },

  /**
   * Format an ISO date string for display.
   * @param {string} isoString
   * @param {object} options
   * @returns {string}
   */
  formatDate(isoString, options = {}) {
    const defaults = {
      month: "short",
      day: "numeric",
      year: "numeric",
    };
    return new Intl.DateTimeFormat("en-US", { ...defaults, ...options }).format(
      new Date(isoString)
    );
  },

  /**
   * Format an ISO date string as relative time (e.g. "2 hours ago").
   * @param {string} isoString
   * @returns {string}
   */
  formatRelativeTime(isoString) {
    const now = Date.now();
    const then = new Date(isoString).getTime();
    const diffSec = Math.round((then - now) / 1000);
    const absSec = Math.abs(diffSec);

    const units = [
      { limit: 60, divisor: 1, unit: "second" },
      { limit: 3600, divisor: 60, unit: "minute" },
      { limit: 86400, divisor: 3600, unit: "hour" },
      { limit: 604800, divisor: 86400, unit: "day" },
      { limit: 2592000, divisor: 604800, unit: "week" },
      { limit: 31536000, divisor: 2592000, unit: "month" },
      { limit: Infinity, divisor: 31536000, unit: "year" },
    ];

    const rtf = new Intl.RelativeTimeFormat("en", { numeric: "auto" });

    for (const { limit, divisor, unit } of units) {
      if (absSec < limit) {
        const value = Math.round(diffSec / divisor);
        return rtf.format(value, unit);
      }
    }

    return rtf.format(0, "second");
  },

  /**
   * Map a risk level to badge CSS class.
   * @param {"low"|"medium"|"high"|"critical"} level
   * @returns {string}
   */
  getRiskBadgeClass(level) {
    const map = {
      low: "badge--safe",
      medium: "badge--warning",
      high: "badge--high-risk",
      critical: "badge--high-risk",
    };
    return map[level] || "badge--neutral";
  },

  /**
   * Map a risk level to human-readable label.
   * @param {"low"|"medium"|"high"|"critical"} level
   * @returns {string}
   */
  getRiskLabel(level) {
    const map = {
      low: "Low Risk",
      medium: "Medium Risk",
      high: "High Risk",
      critical: "Critical",
    };
    return map[level] || "Unknown";
  },

  /**
   * Map a transaction status to badge CSS class.
   * @param {string} status
   * @returns {string}
   */
  getStatusBadgeClass(status) {
    const map = {
      approved: "badge--safe",
      pending: "badge--warning",
      flagged: "badge--high-risk",
      blocked: "badge--high-risk",
      review: "badge--warning",
    };
    return map[status] || "badge--neutral";
  },

  /**
   * Capitalize the first letter of a string.
   * @param {string} str
   * @returns {string}
   */
  capitalize(str) {
    if (!str) return "";
    return str.charAt(0).toUpperCase() + str.slice(1);
  },

  /**
   * Truncate text with ellipsis.
   * @param {string} str
   * @param {number} maxLength
   * @returns {string}
   */
  truncate(str, maxLength = 40) {
    if (!str || str.length <= maxLength) return str;
    return str.slice(0, maxLength - 1) + "…";
  },

  /**
   * Generate initials from a full name.
   * @param {string} name
   * @returns {string}
   */
  getInitials(name) {
    if (!name) return "?";
    return name
      .split(" ")
      .filter(Boolean)
      .slice(0, 2)
      .map((part) => part[0].toUpperCase())
      .join("");
  },

  /**
   * Debounce a function call.
   * @param {Function} fn
   * @param {number} delay
   * @returns {Function}
   */
  debounce(fn, delay = 300) {
    let timer;
    return function (...args) {
      clearTimeout(timer);
      timer = setTimeout(() => fn.apply(this, args), delay);
    };
  },
};

if (typeof window !== "undefined") {
  window.FraudShieldUtils = FraudShieldUtils;
}
