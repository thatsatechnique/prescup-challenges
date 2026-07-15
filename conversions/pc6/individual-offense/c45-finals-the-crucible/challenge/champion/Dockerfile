FROM debian:bookworm-slim

RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-server \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /run/sshd \
    && ssh-keygen -A

# Competitor-facing account; login via publickey only, using the ORIGINAL (uncorrupted) key
RUN useradd --create-home --shell /bin/bash user
COPY original/id_rsa.pub /home/user/.ssh/authorized_keys
RUN chown -R user:user /home/user/.ssh \
    && chmod 700 /home/user/.ssh \
    && chmod 600 /home/user/.ssh/authorized_keys \
    && sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config

EXPOSE 22

# Token arrives via env (tokenChampion); drop it in the home directory, then run sshd in the foreground.
CMD ["sh", "-c", "echo \"$tokenChampion\" > /home/user/token.txt && chown user:user /home/user/token.txt && chmod 600 /home/user/token.txt && exec /usr/sbin/sshd -D -e"]
