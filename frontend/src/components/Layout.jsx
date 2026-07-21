import React, { useState } from 'react';
import Sidebar from './Sidebar';
import { Outlet, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Menu, LogOut, Settings as SettingsIcon, AlertTriangle } from 'lucide-react';

export default function Layout() {
    const { user, logout } = useAuth();
    const navigate = useNavigate();

    // UI Layout states
    const [isMobileOpen, setIsMobileOpen] = useState(false);
    const [isProfileOpen, setIsProfileOpen] = useState(false);
    const [isLogoutModalOpen, setIsLogoutModalOpen] = useState(false);

    const executeSignOut = () => {
        setIsLogoutModalOpen(false);
        logout();
        navigate('/login');
    };

    return (
        <div className="flex h-screen bg-slate-900 border-none overflow-hidden transition-colors relative">
            <Sidebar
                isMobileOpen={isMobileOpen}
                setIsMobileOpen={setIsMobileOpen}
                requestLogout={() => setIsLogoutModalOpen(true)}
            />

            <div className="flex-1 overflow-y-auto w-full flex flex-col relative">
                <header className="sticky top-0 z-30 bg-slate-900/90 backdrop-blur-md border-b border-slate-800 w-full shrink-0">
                    <div className="px-4 md:px-8 py-4 flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <button
                                className="md:hidden text-slate-400 hover:text-white transition-colors"
                                onClick={() => setIsMobileOpen(true)}
                            >
                                <Menu size={24} />
                            </button>
                            <h1 className="text-xl md:text-2xl font-bold text-white tracking-tight">AI Fraud Engine</h1>
                        </div>
                        <div className="flex items-center gap-4 relative">
                            <span className="hidden md:block text-slate-400 text-sm font-medium">{user?.email}</span>
                            <button
                                onClick={() => setIsProfileOpen(!isProfileOpen)}
                                className="w-10 h-10 rounded-full bg-indigo-600/20 flex items-center justify-center text-indigo-400 font-semibold border border-indigo-500/20 hover:bg-indigo-600/30 transition-colors focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                            >
                                {user?.email ? user.email[0].toUpperCase() : 'A'}
                            </button>

                            {/* Dropdown Menu */}
                            {isProfileOpen && (
                                <>
                                    <div
                                        className="fixed inset-0 z-20"
                                        onClick={() => setIsProfileOpen(false)}
                                    />
                                    <div className="absolute right-0 top-12 mt-2 w-48 bg-slate-800 border border-slate-700/50 rounded-lg shadow-xl z-30 overflow-hidden transform origin-top-right transition-all">
                                        <button
                                            onClick={() => { setIsProfileOpen(false); navigate('/settings'); }}
                                            className="w-full flex items-center gap-3 px-4 py-3 text-sm text-slate-300 hover:bg-slate-700 hover:text-white transition-colors"
                                        >
                                            <SettingsIcon size={16} />
                                            Settings
                                        </button>
                                        <button
                                            onClick={() => { setIsProfileOpen(false); setIsLogoutModalOpen(true); }}
                                            className="w-full flex items-center gap-3 px-4 py-3 text-sm text-red-400 hover:bg-slate-700 hover:text-red-300 transition-colors border-t border-slate-700"
                                        >
                                            <LogOut size={16} />
                                            Sign Out
                                        </button>
                                    </div>
                                </>
                            )}
                        </div>
                    </div>
                </header>

                <main className="px-4 md:px-8 pb-8 pt-16 md:pt-20 max-w-7xl w-full mx-auto space-y-8 flex-1">
                    <Outlet />
                </main>
            </div>

            {/* Logout Confirmation Modal Overlay */}
            {isLogoutModalOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm transition-opacity">
                    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 w-full max-w-md shadow-2xl relative overflow-hidden transform scale-100 transition-transform">
                        <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-red-500 to-orange-500"></div>
                        <div className="flex items-center gap-3 mb-2">
                            <div className="w-10 h-10 rounded-full bg-red-500/20 text-red-400 flex items-center justify-center shrink-0">
                                <AlertTriangle size={20} />
                            </div>
                            <h2 className="text-xl font-bold text-white tracking-wide">Confirm Logout</h2>
                        </div>
                        <p className="text-slate-400 mb-8 ml-13">Are you sure you want to end your current FinGuard session? All unsaved queries will remain active in the background.</p>

                        <div className="flex gap-3 ml-13">
                            <button
                                onClick={() => setIsLogoutModalOpen(false)}
                                className="flex-1 py-2.5 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors font-medium border border-slate-700 hover:border-slate-600 focus:outline-none"
                            >
                                Cancel
                            </button>
                            <button
                                onClick={executeSignOut}
                                className="flex-1 py-2.5 px-4 bg-red-600 hover:bg-red-700 text-white shadow-lg shadow-red-600/20 rounded-lg transition-all font-medium focus:outline-none focus:ring-2 focus:ring-red-500"
                            >
                                Sign Out
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
