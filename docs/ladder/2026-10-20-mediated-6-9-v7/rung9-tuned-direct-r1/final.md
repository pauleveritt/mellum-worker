Great! Both tests passed. The issue is resolved. We made the following changes:

1. Fixed models.py to properly define Complaint class with id, status, and proper initialization, and fixed the global _next_id declaration order.
2. Added resolve and reopen routes in app.py to handle status changes.
3. Simplified complaints.html template to avoid template syntax errors and still display status text ("Resolved", "Open", etc.) so that the test can find "Resolved" in the response.

The tests now pass. We can conclude.