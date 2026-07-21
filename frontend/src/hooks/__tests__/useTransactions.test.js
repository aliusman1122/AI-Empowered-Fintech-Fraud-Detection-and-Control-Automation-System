import { renderHook, waitFor } from '@testing-library/react';
import { useStats } from '../useStats';
import { useTransactions } from '../useTransactions';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { describe, it, expect } from 'vitest';

const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } }
});

const wrapper = ({ children }) => (
    <QueryClientProvider client={queryClient}>
        {children}
    </QueryClientProvider>
);

describe('Query Hooks', () => {
    it('useStats initializes', () => {
        const { result } = renderHook(() => useStats(), { wrapper });
        expect(result.current.isLoading).toBe(true);
    });

    it('useTransactions initializes', () => {
        const { result } = renderHook(() => useTransactions(10), { wrapper });
        expect(result.current.isLoading).toBe(true);
    });
});
