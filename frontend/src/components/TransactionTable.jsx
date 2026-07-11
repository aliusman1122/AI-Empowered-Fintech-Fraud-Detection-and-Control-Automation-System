import { useEffect, useState } from 'react';
import { getTransactions } from '../services/api';
import { Search } from 'lucide-react';

export default function TransactionTable({ refreshTrigger }) {
    const [transactions, setTransactions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [search, setSearch] = useState('');

    useEffect(() => {
        const fetchTx = async () => {
            try {
                const data = await getTransactions(20);
                setTransactions(data);
            } catch (error) {
                console.error(error);
            } finally {
                setLoading(false);
            }
        };
        fetchTx();
    }, [refreshTrigger]);

    const filtered = transactions.filter(tx =>
        (tx?.transaction_id || '').toLowerCase().includes(search.toLowerCase()) ||
        (tx?.status || '').toLowerCase().includes(search.toLowerCase())
    );

    const getStatusColor = (status) => {
        switch (status) {
            case 'APPROVED': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
            case 'FLAGGED': return 'bg-red-500/20 text-red-400 border-red-500/30';
            case 'VERIFICATION_SENT': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
            default: return 'bg-slate-500/20 text-slate-400 border-slate-500/30';
        }
    };

    return (
        <div className="card border-slate-700/50">
            <div className="flex justify-between items-center mb-6">
                <h3 className="text-lg font-medium text-white">Recent Transactions</h3>
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-500" size={16} />
                    <input
                        type="text"
                        placeholder="Search ID or Status..."
                        value={search}
                        onChange={(e) => setSearch(e.target.value)}
                        className="bg-slate-900 border border-slate-700 rounded-lg pl-9 pr-4 py-2 text-sm text-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all w-64"
                    />
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                    <thead>
                        <tr className="border-b border-slate-700 text-slate-400 text-sm uppercase tracking-wider">
                            <th className="pb-3 px-4 font-medium">Transaction ID</th>
                            <th className="pb-3 px-4 font-medium">Amount</th>
                            <th className="pb-3 px-4 font-medium">Risk Score</th>
                            <th className="pb-3 px-4 font-medium">Status</th>
                            <th className="pb-3 px-4 font-medium">Time</th>
                        </tr>
                    </thead>
                    <tbody className="text-sm">
                        {loading ? (
                            <tr>
                                <td colSpan="5" className="text-center py-8 text-slate-500">Loading transactions...</td>
                            </tr>
                        ) : filtered.length === 0 ? (
                            <tr>
                                <td colSpan="5" className="text-center py-8 text-slate-500">No transactions found.</td>
                            </tr>
                        ) : (
                            filtered.map((tx, idx) => (
                                <tr key={tx?.transaction_id || idx} className="border-b border-slate-800/50 hover:bg-slate-800/50 transition-colors">
                                    <td className="py-4 px-4 font-mono text-slate-300">{(tx?.transaction_id || 'N/A').substring(0, 12)}...</td>
                                    <td className="py-4 px-4 text-white font-medium">${(tx?.amount || 0).toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                                    <td className="py-4 px-4">
                                        <span className={`px-2.5 py-1 rounded-full text-xs font-semibold ${(tx?.fraud_probability || 0) > 0.35 ? 'text-red-400 bg-red-400/10' : 'text-emerald-400 bg-emerald-400/10'}`}>
                                            {((tx?.fraud_probability || 0) * 100).toFixed(1)}%
                                        </span>
                                    </td>
                                    <td className="py-4 px-4">
                                        <span className={`px-2.5 py-1 rounded-full text-xs font-medium border ${getStatusColor(tx?.status)}`}>
                                            {tx?.status || 'APPROVED'}
                                        </span>
                                    </td>
                                    <td className="py-4 px-4 text-slate-400">
                                        {tx?.created_at ? new Date(tx.created_at).toLocaleString() : 'N/A'}
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
}
