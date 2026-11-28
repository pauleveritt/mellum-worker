Great! Both tests now pass. We have fixed the issues:

1. Added id and status fields to Complaint class with auto-increment id and default status "open".
2. Added resolve and reopen routes in app.py that update complaint status to "resolved" (lowercase) and "open" respectively.
3. Modified the complaints.html template to display "Resolved" when status is "resolved" (using conditional), so that the test checking for "Resolved" in text passes.
4. Ensured that the status attribute is set to "resolved" lowercase to pass the model assertion.

The tests pass now. We can conclude.