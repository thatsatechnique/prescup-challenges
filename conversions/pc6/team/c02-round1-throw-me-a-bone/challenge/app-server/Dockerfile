FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends openssh-server sudo nano vim-tiny procps && \
    rm -rf /var/lib/apt/lists/* && \
    mkdir /var/run/sshd

# Provide a minimal systemctl shim so 'sudo systemctl restart sshd.service' works
RUN printf '%s\n' \
    '#!/bin/bash' \
    'case "$1" in' \
    '    restart|reload|start)' \
    '        case "$2" in' \
    '            sshd*|ssh*)' \
    '                pkill -HUP -f /usr/sbin/sshd 2>/dev/null || true' \
    '                ;;' \
    '        esac' \
    '        ;;' \
    '    status)' \
    '        pgrep -x sshd >/dev/null && echo "Active: active (running)" || echo "Active: inactive (dead)"' \
    '        ;;' \
    'esac' \
    'exit 0' \
    > /usr/local/bin/systemctl && chmod +x /usr/local/bin/systemctl

# Create user account (password: tartans) with passwordless sudo
RUN useradd -m -s /bin/bash user && \
    echo 'user:tartans' | chpasswd && \
    usermod -aG sudo user && \
    echo 'user ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/user && \
    chmod 440 /etc/sudoers.d/user

# Create scanuser account (password: 2th3st@rs) with passwordless sudo
RUN useradd -m -s /bin/bash scanuser && \
    echo 'scanuser:2th3st@rs' | chpasswd && \
    usermod -aG sudo scanuser && \
    echo 'scanuser ALL=(ALL) NOPASSWD: ALL' > /etc/sudoers.d/scanuser && \
    chmod 440 /etc/sudoers.d/scanuser

# All inactive users already removed and archived
RUN mkdir -p /home/archived_users/lrobinson \
             /home/archived_users/eclark \
             /home/archived_users/awright \
             /home/archived_users/sscott \
             /home/archived_users/dgreen \
             /home/archived_users/hcarter

# VULNERABILITY: SSH allows root login
# Replace existing PermitRootLogin line in-place (visible in Authentication section);
# also remove any drop-in overrides; append if no line exists.
RUN sed -i -E 's|^[[:space:]]*#*[[:space:]]*PermitRootLogin[[:space:]].*|PermitRootLogin yes|' /etc/ssh/sshd_config && \
    grep -q '^PermitRootLogin yes' /etc/ssh/sshd_config || echo 'PermitRootLogin yes' >> /etc/ssh/sshd_config && \
    find /etc/ssh/sshd_config.d -type f -exec sed -i '/PermitRootLogin/d' {} \; 2>/dev/null || true

# VULNERABILITY: Incorrect /etc/shadow permissions
RUN chmod 644 /etc/passwd && \
    chmod 777 /etc/shadow

EXPOSE 22

CMD ["/usr/sbin/sshd", "-D"]
