import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import TransactionForm from '../TransactionForm';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

const queryClient = new QueryClient();

describe('TransactionForm Component', () => {
    it('renders the core input fields', () => {
        render(
            <QueryClientProvider client={queryClient}>
                <TransactionForm />
            </QueryClientProvider>
        );
        expect(screen.getByText('Amount ($)')).toBeInTheDocument();
        expect(screen.getByText('Hour of Day (0-23)')).toBeInTheDocument();
        expect(screen.getByText('Process Transaction')).toBeInTheDocument();
    });
});
