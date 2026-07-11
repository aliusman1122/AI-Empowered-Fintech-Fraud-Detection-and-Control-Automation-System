import { LayoutDashboard, Receipt, ShieldAlert, Settings, LogOut } from 'lucide-react';

export default function Sidebar() {
  return (
    <div className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col h-screen text-slate-300">
      <div className="p-6 flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
          <ShieldAlert size={20} className="text-white" />
        </div>
        <span className="text-xl font-bold text-white tracking-wide">FinGuard</span>
      </div>
      
      <nav className="flex-1 px-4 space-y-2 mt-4">
        <a href="#" className="flex items-center gap-3 px-4 py-3 rounded-lg bg-indigo-600/10 text-indigo-400 font-medium">
          <LayoutDashboard size={20} />
          Dashboard
        </a>
        <a href="#" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors">
          <Receipt size={20} />
          Transactions
        </a>
        <a href="#" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors">
          <Settings size={20} />
          Settings
        </a>
      </nav>

      <div className="p-4 border-t border-slate-800">
        <button className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors w-full text-left text-slate-400 hover:text-white">
          <LogOut size={20} />
          Sign Out
        </button>
      </div>
    </div>
  );
}
