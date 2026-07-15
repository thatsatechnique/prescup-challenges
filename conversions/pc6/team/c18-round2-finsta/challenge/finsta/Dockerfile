FROM python:3.11-slim

# openssh-server so the grader (challenge.pccc) can SFTP socialmedia.db from this host.
# Shared volumes are not available in the target infrastructure.
RUN apt-get update && \
    apt-get install -y --no-install-recommends openssh-server && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir -p /var/run/sshd

# SSH user consumed by scripts/runXSS.py.
ENV SSH_USER=user
ENV SSH_PASSWORD=L1k3AndSubscr1b3!?
RUN useradd -m -s /bin/bash ${SSH_USER} && \
    echo "${SSH_USER}:${SSH_PASSWORD}" | chpasswd

RUN pip install --no-cache-dir \
    flask \
    flask-jwt-extended \
    Flask-SQLAlchemy \
    bootstrap-flask \
    Flask-Login \
    Flask-WTF \
    gunicorn

# Mirror the VM layout so sftp.get("/home/user/app/instance/socialmedia.db", ...) keeps working.
WORKDIR /home/user/app
COPY ./app /home/user/app
RUN chown -R user:user /home/user/app

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

CMD ["/entrypoint.sh"]
