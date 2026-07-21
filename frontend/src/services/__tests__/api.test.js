import { describe, it, expect, vi } from 'vitest';
import { getSystemStats, getTransactions } from '../api';

vi.mock('axios', () => {
    return {
        default: {
            create: vi.fn(() => ({
                get: vi.fn((url) => {
                    if (url === '/stats') return Promise.resolve({ data: { total: 100 } });
                    if (url.includes('/transactions/')) return Promise.resolve({ data: [{ id: 1 }] });
                }),
                post: vi.fn(),
            }))
        }
    };
});

describe('API Services', () => {
    it('fetches system stats', async () => {
        const stats = await getSystemStats();
        expect(stats).toBeDefined();
    });

    it('fetches transactions', async () => {
        const txs = await getTransactions(10);
        expect(txs).toBeDefined();
    });
});
