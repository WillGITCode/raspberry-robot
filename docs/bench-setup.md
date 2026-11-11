# Bench setup: Boss's one-time checklist

The repo holds no host, user or key. Agents and the bench tool reach the Pi through the SSH alias `rover-bench` in the desktop's `~/.ssh/config`.

## One-time steps

- [x] Update the Pi 4 bootloader for USB boot (done 2026-11-09 to 11: bootloader current).
- [x] Flash the USB SSD with Imager: Pi OS Lite 64-bit (trixie), the `rover` user with a key, NOPASSWD sudo, Wi-Fi. Root is `/dev/sda2`.
- [x] Add the `rover-bench` alias to `~/.ssh/config`.
- [ ] Ethernet on the stand (decision 7). Wi-Fi only for now; the provision script leaves the Wi-Fi profile alone, and a broken network needs you at the bench.
- [ ] Check the L298N inputs for pull-downs (what the motors do when a pin floats). The stop script drives every pin low rather than releasing it.
- [ ] Mount the C920 on the desktop facing the stand.
- [ ] Take a backup image of the SSD after the first good provision, and keep it on the desktop.

Motor power stays off until a motor slice says otherwise.

## Provisioning (agents run this)

From the repo root on the desktop, as one command each (a chained or piped `ssh rover-bench` call runs sandboxed and cannot resolve the host):

    pi/provision.sh

It installs `python3-gpiozero`, `python3-lgpio` and `git`, makes the venv at `~/rover/.venv` with `--system-site-packages`, turns on the hardware watchdog (`dtparam=watchdog=on`, `RuntimeWatchdogSec=15`), sets journald to persistent, creates the bare repo `~/rover.git` with the `post-receive` hook, and installs `rover.service` and `rover-stop`.

It is idempotent: every run ends with `changes: N`, and a rerun with nothing to do prints `changes: 0`. The watchdog change needs one reboot (`ssh rover-bench 'sudo systemctl reboot'`).

If the script cannot run itself in a sandbox, do its three steps by hand: create `~/rover.git` (`git init --bare`), `git push rover-bench HEAD:main`, then `ssh rover-bench 'git --git-dir=$HOME/rover.git show main:pi/provision.sh | bash -s -- --on-pi'`.

## Deploys

Every push to `rover-bench` runs `post-receive`: it checks out the pushed commit to `~/rover`, refreshes the unit and `rover-stop`, logs a `rover-deploy` JSON line to the journal, and restarts `rover.service` (which reports the commit through `ROVER_COMMIT`).
