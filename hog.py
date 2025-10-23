#!/usr/bin/env python3

import os
import time
import platform
import subprocess
import threading
import atexit
import sys

def detect_distro():
    """Detects if the system is Debian-based or Arch-based"""
    try:
        with open("/etc/os-release") as f:
            data = f.read().lower()
            if "debian" in data or "ubuntu" in data:
                return "debian"
            elif "arch" in data:
                return "arch"
    except:
        pass
    return "unknown"

def clean_history():
    """Disables and clears bash history"""
    os.environ["HISTFILE"] = ""
    home = os.path.expanduser("~")
    hist = os.path.join(home, ".bash_history")
    if os.path.exists(hist):
        try:
            open(hist, "w").close()
        except:
            pass

def clean_cache():
    """Cleans common user-level cache and session files"""
    home = os.path.expanduser("~")
    targets = [
        os.path.join(home, ".cache"),
        os.path.join(home, ".wget-hsts"),
        os.path.join(home, ".local/share/recently-used.xbel"),
    ]
    for path in targets:
        if os.path.exists(path):
            try:
                if os.path.isfile(path):
                    open(path, "w").close()
                elif os.path.isdir(path):
                    subprocess.call(["rm", "-rf", path])
            except:
                pass

def clean_logs(distro):
    """Cleans system logs depending on distro"""
    if distro == "debian":
        subprocess.call(["truncate", "-s", "0", "/var/log/apt/history.log"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    elif distro == "arch":
        subprocess.call(["truncate", "-s", "0", "/var/log/pacman.log"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.call(["journalctl", "--vacuum-time=1s"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def loop_cleaner(distro, stop_event):
    """Looped cleaner that runs every 5 seconds"""
    while not stop_event.is_set():
        clean_history()
        clean_cache()
        clean_logs(distro)
        time.sleep(5)

def main():
    if len(sys.argv) < 2 or sys.argv[1] != "--start":
        print("Usage: sudo hog --start")
        sys.exit(1)

    if os.geteuid() != 0:
        print("Error: hog must be run with sudo.")
        sys.exit(1)

    distro = detect_distro()
    if distro == "unknown":
        print("Unsupported distro.")
        sys.exit(1)

    print("hog started, good luck.")

    stop_event = threading.Event()
    cleaner_thread = threading.Thread(target=loop_cleaner, args=(distro, stop_event))
    cleaner_thread.daemon = True
    cleaner_thread.start()

    # Ensure cleanup on exit
    def on_exit():
        stop_event.set()
        cleaner_thread.join(timeout=1)
        clean_history()
        clean_cache()
        clean_logs(distro)

    atexit.register(on_exit)

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()
