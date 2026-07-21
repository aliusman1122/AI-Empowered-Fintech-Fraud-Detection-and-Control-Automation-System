import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { ShieldCheck, Loader2, Eye, EyeOff } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';

export default function Login() {
    const { login } = useAuth();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [formData, setFormData] = useState({ username: '', password: '' });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        const success = await login(formData);
        if (success) {
            navigate('/dashboard');
        }
        setLoading(false);
    };

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4">
            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
                <div className="flex flex-col items-center mb-8">
                    <div className="w-12 h-12 bg-indigo-500/20 text-indigo-400 rounded-xl flex items-center justify-center mb-4">
                        <ShieldCheck size={28} />
                    </div>
                    <h2 className="text-2xl font-bold text-white tracking-wide">FinGuard Access</h2>
                    <p className="text-slate-400 text-sm mt-2">Secure AI Fraud Detection Engine</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-1">Email / Username</label>
                        <input
                            required
                            type="text"
                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                            placeholder="analyst@finguard.ai"
                            value={formData.username}
                            onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                        />
                    </div>
                    <div className="relative">
                        <label className="block text-sm font-medium text-slate-300 mb-1">Passphrase</label>
                        <input
                            required
                            type={showPassword ? "text" : "password"}
                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2.5 pr-10 text-white placeholder-slate-500 focus:outline-none focus:border-indigo-500 focus:ring-1 focus:ring-indigo-500 transition-colors"
                            placeholder="••••••••••••"
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-9 text-slate-400 hover:text-slate-300 transition-colors"
                        >
                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-medium py-2.5 rounded-lg flex justify-center items-center transition-colors mt-6 disabled:opacity-50"
                    >
                        {loading ? <Loader2 size={20} className="animate-spin" /> : 'Authenticate Context'}
                    </button>

                    <div className="text-center mt-6 pt-6 border-t border-slate-800">
                        <p className="text-slate-400 text-sm">
                            Don't have an access node? <Link to="/register" className="text-indigo-400 hover:text-indigo-300">Request Provisioning</Link>
                        </p>
                    </div>
                </form>
            </div>
        </div>
    );
}
