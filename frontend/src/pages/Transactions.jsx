import React, { useState } from 'react';
import TransactionForm from '../components/TransactionForm';
import TransactionTable from '../components/TransactionTable';

export default function Transactions() {
    // Local refresh triggers if components need to force a re-render explicitly, 
    // although react query invalidation will handle most of the DOM updates.
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const handleRefresh = () => setRefreshTrigger(prev => prev + 1);

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-8">
            <h2 className="text-xl font-semibold text-slate-200">Transaction Control Center</h2>
            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8 items-start">
                <div className="xl:col-span-1">
                    <TransactionForm onTransactionSubmitted={handleRefresh} />
                </div>
                <div className="xl:col-span-2">
                    <TransactionTable refreshTrigger={refreshTrigger} />
                </div>
            </div>
        </div>
    );
}
