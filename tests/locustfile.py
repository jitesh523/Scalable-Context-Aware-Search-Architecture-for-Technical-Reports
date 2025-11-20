"""
Locust load testing script.
"""

from locust import HttpUser, task, between
import random

class RAGUser(HttpUser):
    wait_time = between(1, 5)
    
    def on_start(self):
        """Login and get token."""
        # Placeholder for auth logic if needed for load test
        self.headers = {"Authorization": "Bearer test-token"}

    @task(3)
    def search(self):
        """Simulate search queries."""
        queries = [
            "How does the transformer architecture work?",
            "What are the safety protocols for engine maintenance?",
            "Explain the database schema design.",
            "List the API endpoints."
        ]
        
        self.client.post(
            "/search",
            json={"query": random.choice(queries)},
            headers=self.headers
        )

    @task(1)
    def health_check(self):
        """Check health endpoint."""
        self.client.get("/health")
