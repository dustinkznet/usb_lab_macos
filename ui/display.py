"""
Display utilities for USB LAB terminal interface.
"""

import os
from .colors import Color

def print_header():
    """Display compact header with small mascot."""
    print(f"""
  {Color.BRIGHT_CYAN} ▄▀▀▀▄   {Color.BRIGHT_MAGENTA}┃ {Color.BOLD}{Color.BRIGHT_WHITE}USB LAB {Color.RESET}{Color.BRIGHT_YELLOW}v0.3.0
  {Color.BRIGHT_CYAN}▐ {Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN} {Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN} ▌  {Color.BRIGHT_MAGENTA}┃ {Color.WHITE}Drive Analysis · Testing · Benchmarking
  {Color.BRIGHT_CYAN} ▀▄{Color.BRIGHT_WHITE}▼{Color.BRIGHT_CYAN}▄▀   {Color.BRIGHT_MAGENTA}┃ {Color.CYAN}macOS Edition{Color.RESET}
""")


def print_section(title: str, color: str = Color.BRIGHT_CYAN):
    """Print section header"""
    print(f"\n{color}{'─' * 80}{Color.RESET}")
    print(f"{Color.BOLD}{color}■ {title}{Color.RESET}")
    print(f"{color}{'─' * 80}{Color.RESET}\n")


def print_info(label: str, value: str, indent: int = 0):
    """Print labeled information"""
    spaces = "  " * indent
    print(f"{spaces}{Color.CYAN}{label}:{Color.RESET} {Color.WHITE}{value}{Color.RESET}")


def print_warning(message: str):
    """Print warning message"""
    print(f"{Color.BRIGHT_YELLOW}⚠ WARNING:{Color.RESET} {message}")


def print_error(message: str):
    """Print error message"""
    print(f"{Color.BRIGHT_RED}✗ ERROR:{Color.RESET} {message}")


def print_success(message: str):
    """Print success message"""
    print(f"{Color.BRIGHT_GREEN}✓{Color.RESET} {message}")


def clear_screen():
    """Clear terminal screen"""
    os.system('clear' if os.name != 'nt' else 'cls')