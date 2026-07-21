import { useEffect } from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useQueryClient } from '@tanstack/react-query';
import { subscribeToTransactions } from './services/api';
import { showInfo } from './lib/toast';

// Layout & Guards
import ErrorBoundary from './components/ErrorBoundary';
import Layout from './components/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import Dashboard from './pages/Dashboard';
import Transactions from './pages/Transactions';
import Settings from './pages/Settings';
import Login from './pages/Login';
import Register from './pages/Register';

function App() {
    const queryClient = useQueryClient();

    useEffect(() => {
        const eventSource = subscribeToTransactions((newTxn) => {
            queryClient.invalidateQueries({ queryKey: ['transactions'] });
            queryClient.invalidateQueries({ queryKey: ['stats'] });
            showInfo(`New transaction received: ${newTxn.transaction_id}`);
        });

        return () => {
            if (eventSource) eventSource.close();
        };
    }, [queryClient]);

    return (
        <ErrorBoundary>
            <Toaster position="top-right" />
            <Routes>
                {/* Public Auth Routes */}
                <Route path="/login" element={<Login />} />
                <Route path="/register" element={<Register />} />

                {/* Protected Application Layout */}
                <Route element={<ProtectedRoute />}>
                    <Route element={<Layout />}>
                        <Route path="/" element={<Navigate to="/dashboard" replace />} />
                        <Route path="/dashboard" element={<Dashboard />} />
                        <Route path="/transactions" element={<Transactions />} />
                        <Route path="/settings" element={<Settings />} />
                    </Route>
                </Route>

                <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
        </ErrorBoundary>
    );
}

export default App;
