import toast from 'react-hot-toast';

export const showSuccess = (message) => toast.success(message, {
    style: {
        background: '#10b981',
        color: '#fff',
    },
});

export const showError = (message) => toast.error(message, {
    style: {
        background: '#ef4444',
        color: '#fff',
    },
});

export const showInfo = (message) => toast(message, {
    icon: 'ℹ️',
    style: {
        background: '#3b82f6',
        color: '#fff',
    },
});
