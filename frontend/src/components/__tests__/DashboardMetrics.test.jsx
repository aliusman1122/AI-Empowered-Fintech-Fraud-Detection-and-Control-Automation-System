import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import DashboardMetrics from '../DashboardMetrics';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

// ResizeObserver mock needed for Recharts ResponsiveContainer
global.ResizeObserver = class ResizeObserver {
    observe() { }
    unobserve() { }
    disconnect() { }
};

describe('DashboardMetrics Component', () => {
    it('renders the generic layout metrics cards', () => {
        render(
            <QueryClientProvider client={queryClient}>
                <DashboardMetrics />
            </QueryClientProvider>
        );
        expect(screen.getByText('Total Transactions')).toBeInTheDocument();
        expect(screen.getByText('Fraud Alerts')).toBeInTheDocument();
        expect(screen.getByText('Auto-Approved')).toBeInTheDocument();
        expect(screen.getByText('Pending Verifications')).toBeInTheDocument();
    });
});
