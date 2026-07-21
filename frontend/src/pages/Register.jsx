import React, { useState } from 'react';
import { ShieldCheck, Loader2, Eye, EyeOff } from 'lucide-react';
import { Link, useNavigate } from 'react-router-dom';
import { registerUser } from '../services/api';
import toast from 'react-hot-toast';

export default function Register() {
    const navigate = useNavigate();
    const [loading, setLoading] = useState(false);
    const [showPassword, setShowPassword] = useState(false);
    const [formData, setFormData] = useState({ full_name: '', email: '', password: '' });

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        try {
            await registerUser(formData);
            toast.success('Provisioning complete! You may now authenticate.');
            navigate('/dashboard');
        } catch (error) {
            const detail = error.response?.data?.detail;
            const errMsg = typeof detail === 'string' ? detail : detail?.[0]?.msg || 'Registration failed.';
            toast.error(errMsg);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4">
            <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl shadow-2xl p-8">
                <div className="flex flex-col items-center mb-8">
                    <div className="w-12 h-12 bg-emerald-500/20 text-emerald-400 rounded-xl flex items-center justify-center mb-4">
                        <ShieldCheck size={28} />
                    </div>
                    <h2 className="text-2xl font-bold text-white tracking-wide">Analyst Registration</h2>
                    <p className="text-slate-400 text-sm mt-2">FinGuard Access Provisioning</p>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-1">Full Name</label>
                        <input
                            required
                            type="text"
                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                            placeholder="Satoshi Nakamoto"
                            value={formData.full_name}
                            onChange={(e) => setFormData({ ...formData, full_name: e.target.value })}
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-slate-300 mb-1">Email Reference</label>
                        <input
                            required
                            type="email"
                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                            placeholder="analyst@finguard.ai"
                            value={formData.email}
                            onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                        />
                    </div>
                    <div className="relative">
                        <label className="block text-sm font-medium text-slate-300 mb-1">Passphrase</label>
                        <input
                            required
                            type={showPassword ? "text" : "password"}
                            className="w-full bg-slate-950 border border-slate-800 rounded-lg px-4 py-2 pr-10 text-white placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-colors"
                            placeholder="Must contain 12+ characters, special symbols..."
                            value={formData.password}
                            onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-8 text-slate-400 hover:text-slate-300 transition-colors"
                        >
                            {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                        </button>
                    </div>

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-medium py-2.5 rounded-lg flex justify-center items-center transition-colors mt-6 disabled:opacity-50"
                    >
                        {loading ? <Loader2 size={20} className="animate-spin" /> : 'Provision Identity'}
                    </button>

                    <div className="text-center mt-6 pt-6 border-t border-slate-800">
                        <p className="text-slate-400 text-sm">
                            Already provisioned? <Link to="/login" className="text-emerald-400 hover:text-emerald-300">Authenticate context</Link>
                        </p>
                    </div>
                </form>
            </div>
        </div>
    );
}
