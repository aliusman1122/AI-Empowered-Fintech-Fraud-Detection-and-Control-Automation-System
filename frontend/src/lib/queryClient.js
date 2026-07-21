import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 30 * 1000,       // Data gets stale after 30 seconds
            gcTime: 5 * 60 * 1000,      // Cache lives for 5 minutes
            retry: 2,                   // Retry failed queries twice
            refetchOnWindowFocus: false // Do not aggressively refetch on browser focus
        },
    },
});
