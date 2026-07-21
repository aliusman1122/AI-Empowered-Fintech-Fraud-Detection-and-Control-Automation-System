from locust import HttpUser, task, between

class FraudSystemUser(HttpUser):
    wait_time = between(1, 3)

    def on_start(self):
        # Register a unique user for each simulated client
        import uuid
        self.username = f"loadtest_{uuid.uuid4().hex[:8]}@example.com"
        self.password = "LoadTest123!"
        
        self.client.post("/api/v1/auth/register", json={
            "email": self.username,
            "password": self.password
        })
        
        # Login and store token
        response = self.client.post("/api/v1/auth/login", data={
            "username": self.username,
            "password": self.password
        })
        if response.status_code == 200:
            self.token = response.json().get("access_token")
            self.client.headers.update({"Authorization": f"Bearer {self.token}"})

    @task(10)
    def create_transaction(self):
        import random
        self.client.post("/api/v1/transactions", json={
            "amount": round(random.uniform(10.0, 5000.0), 2),
            "transaction_hour": random.randint(0, 23),
            "device_risk_score": random.uniform(0, 1),
            "ip_risk_score": random.uniform(0, 1),
            "merchant_category": random.choice(["food", "electronics", "crypto", "travel", "other"]),
            "transaction_type": random.choice(["online", "in_person"]),
            "country": random.choice(["US", "UK", "CA", "AU", "RU"])
        })

    @task(2)
    def view_dashboard_stats(self):
        self.client.get("/api/v1/stats")
        self.client.get("/api/v1/transactions?skip=0&limit=20")
