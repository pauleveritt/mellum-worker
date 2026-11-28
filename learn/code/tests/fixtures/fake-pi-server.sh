#!/bin/sh
# A stand-in Pi that starts a long-lived "server" in a session of its own, as Pi's bash tool does,
# then keeps working, so the harness can be stopped mid-session.
python3 -c "import subprocess; subprocess.Popen(['sleep', '307'], start_new_session=True)"
echo started > server.txt
sleep 300
