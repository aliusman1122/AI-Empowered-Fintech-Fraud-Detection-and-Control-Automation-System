import React, { createContext, useContext, useState, useEffect } from 'react';
import { loginUser } from '../services/api';
import toast from 'react-hot-toast';

const AuthContext = createContext(null);

export const AuthProvider = ({ children }) => {
    const [user, setUser] = useState(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const storedToken = localStorage.getItem('finguard_token');
        const storedUser = localStorage.getItem('finguard_user');
        if (storedToken && storedUser) {
            setUser(JSON.parse(storedUser));
        }
        setLoading(false);
    }, []);

    const login = async (credentials) => {
        try {
            const data = await loginUser(credentials);
            if (data.access_token) {
                localStorage.setItem('finguard_token', data.access_token);
                // The backend auth/login endpoint might not return user details directly,
                // but for now, we'll store a mock active user or if data returns it.
                const activeUser = { email: credentials.username, role: 'analyst' };
                localStorage.setItem('finguard_user', JSON.stringify(activeUser));
                setUser(activeUser);
                toast.success('Logged in successfully!');
                return true;
            }
        } catch (error) {
            const detail = error.response?.data?.detail;
            const errMsg = typeof detail === 'string' ? detail : detail?.[0]?.msg || 'Login failed. Please check your credentials.';
            toast.error(errMsg);
            return false;
        }
    };

    const logout = () => {
        localStorage.removeItem('finguard_token');
        localStorage.removeItem('finguard_user');
        setUser(null);
    };

    return (
        <AuthContext.Provider value={{ user, login, logout, loading }}>
            {!loading && children}
        </AuthContext.Provider>
    );
};

export const useAuth = () => useContext(AuthContext);
