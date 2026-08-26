import os
import sys
import platform


def format_bytes(b):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if b < 1024:
            return f"{b:.2f} {unit}"
        b /= 1024
    return f"{b:.2f} PB"


def is_root():
    return os.geteuid() == 0


def is_windows():
    return platform.system() == "Windows"


def get_rules_path():
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, "firewall_rules.json")
