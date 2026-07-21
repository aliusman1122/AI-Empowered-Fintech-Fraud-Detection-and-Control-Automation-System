import React, { useState } from 'react';
import { LayoutDashboard, Receipt, ShieldAlert, Settings, LogOut, PanelLeft, X } from 'lucide-react';
import { NavLink } from 'react-router-dom';

export default function Sidebar({ isMobileOpen, setIsMobileOpen, requestLogout }) {
    const [isCollapsed, setIsCollapsed] = useState(false);

    // Responsive classes
    const mobileClasses = isMobileOpen ? 'translate-x-0' : '-translate-x-full';
    const desktopClasses = `md:translate-x-0 transition-all duration-300 ease-in-out ${isCollapsed ? 'w-20' : 'w-64'}`;

    const getNavLinkClass = ({ isActive }) =>
        `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors overflow-hidden whitespace-nowrap ${isActive ? 'bg-indigo-600/10 text-indigo-400 font-medium' : 'text-slate-300 hover:bg-slate-800 hover:text-white'
        }`;

    return (
        <>
            {/* Mobile Overlay */}
            {isMobileOpen && (
                <div
                    className="fixed inset-0 bg-slate-950/80 z-40 md:hidden backdrop-blur-sm"
                    onClick={() => setIsMobileOpen(false)}
                />
            )}

            {/* Sidebar Container */}
            <div className={`fixed inset-y-0 left-0 z-50 md:relative bg-slate-900 border-r border-slate-800 flex flex-col h-screen transform ${mobileClasses} ${desktopClasses}`}>

                {/* Header Section */}
                <div className="p-4 flex items-center justify-between shrink-0">
                    <div className="flex items-center gap-3 overflow-hidden whitespace-nowrap">
                        <div className="w-10 h-10 shrink-0 rounded-lg bg-indigo-600 flex items-center justify-center">
                            <ShieldAlert size={22} className="text-white" />
                        </div>
                        {!isCollapsed && <span className="text-xl font-bold text-white tracking-wide transition-opacity duration-300">FinGuard</span>}
                    </div>

                    {/* Mobile Close Button */}
                    <button
                        onClick={() => setIsMobileOpen(false)}
                        className="md:hidden text-slate-400 hover:text-white p-1"
                    >
                        <X size={24} />
                    </button>

                    {/* Desktop Collapse Toggle */}
                    <button
                        onClick={() => setIsCollapsed(!isCollapsed)}
                        className="hidden md:block text-slate-400 hover:text-white p-2 rounded-lg hover:bg-slate-800 transition-colors"
                    >
                        <PanelLeft size={20} />
                    </button>
                </div>

                {/* Navigation Menu */}
                <nav className="flex-1 px-3 space-y-2 mt-6 overflow-y-auto overflow-x-hidden">
                    <NavLink to="/dashboard" onClick={() => setIsMobileOpen(false)} className={getNavLinkClass}>
                        <div className="shrink-0"><LayoutDashboard size={22} /></div>
                        {!isCollapsed && <span className="transition-opacity duration-300">Dashboard</span>}
                    </NavLink>
                    <NavLink to="/transactions" onClick={() => setIsMobileOpen(false)} className={getNavLinkClass}>
                        <div className="shrink-0"><Receipt size={22} /></div>
                        {!isCollapsed && <span className="transition-opacity duration-300">Transactions</span>}
                    </NavLink>
                    <NavLink to="/settings" onClick={() => setIsMobileOpen(false)} className={getNavLinkClass}>
                        <div className="shrink-0"><Settings size={22} /></div>
                        {!isCollapsed && <span className="transition-opacity duration-300">Settings</span>}
                    </NavLink>
                </nav>

                {/* Bottom Action Footer */}
                <div className="p-3 border-t border-slate-800">
                    <button
                        onClick={requestLogout}
                        className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors w-full text-left text-slate-400 hover:text-red-400 hover:bg-red-500/10 overflow-hidden whitespace-nowrap"
                    >
                        <div className="shrink-0"><LogOut size={22} /></div>
                        {!isCollapsed && <span className="transition-opacity duration-300">Sign Out</span>}
                    </button>
                </div>

            </div>
        </>
    );
}
