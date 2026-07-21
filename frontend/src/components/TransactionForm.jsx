import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { transactionSchema } from '../schemas/transactionSchema';
import { useCreateTransaction } from '../hooks/useTransactions';
import { AlertTriangle, CheckCircle, Loader2, AlertCircle } from 'lucide-react';
import { useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';

export default function TransactionForm({ onTransactionSubmitted }) {
    const { register, handleSubmit, formState: { errors }, reset, watch } = useForm({
        resolver: zodResolver(transactionSchema),
        defaultValues: {
            amount: '',
            hour: '',
            device_risk_score: '',
            ip_risk_score: '',
            merchant_category: 'other',
            transaction_type: 'online',
            country: 'US',
            user_email: ''
        }
    });

    const createTransaction = useCreateTransaction();
    const queryClient = useQueryClient();
    const [result, setResult] = useState(null);

    const watchedCountry = watch('country') || 'US';

    const getCurrencyInfo = (countryCode) => {
        const mapping = {
            'US': { sym: '$', code: 'USD' },
            'GB': { sym: '£', code: 'GBP' },
            'PK': { sym: 'Rs', code: 'PKR' },
            'AE': { sym: 'د.إ', code: 'AED' },
            'RU': { sym: '₽', code: 'RUB' }
        };
        return mapping[countryCode] || { sym: '$', code: 'USD' };
    };

    const activeCurrency = getCurrencyInfo(watchedCountry);

    const onSubmit = (data) => {
        setResult(null);

        // Zod validation success. Trigger mutation.
        const payload = {
            amount: parseFloat(data.amount) || 0,
            hour: parseInt(data.hour, 10) || 0,
            device_risk_score: parseFloat(data.device_risk_score) || 0,
            ip_risk_score: parseFloat(data.ip_risk_score) || 0,
            merchant_category: (data.merchant_category || 'other').toLowerCase().trim(),
            transaction_type: (data.transaction_type || 'online').toLowerCase().trim(),
            country: (data.country || 'US').split(' ')[0].trim().toUpperCase().substring(0, 2),
            currency: getCurrencyInfo(data.country || 'US').code,
            user_email: data.user_email || null,
        };

        createTransaction.mutate(payload, {
            onSuccess: (response) => {
                setResult(response ?? {});

                // Form reset natively via react-hook-form
                reset();

                // Real-time Dashboard invalidation
                queryClient.invalidateQueries({ queryKey: ['transactions'] });
                queryClient.invalidateQueries({ queryKey: ['stats'] });

                if (onTransactionSubmitted) {
                    onTransactionSubmitted();
                }
            },
            onError: (error) => {
                toast.error(error.response?.data?.detail || 'Failed to process transaction.');
            }
        });
    };

    return (
        <div className="card max-w-2xl mx-auto w-full border-slate-700/50 relative overflow-hidden">
            {/* Decorative gradient */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-indigo-500 to-purple-500"></div>

            <div className="mb-6">
                <h2 className="text-xl font-bold text-white tracking-tight">New Transaction</h2>
                <p className="text-slate-400 text-sm mt-1">Submit transaction details for real-time AI risk analysis.</p>
            </div>

            {/* Fraud Alert Banner */}
            {result && result?.fraud_flag === true && (
                <div className="mb-8 p-5 bg-red-500/10 border border-red-500/50 rounded-xl animate-in fade-in slide-in-from-top-4">
                    <div className="flex items-start gap-3">
                        <AlertTriangle className="text-red-400 shrink-0 mt-0.5" size={24} />
                        <div>
                            <h3 className="text-lg font-bold text-red-400">High Fraud Risk — Pending Authorization</h3>
                            <p className="text-red-300/80 text-sm mt-1">{result?.message || 'High fraud risk detected. Verification email sent for human authorization.'}</p>

                            {result?.reason_codes?.length > 0 && (
                                <div className="mt-4 space-y-2">
                                    <h4 className="text-xs font-semibold text-red-400/80 uppercase tracking-wider">Risk Factors Detected</h4>
                                    <ul className="list-disc list-inside text-sm text-red-200/90 space-y-1">
                                        {(result?.reason_codes || []).map((code, idx) => (
                                            <li key={idx}>{code}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Approved Banner */}
            {result && result?.fraud_flag === false && (
                <div className="mb-8 p-5 bg-emerald-500/10 border border-emerald-500/50 rounded-xl animate-in fade-in slide-in-from-top-4">
                    <div className="flex items-start gap-3">
                        <CheckCircle className="text-emerald-400 shrink-0 mt-0.5" size={24} />
                        <div>
                            <h3 className="text-lg font-bold text-emerald-400">Transaction Approved</h3>
                            <p className="text-emerald-300/80 text-sm mt-1">{result?.message || 'Transaction was successful.'}</p>
                        </div>
                    </div>
                </div>
            )}

            {/* Generic Error Banner */}
            {createTransaction.isError && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                    {createTransaction.error?.message || 'Failed to process transaction.'}
                </div>
            )}

            <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">
                            Amount ({activeCurrency.sym} {activeCurrency.code})
                        </label>
                        <input
                            type="number" step="0.01"
                            {...register("amount", { valueAsNumber: true })}
                            className={`w-full bg-slate-900 border ${errors.amount ? 'border-red-500' : 'border-slate-700'} rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none`}
                            placeholder="e.g. 1250.00"
                        />
                        {errors.amount && <span className="text-red-400 text-xs">{errors.amount.message}</span>}
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">Hour of Day (0-23)</label>
                        <input
                            type="number" min="0" max="23"
                            {...register("hour", { valueAsNumber: true })}
                            className={`w-full bg-slate-900 border ${errors.hour ? 'border-red-500' : 'border-slate-700'} rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none`}
                            placeholder="e.g. 14"
                        />
                        {errors.hour && <span className="text-red-400 text-xs">{errors.hour.message}</span>}
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">Device Risk Score (0-1)</label>
                        <input
                            type="number" step="0.01" min="0" max="1"
                            {...register("device_risk_score", { valueAsNumber: true })}
                            className={`w-full bg-slate-900 border ${errors.device_risk_score ? 'border-red-500' : 'border-slate-700'} rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none`}
                            placeholder="e.g. 0.85"
                        />
                        {errors.device_risk_score && <span className="text-red-400 text-xs">{errors.device_risk_score.message}</span>}
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">IP Risk Score (0-1)</label>
                        <input
                            type="number" step="0.01" min="0" max="1"
                            {...register("ip_risk_score", { valueAsNumber: true })}
                            className={`w-full bg-slate-900 border ${errors.ip_risk_score ? 'border-red-500' : 'border-slate-700'} rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none`}
                            placeholder="e.g. 0.2"
                        />
                        {errors.ip_risk_score && <span className="text-red-400 text-xs">{errors.ip_risk_score.message}</span>}
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">Merchant Category</label>
                        <select
                            {...register("merchant_category")}
                            className={`w-full bg-slate-900 border ${errors.merchant_category ? 'border-red-500' : 'border-slate-700'} rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none`}
                            defaultValue="other"
                        >
                            <option value="electronics">Electronics</option>
                            <option value="food">Food</option>
                            <option value="travel">Travel</option>
                            <option value="gambling">Gambling</option>
                            <option value="crypto">Crypto</option>
                            <option value="wire_transfer">Wire Transfer</option>
                            <option value="foreign_exchange">Foreign Exchange</option>
                            <option value="other">Other</option>
                        </select>
                        {errors.merchant_category && <span className="text-red-400 text-xs">{errors.merchant_category.message}</span>}
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">Country</label>
                        <select
                            {...register("country")}
                            className={`w-full bg-slate-900 border ${errors.country ? 'border-red-500' : 'border-slate-700'} rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none`}
                            defaultValue="US"
                        >
                            <option value="US">US - United States</option>
                            <option value="GB">GB - United Kingdom</option>
                            <option value="PK">PK - Pakistan</option>
                            <option value="RU">RU - Russia</option>
                            <option value="AE">AE - UAE</option>
                        </select>
                        {errors.country && <span className="text-red-400 text-xs">{errors.country.message}</span>}
                    </div>
                </div>

                <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-300">User Email <span className="text-slate-500">(Optional — triggers n8n verification)</span></label>
                    <input
                        type="email"
                        {...register("user_email")}
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                        placeholder="user@example.com"
                    />
                </div>

                <button
                    type="submit"
                    disabled={createTransaction.isPending}
                    className="w-full mt-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2"
                >
                    {createTransaction.isPending ? <Loader2 className="animate-spin" size={20} /> : 'Process Transaction'}
                </button>
            </form>
        </div>
    );
}
