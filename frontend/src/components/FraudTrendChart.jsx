import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';

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

const FRAUD_STATUSES = new Set(['FLAGGED', 'BLOCKED', 'VERIFICATION_SENT']);

export default function FraudTrendChart({ txData }) {
    const dynamicChartData = (Array.isArray(txData) ? txData : []).reduce((acc, tx) => {
        if (!tx || typeof tx !== 'object') return acc;
        const hour = safeHourBucket(tx?.created_at);
        const status = typeof tx?.status === 'string' ? tx.status.toUpperCase() : '';
        const isApproved = status === 'APPROVED';
        const isFraud = FRAUD_STATUSES.has(status);

        let point = acc.find(p => p.time === hour);
        if (!point) {
            point = { time: hour, fraud: 0, approved: 0 };
            acc.push(point);
        }

        if (isApproved) point.approved += 1;
        if (isFraud) point.fraud += 1;
        return acc;
    }, []).sort((a, b) => (a.time > b.time ? 1 : -1));

    const finalChartData = dynamicChartData.length > 0
        ? dynamicChartData
        : [
            { time: '00:00', fraud: 0, approved: 0 },
            { time: '06:00', fraud: 0, approved: 0 },
            { time: '12:00', fraud: 0, approved: 0 },
            { time: '18:00', fraud: 0, approved: 0 },
        ];

    return (
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
    );
}
