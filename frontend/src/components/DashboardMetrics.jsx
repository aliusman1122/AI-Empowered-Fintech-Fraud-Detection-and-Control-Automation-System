import { useEffect, useState } from 'react';
import { getSystemStats, getTransactions } from '../services/api';
import { Activity, ShieldAlert, CheckCircle, Clock } from 'lucide-react';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

// Safely parse a date string and extract the hour bucket (e.g. "14:00").
// Returns "00:00" if the string is missing, null, or produces an invalid Date.
function safeHourBucket(dateStr) {
    if (!dateStr) return '00:00';
    try {
        const d = new Date(dateStr);
        if (isNaN(d.getTime())) return '00:00';
        const h = d.getHours();
        return `${String(h).padStart(2, '0')}:00`;
    } catch {
        return '00:00';
    }
}

// Known statuses — any unknown value falls through without crashing.
const FRAUD_STATUSES = new Set(['FLAGGED', 'BLOCKED', 'VERIFICATION_SENT']);

export default function DashboardMetrics({ refreshTrigger }) {
    const [stats, setStats] = useState(null);
    const [txData, setTxData] = useState([]);

    useEffect(() => {
        let cancelled = false;

        const fetchData = async () => {
            try {
                // Use static import (already imported at top) — no dynamic import() in effects.
                const [statsResponse, txResponse] = await Promise.allSettled([
                    getSystemStats(),
                    getTransactions(100),
                ]);

                if (cancelled) return;

                setStats(
                    statsResponse.status === 'fulfilled' ? (statsResponse.value ?? null) : null
                );
                setTxData(
                    txResponse.status === 'fulfilled' && Array.isArray(txResponse.value)
                        ? txResponse.value
                        : []
                );
            } catch (err) {
                if (!cancelled) console.error('DashboardMetrics fetch error:', err);
            }
        };

        fetchData();
        return () => { cancelled = true; };
    }, [refreshTrigger]);

    // Build hourly chart buckets with rigid defensive checks on every field.
    const dynamicChartData = (Array.isArray(txData) ? txData : []).reduce((acc, tx) => {
        if (!tx || typeof tx !== 'object') return acc;  // skip corrupt entries

        const hour = safeHourBucket(tx?.created_at);
        const status = typeof tx?.status === 'string' ? tx.status.toUpperCase() : '';
        const isApproved = status === 'APPROVED';
        const isFraud = FRAUD_STATUSES.has(status);
        const amount = Number(tx?.amount) || 0;
        const risk = Number(tx?.fraud_probability) || 0;

        let point = acc.find(p => p.time === hour);
        if (!point) {
            point = { time: hour, fraud: 0, approved: 0, amount: 0, risk: 0 };
            acc.push(point);
        }

        if (isApproved) point.approved += 1;
        if (isFraud) point.fraud += 1;
        point.amount = Number((point.amount + amount).toFixed(2));
        point.risk = Number(risk.toFixed(4));

        return acc;
    }, []).sort((a, b) => (a.time > b.time ? 1 : -1));

    // Always guarantee at least one valid fallback data point for Recharts.
    const finalChartData = dynamicChartData.length > 0
        ? dynamicChartData
        : [
            { time: '00:00', fraud: 0, approved: 0 },
            { time: '06:00', fraud: 0, approved: 0 },
            { time: '12:00', fraud: 0, approved: 0 },
            { time: '18:00', fraud: 0, approved: 0 },
        ];

    // Derive counts from live transaction array to prevent static blanks
    const safeTxData = Array.isArray(txData) ? txData : [];
    const fraudCount = safeTxData.filter(tx => tx?.status === 'BLOCKED' || tx?.status === 'FLAGGED').length;
    const approvedCount = safeTxData.filter(tx => tx?.status === 'APPROVED').length;
    const pendingCount = safeTxData.filter(tx => tx?.status === 'VERIFICATION_SENT').length;
    const totalTxCount = safeTxData.length;

    const cards = [
        {
            title: 'Total Transactions',
            value: stats?.total_transactions ?? totalTxCount,
            icon: <Activity className="text-blue-400" size={24} />,
            bg: 'bg-blue-500/10'
        },
        {
            title: 'Fraud Alerts',
            value: stats?.flagged_transactions ?? fraudCount,
            icon: <ShieldAlert className="text-red-400" size={24} />,
            bg: 'bg-red-500/10'
        },
        {
            title: 'Auto-Approved',
            value: stats?.approved_transactions ?? approvedCount,
            icon: <CheckCircle className="text-emerald-400" size={24} />,
            bg: 'bg-emerald-500/10'
        },
        {
            title: 'Pending Verifications',
            value: stats?.pending_verifications ?? pendingCount,
            icon: <Clock className="text-amber-400" size={24} />,
            bg: 'bg-amber-500/10'
        },
    ];

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                {cards.map((card, index) => (
                    <div key={index} className="card flex items-center p-6 gap-4 border-slate-700/50 hover:border-slate-600 transition-colors">
                        <div className={`p-4 rounded-xl ${card.bg}`}>
                            {card.icon}
                        </div>
                        <div>
                            <p className="text-slate-400 text-sm font-medium">{card.title}</p>
                            <h3 className="text-2xl font-bold text-white mt-1">{String(card.value)}</h3>
                        </div>
                    </div>
                ))}
            </div>

            <div className="card border-slate-700/50">
                <h3 className="text-lg font-medium text-white mb-6">Transaction Activity</h3>
                <div className="h-72 w-full">
                    <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={finalChartData} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                            <defs>
                                <linearGradient id="colorApproved" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                                </linearGradient>
                                <linearGradient id="colorFraud" x1="0" y1="0" x2="0" y2="1">
                                    <stop offset="5%" stopColor="#ef4444" stopOpacity={0.3} />
                                    <stop offset="95%" stopColor="#ef4444" stopOpacity={0} />
                                </linearGradient>
                            </defs>
                            <XAxis dataKey="time" stroke="#475569" tick={{ fill: '#94a3b8' }} />
                            <YAxis stroke="#475569" tick={{ fill: '#94a3b8' }} />
                            <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                                itemStyle={{ color: '#e2e8f0' }}
                            />
                            <Area type="monotone" dataKey="approved" stroke="#10b981" fillOpacity={1} fill="url(#colorApproved)" />
                            <Area type="monotone" dataKey="fraud" stroke="#ef4444" fillOpacity={1} fill="url(#colorFraud)" />
                        </AreaChart>
                    </ResponsiveContainer>
                </div>
            </div>
        </div>
    );
}
