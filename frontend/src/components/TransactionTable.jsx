import { useState, useEffect } from 'react';
import { useTransactions } from '../hooks/useTransactions';
import { Search, ArrowUpDown, Download } from 'lucide-react';
import Skeleton from 'react-loading-skeleton';
import 'react-loading-skeleton/dist/skeleton.css';

export default function TransactionTable({ refreshTrigger }) {
    const { data: transactions, isLoading, refetch } = useTransactions(100);
    const [search, setSearch] = useState('');
    const [sortConfig, setSortConfig] = useState({ key: 'created_at', direction: 'desc' });

    // Explicit reactivity forcing real-time table syncing bypassing idle interval locks
    useEffect(() => {
        if (refreshTrigger) {
            refetch();
        }
    }, [refreshTrigger, refetch]);

    const handleSort = (key) => {
        let direction = 'asc';
        if (sortConfig.key === key && sortConfig.direction === 'asc') {
            direction = 'desc';
        }
        setSortConfig({ key, direction });
    };

    const safeData = Array.isArray(transactions) ? transactions : [];

    const sortedData = [...safeData].sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) return sortConfig.direction === 'asc' ? -1 : 1;
        if (a[sortConfig.key] > b[sortConfig.key]) return sortConfig.direction === 'asc' ? 1 : -1;
        return 0;
    });

    const filtered = sortedData.filter(tx =>
        (tx?.transaction_id || '').toLowerCase().includes(search.toLowerCase()) ||
        (tx?.status || '').toLowerCase().includes(search.toLowerCase())
    );

    const handleExport = () => {
        const headers = ["Transaction ID", "Amount", "Risk Score", "Status", "Time"];
        const csvContent = [
            headers.join(","),
            ...filtered.map(tx => [
                tx?.transaction_id,
                tx?.amount,
                tx?.fraud_probability,
                tx?.status,
                tx?.created_at
            ].join(","))
        ].join("\n");

        const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.setAttribute("download", "transactions_export.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

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
                <div className="flex gap-4">
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
                    <button
                        onClick={handleExport}
                        className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg border border-slate-700 transition"
                    >
                        <Download size={16} /> Export CSV
                    </button>
                </div>
            </div>

            <div className="overflow-x-auto">
                <table className="w-full table-auto text-left border-collapse">
                    <thead>
                        <tr className="border-b border-slate-700 text-slate-400 text-sm uppercase tracking-wider">
                            <th className="pb-3 px-4 font-medium cursor-pointer hover:text-white" onClick={() => handleSort('transaction_id')}>
                                <div className="flex items-center gap-1">Transaction ID <ArrowUpDown size={14} /></div>
                            </th>
                            <th className="pb-3 px-4 font-medium cursor-pointer hover:text-white" onClick={() => handleSort('amount')}>
                                <div className="flex items-center gap-1">Amount <ArrowUpDown size={14} /></div>
                            </th>
                            <th className="pb-3 px-4 font-medium cursor-pointer hover:text-white" onClick={() => handleSort('fraud_probability')}>
                                <div className="flex items-center gap-1">Risk Score <ArrowUpDown size={14} /></div>
                            </th>
                            <th className="pb-3 px-4 font-medium cursor-pointer hover:text-white" onClick={() => handleSort('status')}>
                                <div className="flex items-center gap-1">Status <ArrowUpDown size={14} /></div>
                            </th>
                            <th className="pb-3 px-4 font-medium cursor-pointer hover:text-white" onClick={() => handleSort('created_at')}>
                                <div className="flex items-center gap-1">Time <ArrowUpDown size={14} /></div>
                            </th>
                        </tr>
                    </thead>
                    <tbody className="text-sm">
                        {isLoading ? (
                            Array.from({ length: 5 }).map((_, idx) => (
                                <tr key={idx}>
                                    <td className="py-4 px-4"><Skeleton baseColor="#1e293b" highlightColor="#334155" /></td>
                                    <td className="py-4 px-4"><Skeleton baseColor="#1e293b" highlightColor="#334155" /></td>
                                    <td className="py-4 px-4"><Skeleton baseColor="#1e293b" highlightColor="#334155" /></td>
                                    <td className="py-4 px-4"><Skeleton baseColor="#1e293b" highlightColor="#334155" /></td>
                                    <td className="py-4 px-4"><Skeleton baseColor="#1e293b" highlightColor="#334155" /></td>
                                </tr>
                            ))
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
