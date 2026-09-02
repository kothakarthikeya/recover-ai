/**
 * Safe currency formatter converting integer paise to Rupee representation.
 * E.g., 1250000 -> ₹12,500.00
 */
export function formatCurrency(paise: number): string {
  if (isNaN(paise) || paise === null || paise === undefined) return "₹0.00";
  const rupees = paise / 100.0;
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(rupees);
}

/**
 * Format decimal/rate to percentage string.
 * E.g. 0.745 -> 74.5%
 */
export function formatPercent(value: number): string {
  if (isNaN(value) || value === null || value === undefined) return "0%";
  const pct = value <= 1.0 && value >= 0.0 ? value * 100 : value;
  return `${pct.toFixed(1)}%`;
}

/**
 * Format raw event_type enum to human-friendly title.
 */
export function formatEventType(eventType: string): string {
  const map: Record<string, string> = {
    payment_failure: "Payment Failure",
    checkout_abandonment: "Checkout Abandonment",
    subscription_failure: "Subscription Failure",
    overdue_invoice: "Overdue B2B Invoice",
  };
  return map[eventType] || eventType.replace(/_/g, " ");
}

/**
 * Format strategy enum to human-friendly name.
 */
export function formatStrategy(strategy: string): string {
  const map: Record<string, string> = {
    SMART_RETRY: "Smart Retry",
    PAYMENT_REMINDER: "Payment Reminder",
    PAYMENT_LINK: "Payment Link",
    SUBSCRIPTION_RETRY: "Subscription Retry",
    ESCALATE: "Escalate for Approval",
    NO_ACTION: "No Action",
  };
  return map[strategy] || strategy;
}

/**
 * Format date string to localized readable date-time.
 */
export function formatDate(dateStr: string): string {
  if (!dateStr) return "-";
  try {
    const d = new Date(dateStr);
    return new Intl.DateTimeFormat("en-IN", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    }).format(d);
  } catch {
    return dateStr;
  }
}
