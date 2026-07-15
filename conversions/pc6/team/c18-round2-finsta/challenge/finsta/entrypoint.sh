#!/bin/bash
set -e

# Start sshd in the background so the grader can SFTP socialmedia.db
/usr/sbin/sshd

# Run the Flask app on port 80 (as root, since binding <1024 requires it)
cd /home/user/app
exec gunicorn --workers 2 --bind 0.0.0.0:80 app:app
