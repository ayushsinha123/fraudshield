/**
 * FraudShield — mock data for development
 * Replace with API calls when backend is available.
 */

const FraudShieldMockData = {
  currentUser: {
    id: "usr_001",
    name: "Alex Morgan",
    email: "alex.morgan@fraudshield.io",
    role: "Fraud Analyst",
    initials: "AM",
  },

  navigation: [
    {
      section: "Main",
      items: [
        { id: "dashboard", label: "Dashboard", href: "pages/dashboard.html", icon: "dashboard" },
        { id: "transactions", label: "Transactions", href: "pages/transactions.html", icon: "transactions" },
        { id: "alerts", label: "Alerts", href: "pages/alerts.html", icon: "alerts", badge: 12 },
      ],
    },
    {
      section: "Insights",
      items: [
        { id: "analytics", label: "Analytics", href: "pages/analytics.html", icon: "analytics" },
        { id: "reports", label: "Reports", href: "pages/reports.html", icon: "reports" },
      ],
    },
    {
      section: "System",
      items: [
        { id: "settings", label: "Settings", href: "pages/settings.html", icon: "settings" },
      ],
    },
  ],

  dashboardStats: [
    { id: "flagged", label: "Flagged Today", value: 47, change: 12, trend: "up" },
    { id: "blocked", label: "Blocked Amount", value: 284500, change: -8, trend: "down", isCurrency: true },
    { id: "accuracy", label: "Detection Rate", value: 98.4, change: 1.2, trend: "up", suffix: "%" },
    { id: "pending", label: "Pending Review", value: 23, change: 5, trend: "up" },
  ],

  transactions: [
    {
      id: "txn_8f3a2b",
      merchant: "Global Tech Supplies",
      customer: "Sarah Chen",
      amount: 4299.99,
      currency: "USD",
      status: "flagged",
      riskLevel: "high",
      date: "2026-08-16T08:42:00Z",
      location: "Singapore",
    },
    {
      id: "txn_7e2c1d",
      merchant: "Metro Coffee Co.",
      customer: "James Wilson",
      amount: 12.50,
      currency: "USD",
      status: "approved",
      riskLevel: "low",
      date: "2026-08-16T08:38:00Z",
      location: "New York, US",
    },
    {
      id: "txn_6d1b0a",
      merchant: "Luxury Watches Ltd",
      customer: "Unknown User",
      amount: 15750.00,
      currency: "USD",
      status: "blocked",
      riskLevel: "critical",
      date: "2026-08-16T08:15:00Z",
      location: "Lagos, NG",
    },
    {
      id: "txn_5c0a9f",
      merchant: "CloudHost Pro",
      customer: "DevOps Team Inc",
      amount: 890.00,
      currency: "USD",
      status: "review",
      riskLevel: "medium",
      date: "2026-08-16T07:55:00Z",
      location: "London, UK",
    },
    {
      id: "txn_4b9e8d",
      merchant: "FreshMart Grocery",
      customer: "Maria Garcia",
      amount: 156.32,
      currency: "USD",
      status: "approved",
      riskLevel: "low",
      date: "2026-08-16T07:30:00Z",
      location: "Miami, US",
    },
  ],

  alerts: [
    {
      id: "alert_001",
      title: "Unusual velocity pattern detected",
      description: "12 transactions from same card within 5 minutes",
      riskLevel: "high",
      status: "open",
      timestamp: "2026-08-16T08:40:00Z",
      transactionId: "txn_8f3a2b",
    },
    {
      id: "alert_002",
      title: "Geolocation mismatch",
      description: "Card used in two countries within 30 minutes",
      riskLevel: "critical",
      status: "open",
      timestamp: "2026-08-16T08:12:00Z",
      transactionId: "txn_6d1b0a",
    },
    {
      id: "alert_003",
      title: "New device login attempt",
      description: "First-time device accessing high-value account",
      riskLevel: "medium",
      status: "investigating",
      timestamp: "2026-08-16T07:50:00Z",
      transactionId: null,
    },
  ],

  riskDistribution: [
    { level: "low", count: 1240, percentage: 72 },
    { level: "medium", count: 310, percentage: 18 },
    { level: "high", count: 142, percentage: 8 },
    { level: "critical", count: 34, percentage: 2 },
  ],
};

if (typeof window !== "undefined") {
  window.FraudShieldMockData = FraudShieldMockData;
}
