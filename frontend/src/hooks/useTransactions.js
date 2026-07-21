import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import { showSuccess, showError } from '../lib/toast';

export const useTransactions = (limit = 50) => {
    return useQuery({
        queryKey: ['transactions', limit],
        queryFn: async () => {
            const { data } = await api.get(`/transactions?limit=${limit}`);
            return data;
        },
        refetchInterval: (query) => {
            const data = query?.state?.data;
            const hasPending = Array.isArray(data) && data.some(
                (tx) => String(tx?.status || '').toLowerCase() === 'pending'
            );
            return hasPending ? 3000 : false;
        },
        refetchIntervalInBackground: true,
    });
};

export const useTransaction = (id) => {
    return useQuery({
        queryKey: ['transactions', id],
        queryFn: async () => {
            if (!id) return null;
            const { data } = await api.get(`/transactions/${id}`);
            return data;
        },
        enabled: !!id,
    });
};

export const useCreateTransaction = () => {
    const queryClient = useQueryClient();

    return useMutation({
        mutationFn: async (transactionData) => {
            const { data } = await api.post('/transactions', transactionData);
            return data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['transactions'] });
            queryClient.invalidateQueries({ queryKey: ['stats'] });

            if (data.fraud_flag) {
                showError(`High Fraud Risk Detected (${(data.fraud_probability * 100).toFixed(1)}%)! Verification email sent for human authorization.`);
            } else {
                showSuccess(`Transaction submitted successfully!`);
            }
        },
        onError: (error) => {
            showError('Failed to submit transaction.');
            console.error(error);
        }
    });
};
