import { z } from 'zod';

export const transactionSchema = z.object({
    amount: z.number().min(0.01, { message: "Amount must be greater than 0" }),
    merchant_category: z.string().min(1, { message: "Merchant category is required" }),
    transaction_type: z.string().min(1, { message: "Transaction type is required" }),
    country: z.string().min(2, { message: "Country code is required" }),
    device_risk_score: z.number().min(0).max(1),
    ip_risk_score: z.number().min(0).max(1),
    hour: z.number().min(0).max(23),
    user_email: z.string().email().optional().or(z.literal('')),
    currency: z.string().optional(),
});
