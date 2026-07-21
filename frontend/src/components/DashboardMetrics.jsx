import { useTransactions } from '../hooks/useTransactions';
import { useStats as useStatsHook } from '../hooks/useStats';
import { Activity, ShieldAlert, CheckCircle, Clock } from 'lucide-react';
import FraudTrendChart from './FraudTrendChart';
import ModelPerformanceChart from './ModelPerformanceChart';

export default function DashboardMetrics() {
    const { data: statsData } = useStatsHook();
    const { data: txDataList } = useTransactions(100);

    const safeTxData = Array.isArray(txDataList) ? txDataList : [];
    // Local fallbacks use lowercase DB status values
    const fraudCount = safeTxData.filter(tx => tx?.status === 'rejected' || tx?.status === 'blocked').length;
    const autoApprovedCount = safeTxData.filter(tx => tx?.status === 'auto_approved').length;
    const pendingCount = safeTxData.filter(tx => tx?.status === 'pending').length;
    const totalTxCount = safeTxData.length;

    const cards = [
        {
            title: 'Total Transactions',
            value: statsData?.total_transactions ?? totalTxCount,
            icon: <Activity className="text-blue-400" size={24} />,
            bg: 'bg-blue-500/10'
        },
        {
            title: 'Fraud Alerts',
            value: statsData?.fraud_alert_count ?? fraudCount,
            icon: <ShieldAlert className="text-red-400" size={24} />,
            bg: 'bg-red-500/10'
        },
        {
            title: 'Auto-Approved',
            value: statsData?.auto_approved_count ?? autoApprovedCount,
            icon: <CheckCircle className="text-emerald-400" size={24} />,
            bg: 'bg-emerald-500/10'
        },
        {
            title: 'Pending Verifications',
            value: statsData?.pending_count ?? pendingCount,
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

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="card border-slate-700/50">
                    <h3 className="text-lg font-medium text-white mb-6">Transaction Activity</h3>
                    <div className="h-72 w-full">
                        <FraudTrendChart txData={safeTxData} />
                    </div>
                </div>

                <div className="card border-slate-700/50">
                    <h3 className="text-lg font-medium text-white mb-6">Risk Score Distribution</h3>
                    <div className="h-72 w-full">
                        <ModelPerformanceChart txData={safeTxData} />
                    </div>
                </div>
            </div>
        </div>
    );
}
