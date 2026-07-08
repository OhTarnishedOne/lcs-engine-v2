// ============================================
// Billing API — add to lib/api/client.ts
// ============================================

// Add to the types import at the top of client.ts:
// BillingStatus, CheckoutSessionResponse

async createCheckoutSession(): Promise<{ url: string }> {
  return this.post<{ url: string }>("/billing/create-checkout-session");
}

async getBillingStatus(): Promise<{ tier: string; is_pro: boolean }> {
  return this.get<{ tier: string; is_pro: boolean }>("/billing/status");
}
