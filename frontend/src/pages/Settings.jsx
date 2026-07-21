import React from 'react';
import { useAuth } from '../context/AuthContext';

export default function Settings() {
    const { user } = useAuth();

    return (
        <div className="animate-in fade-in slide-in-from-bottom-4 duration-500 space-y-6">
            <h2 className="text-xl font-semibold text-slate-200">System Preferences</h2>

            <div className="card p-8 border-slate-700/50">
                <h3 className="text-lg font-medium text-white mb-4">Identity Details</h3>
                <div className="space-y-4 max-w-md">
                    <div>
                        <label className="block text-sm text-slate-400 mb-1">Authenticated Reference</label>
                        <input type="text" disabled className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-300 opacity-70" value={user?.email || 'N/A'} />
                    </div>
                    <div>
                        <label className="block text-sm text-slate-400 mb-1">Permission Tier</label>
                        <input type="text" disabled className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2 text-slate-300 opacity-70" value={user?.role || 'analyst'} />
                    </div>
                </div>
            </div>

            <div className="card p-8 border-slate-700/50">
                <h3 className="text-lg font-medium text-white mb-4">Data Stream Synchronization</h3>
                <p className="text-slate-400 text-sm">Dashboard metrics are currently receiving live Server-Sent-Events (SSE) updates via Tanstack queries directly mapped into PostgreSQL event triggers.</p>
            </div>
        </div>
    );
}
