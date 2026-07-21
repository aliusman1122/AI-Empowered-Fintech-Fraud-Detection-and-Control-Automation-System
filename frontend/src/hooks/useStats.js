import { useQuery } from '@tanstack/react-query';
import { api } from '../services/api';

export const useStats = () => {
    return useQuery({
        queryKey: ['stats'],
        queryFn: async () => {
            const { data } = await api.get('/stats');
            return data;
        },
        staleTime: 0,           // always consider data stale so it re-fetches on mount
        refetchInterval: 30_000, // auto-refresh every 30 seconds
    });
};
