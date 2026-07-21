import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

export default function ModelPerformanceChart({ txData }) {
    // Generate risk distribution buckets
    const distribution = (Array.isArray(txData) ? txData : []).reduce((acc, tx) => {
        if (!tx || typeof tx !== 'object') return acc;
        const risk = Number(tx.fraud_probability) || 0;

        if (risk < 0.2) acc[0].count++;
        else if (risk < 0.5) acc[1].count++;
        else if (risk < 0.8) acc[2].count++;
        else acc[3].count++;

        return acc;
    }, [
        { bucket: '0.0 - 0.2 (Low)', count: 0 },
        { bucket: '0.2 - 0.5 (Med)', count: 0 },
        { bucket: '0.5 - 0.8 (High)', count: 0 },
        { bucket: '0.8 - 1.0 (Crit)', count: 0 },
    ]);

    return (
        <ResponsiveContainer width="100%" height="100%">
            <BarChart data={distribution} margin={{ top: 10, right: 30, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#334155" vertical={false} />
                <XAxis dataKey="bucket" stroke="#475569" tick={{ fill: '#94a3b8', fontSize: 12 }} />
                <YAxis stroke="#475569" tick={{ fill: '#94a3b8' }} />
                <Tooltip
                    contentStyle={{ backgroundColor: '#1e293b', borderColor: '#334155', color: '#f8fafc' }}
                    itemStyle={{ color: '#e2e8f0' }}
                    cursor={{ fill: '#334155', opacity: 0.4 }}
                />
                <Legend wrapperStyle={{ paddingTop: '20px' }} />
                <Bar dataKey="count" name="Transactions" fill="#6366f1" radius={[4, 4, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    );
}
