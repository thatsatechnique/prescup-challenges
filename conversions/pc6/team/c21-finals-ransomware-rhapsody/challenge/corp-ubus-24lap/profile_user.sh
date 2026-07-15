# === w4Nt3D banner on login ===
cat /etc/banner_user 2>/dev/null
 
# === Skull PS1 in red ===
# 💀 user@host:/path$  (all red text)
export PS1='\[\033[1;31m\]💀 \u@\h:\w\$ \[\033[0m\]'
