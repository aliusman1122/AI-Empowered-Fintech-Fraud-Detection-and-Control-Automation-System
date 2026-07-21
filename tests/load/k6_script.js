import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
    stages: [
        { duration: '30s', target: 50 },  // Ramp up to 50 users
        { duration: '1m', target: 100 },  // Stay at 100 users
        { duration: '30s', target: 0 },   // Ramp down
    ],
    thresholds: {
        http_req_duration: ['p(95)<500'], // 95% of requests must complete below 500ms
        http_req_failed: ['rate<0.01'],   // Error rate must be less than 1%
    },
};

const BASE_URL = __ENV.API_URL || 'http://localhost:8000';

export default function () {
    const userEmail = `k6_${__VU}_${__ITER}@example.com`;
    const password = 'K6Password123!';

    // Register
    const regRes = http.post(`${BASE_URL}/api/v1/auth/register`, JSON.stringify({
        email: userEmail,
        password: password
    }), { headers: { 'Content-Type': 'application/json' } });

    // Login
    const loginRes = http.post(`${BASE_URL}/api/v1/auth/login`, {
        username: userEmail,
        password: password
    });

    const token = loginRes.json('access_token');

    if (token) {
        const params = { headers: { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' } };

        // Create 10 transactions
        for (let i = 0; i < 10; i++) {
            const txRes = http.post(`${BASE_URL}/api/v1/transactions`, JSON.stringify({
                amount: Math.random() * 5000,
                transaction_hour: Math.floor(Math.random() * 24),
                device_risk_score: Math.random(),
                ip_risk_score: Math.random(),
                merchant_category: 'other',
                transaction_type: 'online',
                country: 'US'
            }), params);

            check(txRes, { 'tx status is 2xx': (r) => r.status >= 200 && r.status < 300 });
            sleep(1);
        }

        // View Stats
        http.get(`${BASE_URL}/api/v1/stats`, params);
        http.get(`${BASE_URL}/api/v1/transactions?skip=0&limit=20`, params);
    }
}
