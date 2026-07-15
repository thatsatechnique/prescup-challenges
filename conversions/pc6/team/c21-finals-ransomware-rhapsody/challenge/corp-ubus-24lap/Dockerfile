# =============================================================================
# corp-ubus-24lap — Victim machine for Ransomware Rhapsody (C21)
#
# Uses FULL ubuntu:22.04 (not minimal/slim) because competitors SSH into this
# machine and need a realistic Ubuntu desktop-like environment with standard
# system utilities (find, ls, cat, strings, vim, nano, file, etc.).
#
# The original pc6 challenge ran on a full Ubuntu 22.04 VM — this Dockerfile
# replicates that environment as closely as possible in a container.
# =============================================================================

FROM ubuntu:22.04

# Prevent interactive prompts during package install
ENV DEBIAN_FRONTEND=noninteractive \
    LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

# -----------------------------------------------------------------------------
# Install packages that match the original VM environment
# NOTE: We install the FULL set of utilities competitors might need/expect
# on a real Ubuntu workstation. This is intentional — do NOT slim down.
# -----------------------------------------------------------------------------
RUN apt-get update && apt-get install -y \
    openssh-server \
    sudo \
    python3 \
    python3-pip \
    zip \
    unzip \
    pv \
    procps \
    vim \
    nano \
    less \
    file \
    net-tools \
    iproute2 \
    iputils-ping \
    dnsutils \
    ca-certificates \
    tzdata \
    bash \
    coreutils \
    findutils \
    grep \
    gawk \
    sed \
    curl \
    wget \
    binutils \
    xxd \
    man-db \
    locales \
    passwd \
    login \
    && rm -rf /var/lib/apt/lists/*

# Python cryptography library (needed for the decryptor tool on the victim)
RUN pip3 install --no-cache-dir cryptography==42.0.8 pexpect

# -----------------------------------------------------------------------------
# Create the player user — matches original VM credentials
# The 'user' account has a restricted sudo (NO root escalation by design).
# deployer and root are NOT in scope per challenge rules.
# -----------------------------------------------------------------------------
RUN mkdir -p /var/run/sshd && \
    useradd -m -s /bin/bash user && \
    echo 'user:tartans' | chpasswd

# SSH hardening: disable root login, enable password auth for user
RUN sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config && \
    sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication yes/' /etc/ssh/sshd_config

# -----------------------------------------------------------------------------
# Per-user SSH banners & custom PS1 prompts
# banner_user  = shown when 'user' logs in (pre-auth SSH Banner + post-login MOTD)
# banner_us    = shown when 'ubuntu_service' logs in (post-login only, set in entrypoint)
# -----------------------------------------------------------------------------
COPY banner_user.txt /etc/ssh/banner.txt
COPY banner_us.txt   /etc/banner_us

# Pre-auth banner (everyone sees this before password prompt)
RUN echo 'Banner /etc/ssh/banner.txt' >> /etc/ssh/sshd_config

# Disable Ubuntu's default dynamic MOTD noise
RUN chmod -x /etc/update-motd.d/* 2>/dev/null || true && \
    rm -f /etc/motd

# --- Per-user profile scripts (banner + PS1) ---
COPY profile_user.sh            /etc/profile_user.sh
COPY profile_ubuntu_service.sh  /etc/profile_ubuntu_service.sh

# Append to user's .bashrc (user exists at build time)
RUN cat /etc/profile_user.sh >> /home/user/.bashrc

# -----------------------------------------------------------------------------
# Copy challenge initialization scripts and plaintext seed files
# -----------------------------------------------------------------------------
RUN mkdir -p /opt/challenge

COPY entrypoint.sh            /entrypoint.sh
COPY init_challenge.py        /opt/challenge/init_challenge.py
COPY decrypt0r_v2.py          /opt/challenge/decrypt0r_v2.py
COPY encrypted_files/          /opt/challenge/plaintexts/

# Fix any Windows CRLF line endings (belt-and-suspenders for cross-platform dev)
RUN sed -i 's/\r$//' /entrypoint.sh /opt/challenge/init_challenge.py /opt/challenge/decrypt0r_v2.py

RUN chmod 0755 /entrypoint.sh /opt/challenge/init_challenge.py /opt/challenge/decrypt0r_v2.py && \
    chown -R root:root /opt/challenge

EXPOSE 22

ENTRYPOINT ["/entrypoint.sh"]
