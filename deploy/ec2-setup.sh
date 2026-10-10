#!/usr/bin/env bash
# One-time server prep for Ubuntu 22.04/24.04 on EC2.  Run:  sudo bash ec2-setup.sh
set -euo pipefail

# 2 GB swap so the React build doesn't run out of memory on small instances
if ! swapon --show | grep -q swapfile; then
  fallocate -l 2G /swapfile && chmod 600 /swapfile && mkswap /swapfile && swapon /swapfile
  echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Docker Engine + Compose plugin
apt-get update -y
apt-get install -y ca-certificates curl git
curl -fsSL https://get.docker.com | sh
usermod -aG docker "${SUDO_USER:-ubuntu}"

# Docker log rotation
mkdir -p /etc/docker
cat > /etc/docker/daemon.json <<'JSON'
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
JSON
systemctl restart docker
echo "Done. Log out and back in, then continue with the guide."
