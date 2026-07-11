import { useState, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import DashboardMetrics from './components/DashboardMetrics';
import TransactionForm from './components/TransactionForm';
import TransactionTable from './components/TransactionTable';

function App() {
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const handleRefresh = () => setRefreshTrigger(prev => prev + 1);

    useEffect(() => {
        const intervalId = setInterval(() => {
            handleRefresh();
        }, 4000);
        return () => clearInterval(intervalId);
    }, []);

    return (
        <div className="flex min-h-screen bg-slate-900">
            <Sidebar />
            <div className="flex-1 overflow-auto">
                <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm sticky top-0 z-10">
                    <div className="px-8 py-4 flex items-center justify-between">
                        <h1 className="text-2xl font-bold text-white tracking-tight">AI Fraud Engine</h1>
                        <div className="flex items-center gap-4">
                            <div className="w-10 h-10 rounded-full bg-indigo-600/20 flex items-center justify-center text-indigo-400 font-semibold border border-indigo-500/20">
                                A
                            </div>
                        </div>
                    </div>
                </header>

                <main className="p-8 max-w-7xl mx-auto space-y-8">
                    <DashboardMetrics refreshTrigger={refreshTrigger} />

                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 items-start">
                        <div className="lg:col-span-1">
                            <TransactionForm onTransactionSubmitted={handleRefresh} />
                        </div>
                        <div className="lg:col-span-2">
                            <TransactionTable refreshTrigger={refreshTrigger} />
                        </div>
                    </div>
                </main>
            </div>
        </div>
    );
}

export default App;
