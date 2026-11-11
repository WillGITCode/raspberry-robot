#!/bin/bash
# Idempotent Pi setup. Run from the desktop: pi/provision.sh   (pushes HEAD to rover-bench, then runs itself on the Pi)
# The Wi-Fi profile is not touched. Prints "changes: N"; a second run prints "changes: 0".
set -eu

if [ "${1:-}" != "--on-pi" ]; then
  # desktop side: make sure git and the bare repo exist, push HEAD as main, run this script from there
  ssh rover-bench 'command -v git >/dev/null || { sudo apt-get update -qq && sudo apt-get install -y -qq git; }; [ -d ~/rover.git ] || git init -q --bare ~/rover.git'
  git -C "$(dirname "$(readlink -f "$0")")" push rover-bench HEAD:main
  ssh rover-bench 'git --git-dir=$HOME/rover.git show main:pi/provision.sh | bash -s -- --on-pi'
  exit
fi

# Pi side: take pi/ from the pushed main so the files always match the repo
SRC=$(mktemp -d)
trap 'rm -rf "$SRC"' EXIT
git --git-dir="$HOME/rover.git" archive main pi | tar -x -C "$SRC"
SRC=$SRC/pi
APP=/home/rover/rover
CHANGES=0
changed() { CHANGES=$((CHANGES + 1)); echo "changed: $*"; }

# write a root-owned file only when its content differs
put() { # path mode content
  if [ "$(sudo cat "$1" 2>/dev/null || true)" != "$3" ]; then
    printf '%s\n' "$3" | sudo tee "$1" >/dev/null; sudo chmod "$2" "$1"; changed "$1"; return 0
  fi
  return 1
}

# apt packages
missing=""
for p in python3-gpiozero python3-lgpio git; do dpkg -s "$p" >/dev/null 2>&1 || missing="$missing $p"; done
if [ -n "$missing" ]; then
  sudo apt-get update -qq
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq $missing
  changed "apt:$missing"
fi

# hardware watchdog (needs a reboot to take effect) and persistent journald
if ! grep -q '^dtparam=watchdog=on' /boot/firmware/config.txt; then
  printf '\n[all]\ndtparam=watchdog=on\n' | sudo tee -a /boot/firmware/config.txt >/dev/null
  changed "dtparam=watchdog=on (reboot needed)"
fi
sudo mkdir -p /etc/systemd/system.conf.d /etc/systemd/journald.conf.d
put /etc/systemd/system.conf.d/watchdog.conf 644 $'[Manager]\nRuntimeWatchdogSec=15' && sudo systemctl daemon-reexec || true
if put /etc/systemd/journald.conf.d/persistent.conf 644 $'[Journal]\nStorage=persistent'; then
  sudo mkdir -p /var/log/journal; sudo systemctl restart systemd-journald
fi

# bare repo with the deploy hook
[ -d "$HOME/rover.git" ] || { git init -q --bare "$HOME/rover.git"; changed "~/rover.git"; }
if ! cmp -s "$SRC/post-receive" "$HOME/rover.git/hooks/post-receive"; then
  install -m 755 "$SRC/post-receive" "$HOME/rover.git/hooks/post-receive"; changed "post-receive hook"
fi

# checkout dir, venv with system packages (gpiozero, lgpio)
[ -d "$APP" ] || { mkdir -p "$APP"; changed "$APP"; }
[ -x "$APP/.venv/bin/python" ] || { python3 -m venv --system-site-packages "$APP/.venv"; changed "venv"; }

# unit and stop wrapper (the hook refreshes both from the checkout on each deploy)
if ! sudo cmp -s "$SRC/rover.service" /etc/systemd/system/rover.service; then
  sudo install -m 644 "$SRC/rover.service" /etc/systemd/system/rover.service; sudo systemctl daemon-reload; changed "rover.service"
fi
if [ ! -x "$APP/pi/rover-stop" ]; then
  mkdir -p "$APP/pi"; install -m 755 "$SRC/rover-stop" "$APP/pi/rover-stop"; changed "$APP/pi/rover-stop"
fi
if [ "$(readlink /usr/local/bin/rover-stop 2>/dev/null)" != "$APP/pi/rover-stop" ]; then
  sudo ln -sfn "$APP/pi/rover-stop" /usr/local/bin/rover-stop; changed "/usr/local/bin/rover-stop"
fi
sudo systemctl enable rover.service >/dev/null 2>&1 || true

echo "changes: $CHANGES"
