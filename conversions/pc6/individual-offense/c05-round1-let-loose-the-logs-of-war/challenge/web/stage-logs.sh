#!/bin/bash
# Stage realistic log files so the warlog app has content to display.
# Called by entrypoint at startup. The original challenge ran on a full
# Ubuntu VM so the log viewer had real syslog/auth/kern entries; we
# replicate enough to make the UI look populated and authentic.

LOG=/var/log

cat > "${LOG}/syslog" <<'EOF'
Apr 13 02:17:01 dockerhost systemd[1]: Starting Docker Application Container Engine...
Apr 13 02:17:02 dockerhost dockerd[812]: time="2026-04-13T02:17:02Z" level=info msg="Starting up"
Apr 13 02:17:02 dockerhost dockerd[812]: time="2026-04-13T02:17:02Z" level=info msg="containerd successfully booted in 0.041s"
Apr 13 02:17:03 dockerhost dockerd[812]: time="2026-04-13T02:17:03Z" level=info msg="Loading containers: start."
Apr 13 02:17:04 dockerhost dockerd[812]: time="2026-04-13T02:17:04Z" level=info msg="Loading containers: done."
Apr 13 02:17:04 dockerhost dockerd[812]: time="2026-04-13T02:17:04Z" level=info msg="Daemon has completed initialization"
Apr 13 02:17:04 dockerhost dockerd[812]: time="2026-04-13T02:17:04Z" level=info msg="API listen on /var/run/docker.sock"
Apr 13 02:17:05 dockerhost systemd[1]: Started Docker Application Container Engine.
Apr 13 02:17:10 dockerhost dockerd[812]: time="2026-04-13T02:17:10Z" level=info msg="ignoring event" container=tomcat
Apr 13 02:17:15 dockerhost systemd[1]: Starting Apache HTTP Server...
Apr 13 02:17:16 dockerhost apachectl[918]: AH00558: apache2: Could not reliably determine the server's fully qualified domain name
Apr 13 02:17:17 dockerhost systemd[1]: Started Apache HTTP Server.
Apr 13 02:18:01 dockerhost CRON[1042]: (root) CMD (/usr/sbin/logrotate -f /etc/logrotate.conf)
Apr 13 02:18:03 dockerhost systemd[1]: logrotate.service: Deactivated successfully.
Apr 13 02:22:00 dockerhost CRON[1108]: (root) CMD (/usr/sbin/ntpdate pool.ntp.org > /dev/null 2>&1)
Apr 13 02:32:14 dockerhost dockerd[812]: time="2026-04-13T02:32:14Z" level=info msg="Container tomcat health check: passed"
Apr 13 02:47:01 dockerhost CRON[1205]: (root) CMD (/usr/sbin/logrotate -f /etc/logrotate.conf)
Apr 13 02:47:03 dockerhost systemd[1]: logrotate.service: Deactivated successfully.
Apr 13 03:02:00 dockerhost CRON[1308]: (root) CMD (/usr/sbin/ntpdate pool.ntp.org > /dev/null 2>&1)
Apr 13 03:17:01 dockerhost CRON[1400]: (root) CMD (/usr/sbin/logrotate -f /etc/logrotate.conf)
Apr 13 03:17:03 dockerhost systemd[1]: logrotate.service: Deactivated successfully.
EOF

cat > "${LOG}/auth.log" <<'EOF'
Apr 13 02:17:00 dockerhost sshd[800]: Server listening on 0.0.0.0 port 22.
Apr 13 02:17:00 dockerhost sshd[800]: Server listening on :: port 22.
Apr 13 02:19:12 dockerhost sshd[1055]: Accepted password for user from 10.5.5.5 port 41822 ssh2
Apr 13 02:19:12 dockerhost sshd[1055]: pam_unix(sshd:session): session opened for user user(uid=1000) by user(uid=0)
Apr 13 02:19:13 dockerhost systemd-logind[655]: New session 1 of user user.
Apr 13 02:32:00 dockerhost sudo:     user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/docker ps
Apr 13 02:32:01 dockerhost sudo: pam_unix(sudo:session): session opened for user root(uid=0) by user(uid=1000)
Apr 13 02:37:00 dockerhost sudo:     user : TTY=pts/0 ; PWD=/home/user ; USER=root ; COMMAND=/usr/bin/docker logs tomcat
Apr 13 02:47:00 dockerhost CRON[1200]: pam_unix(cron:session): session opened for user root(uid=0) by (uid=0)
Apr 13 02:47:01 dockerhost CRON[1200]: pam_unix(cron:session): session closed for user root
Apr 13 03:02:00 dockerhost CRON[1350]: pam_unix(cron:session): session opened for user root(uid=0) by (uid=0)
Apr 13 03:02:01 dockerhost CRON[1350]: pam_unix(cron:session): session closed for user root
EOF

cat > "${LOG}/kern.log" <<'EOF'
Apr 13 02:16:50 dockerhost kernel: [    0.000000] Linux version 6.1.0-18-amd64 (debian-kernel@lists.debian.org) (gcc-12 (Debian 12.2.0-14) 12.2.0, GNU ld (GNU Binutils for Debian) 2.40) #1 SMP PREEMPT_DYNAMIC Debian 6.1.76-1 (2024-02-01)
Apr 13 02:16:50 dockerhost kernel: [    0.000000] Command line: BOOT_IMAGE=/vmlinuz-6.1.0-18-amd64 root=/dev/sda1 ro quiet
Apr 13 02:16:55 dockerhost kernel: [    2.341052] EXT4-fs (sda1): mounted filesystem 8ad5a4e2-fa13-4baa-a40e-6cc2e5b3fa1c r/w with ordered data mode. Quota mode: none.
Apr 13 02:16:57 dockerhost kernel: [    4.052141] bridge: filtering via arp/ip/ip6tables is no longer available by default.
Apr 13 02:16:58 dockerhost kernel: [    4.100234] docker0: port 1(veth8a2f1e3) entered blocking state
Apr 13 02:16:58 dockerhost kernel: [    4.100240] docker0: port 1(veth8a2f1e3) entered forwarding state
Apr 13 02:16:58 dockerhost kernel: [    4.201315] eth0: renamed from vethb3c9a12
EOF

cat > "${LOG}/daemon.log" <<'EOF'
Apr 13 02:17:00 dockerhost systemd[1]: Starting containerd container runtime...
Apr 13 02:17:01 dockerhost containerd[750]: time="2026-04-13T02:17:01Z" level=info msg="starting containerd" revision=ae71819c4f5e
Apr 13 02:17:01 dockerhost containerd[750]: time="2026-04-13T02:17:01Z" level=info msg="serving..." address=/run/containerd/containerd.sock
Apr 13 02:17:02 dockerhost systemd[1]: Started containerd container runtime.
Apr 13 02:17:04 dockerhost dockerd[812]: time="2026-04-13T02:17:04Z" level=info msg="Default bridge (docker0) is assigned with an IP address 172.17.0.0/16."
Apr 13 02:17:04 dockerhost dockerd[812]: time="2026-04-13T02:17:04Z" level=info msg="Loading containers: start."
Apr 13 02:17:05 dockerhost dockerd[812]: time="2026-04-13T02:17:05Z" level=info msg="Loading containers: done."
EOF

chmod 0644 "${LOG}/syslog" "${LOG}/auth.log" "${LOG}/kern.log" "${LOG}/daemon.log"
