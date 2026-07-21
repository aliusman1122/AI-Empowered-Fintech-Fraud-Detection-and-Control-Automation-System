import React from 'react';
import DashboardMetrics from '../components/DashboardMetrics';

export default function Dashboard() {
    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500">
            <h2 className="text-xl font-semibold text-slate-200 mb-6">Engine Overview</h2>
            <DashboardMetrics />
        </div>
    );
}
