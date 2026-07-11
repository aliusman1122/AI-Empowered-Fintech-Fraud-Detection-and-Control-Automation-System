import { useState } from 'react';
import { predictTransaction } from '../services/api';
import { AlertTriangle, CheckCircle, Loader2, AlertCircle } from 'lucide-react';

export default function TransactionForm({ onTransactionSubmitted }) {
    const [formData, setFormData] = useState({
        amount: '',
        hour: '',
        device_risk_score: '',
        ip_risk_score: '',
        merchant_category: 'other',
        transaction_type: 'online',
        country: 'US',
        user_email: ''
    });

    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null);
    const [error, setError] = useState(null);
    const [validationError, setValidationError] = useState(null);

    const handleChange = (e) => {
        const { name, value } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: value
        }));
    };

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError(null);
        setResult(null);
        setValidationError(null);

        // Build a strictly typed payload — ensure all numeric fields are parsed,
        // and country is trimmed to the ISO 2-letter code (e.g. "PK - Pakistan" → "PK").
        const payload = {
            amount: parseFloat(formData.amount) || 0,
            hour: parseInt(formData.hour, 10) || 0,
            device_risk_score: parseFloat(formData.device_risk_score) || 0,
            ip_risk_score: parseFloat(formData.ip_risk_score) || 0,
            merchant_category: (formData.merchant_category || 'other').toLowerCase().trim(),
            transaction_type: (formData.transaction_type || 'online').toLowerCase().trim(),
            // Split "PK - Pakistan" → "PK", guard against missing value
            country: (formData.country || 'US').split(' ')[0].trim().toUpperCase().substring(0, 2),
            user_email: formData.user_email || null,
        };

        try {
            const response = await predictTransaction(payload);
            setResult(response ?? {});
            if (onTransactionSubmitted) {
                onTransactionSubmitted();
            }
        } catch (err) {
            const status = err?.response?.status;
            if (status === 422) {
                // Extract Pydantic validation detail array or fallback string
                const detail = err?.response?.data?.detail;
                let msg = 'Invalid data formatting sent to server.';
                if (Array.isArray(detail)) {
                    msg = detail.map(d => `${d?.loc?.join(' → ')}: ${d?.msg}`).join(' | ');
                } else if (typeof detail === 'string') {
                    msg = detail;
                }
                setValidationError(msg);
            } else {
                setError(err?.response?.data?.detail || err?.message || 'Failed to submit transaction.');
            }
        } finally {
            setLoading(false);
        }
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
                            <h3 className="text-lg font-bold text-red-400">Suspicious Fraud Alert</h3>
                            <p className="text-red-300/80 text-sm mt-1">{result?.message || 'Transaction flagged for review.'}</p>

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

            {/* 422 Validation Error Banner (amber/gold) */}
            {validationError && (
                <div className="mb-6 p-4 bg-amber-500/10 border border-amber-500/50 rounded-lg flex items-start gap-3">
                    <AlertCircle className="text-amber-400 shrink-0 mt-0.5" size={20} />
                    <div>
                        <p className="text-amber-400 font-semibold text-sm">Validation Error (422)</p>
                        <p className="text-amber-300/80 text-sm mt-0.5">{validationError}</p>
                    </div>
                </div>
            )}

            {/* Generic Error Banner */}
            {error && (
                <div className="mb-6 p-4 bg-red-500/10 border border-red-500/50 rounded-lg text-red-400 text-sm">
                    {error}
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-5">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">Amount ($)</label>
                        <input
                            type="number" step="0.01" name="amount" required
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                            placeholder="e.g. 1250.00"
                            onChange={handleChange}
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">Hour of Day (0-23)</label>
                        <input
                            type="number" min="0" max="23" name="hour" required
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                            placeholder="e.g. 14"
                            onChange={handleChange}
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">Device Risk Score (0-1)</label>
                        <input
                            type="number" step="0.01" min="0" max="1" name="device_risk_score" required
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                            placeholder="e.g. 0.85"
                            onChange={handleChange}
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">IP Risk Score (0-1)</label>
                        <input
                            type="number" step="0.01" min="0" max="1" name="ip_risk_score" required
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                            placeholder="e.g. 0.2"
                            onChange={handleChange}
                        />
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">Merchant Category</label>
                        <select
                            name="merchant_category"
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                            onChange={handleChange}
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
                    </div>

                    <div className="space-y-1.5">
                        <label className="text-sm font-medium text-slate-300">Country</label>
                        <select
                            name="country"
                            className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                            onChange={handleChange}
                            defaultValue="US"
                        >
                            <option value="US">US - United States</option>
                            <option value="GB">GB - United Kingdom</option>
                            <option value="PK">PK - Pakistan</option>
                            <option value="RU">RU - Russia</option>
                            <option value="AE">AE - UAE</option>
                        </select>
                    </div>
                </div>

                <div className="space-y-1.5">
                    <label className="text-sm font-medium text-slate-300">User Email <span className="text-slate-500">(Optional — triggers n8n verification)</span></label>
                    <input
                        type="email" name="user_email"
                        className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all outline-none"
                        placeholder="user@example.com"
                        onChange={handleChange}
                    />
                </div>

                <button
                    type="submit"
                    disabled={loading}
                    className="w-full mt-4 bg-indigo-600 hover:bg-indigo-500 disabled:opacity-60 disabled:cursor-not-allowed text-white font-medium py-3 rounded-lg shadow-lg shadow-indigo-500/20 transition-all flex items-center justify-center gap-2"
                >
                    {loading ? <Loader2 className="animate-spin" size={20} /> : 'Process Transaction'}
                </button>
            </form>
        </div>
    );
}
