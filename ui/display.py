"""
Display utilities for USB LAB terminal interface.
"""

import os
from .colors import Color

def print_header():
    """Display ASCII art header - retro BBS style"""
    header = f"""
{Color.BRIGHT_CYAN}╔════════════════════════════════════════════════════════════════════════════════╗
{Color.BRIGHT_CYAN}║{Color.BRIGHT_MAGENTA}     .═════════════════════════════════════════════════════════════════════.     {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_MAGENTA}    /                                                                       \\    {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_YELLOW}   ║    {Color.BRIGHT_RED}██╗   ██╗{Color.BRIGHT_YELLOW}███████╗{Color.BRIGHT_GREEN}██████╗ {Color.BRIGHT_CYAN}    ██╗      {Color.BRIGHT_BLUE}█████╗ {Color.BRIGHT_MAGENTA}██████╗{Color.BRIGHT_YELLOW}     ║   {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_YELLOW}   ║    {Color.BRIGHT_RED}██║   ██║{Color.BRIGHT_YELLOW}██╔════╝{Color.BRIGHT_GREEN}██╔══██╗{Color.BRIGHT_CYAN}    ██║     {Color.BRIGHT_BLUE}██╔══██╗{Color.BRIGHT_MAGENTA}██╔══██╗{Color.BRIGHT_YELLOW}    ║   {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_YELLOW}   ║    {Color.BRIGHT_RED}██║   ██║{Color.BRIGHT_YELLOW}███████╗{Color.BRIGHT_GREEN}██████╔╝{Color.BRIGHT_CYAN}    ██║     {Color.BRIGHT_BLUE}███████║{Color.BRIGHT_MAGENTA}██████╔╝{Color.BRIGHT_YELLOW}    ║   {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_YELLOW}   ║    {Color.BRIGHT_RED}██║   ██║{Color.BRIGHT_YELLOW}╚════██║{Color.BRIGHT_GREEN}██╔══██╗{Color.BRIGHT_CYAN}    ██║     {Color.BRIGHT_BLUE}██╔══██║{Color.BRIGHT_MAGENTA}██╔══██╗{Color.BRIGHT_YELLOW}    ║   {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_YELLOW}   ║    {Color.BRIGHT_RED}╚██████╔╝{Color.BRIGHT_YELLOW}███████║{Color.BRIGHT_GREEN}██████╔╝{Color.BRIGHT_CYAN}    ███████╗{Color.BRIGHT_BLUE}██║  ██║{Color.BRIGHT_MAGENTA}██████╔╝{Color.BRIGHT_YELLOW}    ║   {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_YELLOW}   ║    {Color.BRIGHT_RED} ╚═════╝ {Color.BRIGHT_YELLOW}╚══════╝{Color.BRIGHT_GREEN}╚═════╝ {Color.BRIGHT_CYAN}    ╚══════╝{Color.BRIGHT_BLUE}╚═╝  ╚═╝{Color.BRIGHT_MAGENTA}╚═════╝{Color.BRIGHT_YELLOW}     ║   {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_MAGENTA}    \\                                                                       /    {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_MAGENTA}     '═════════════════════════════════════════════════════════════════════'     {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_WHITE}                                                                                {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_GREEN}╔═══════════════════════════════════════════════════════════════════════════╗  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_GREEN}║ {Color.BRIGHT_YELLOW}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ {Color.BRIGHT_GREEN}║  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_GREEN}║ {Color.BRIGHT_YELLOW}▓▓{Color.BRIGHT_WHITE}  USB DRIVE ANALYSIS · TESTING · BENCHMARKING SUITE  {Color.BRIGHT_YELLOW}▓▓ {Color.BRIGHT_GREEN}║  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_GREEN}║ {Color.BRIGHT_YELLOW}▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓ {Color.BRIGHT_GREEN}║  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_GREEN}╚═══════════════════════════════════════════════════════════════════════════╝  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_WHITE}                                                                                {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_CYAN}╭───────────────────────────────────────────────────────────────────────────╮  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_CYAN}│ {Color.BRIGHT_GREEN}[●]{Color.BRIGHT_WHITE} Read-Only Inspection    {Color.BRIGHT_GREEN}[●]{Color.BRIGHT_WHITE} Sequential R/W Testing              {Color.BRIGHT_CYAN}│  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_CYAN}│ {Color.BRIGHT_GREEN}[●]{Color.BRIGHT_WHITE} Drive Classification    {Color.BRIGHT_GREEN}[●]{Color.BRIGHT_WHITE} Random 4K IOPS Testing              {Color.BRIGHT_CYAN}│  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_CYAN}│ {Color.BRIGHT_GREEN}[●]{Color.BRIGHT_WHITE} Health Verification     {Color.BRIGHT_GREEN}[●]{Color.BRIGHT_WHITE} Sustained Performance Tests         {Color.BRIGHT_CYAN}│  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_CYAN}│ {Color.BRIGHT_GREEN}[●]{Color.BRIGHT_WHITE} Performance Logging     {Color.BRIGHT_GREEN}[●]{Color.BRIGHT_WHITE} Small File Operation Tests          {Color.BRIGHT_CYAN}│  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║  {Color.BRIGHT_CYAN}╰───────────────────────────────────────────────────────────────────────────╯  {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_WHITE}                                                                                {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║    {Color.BRIGHT_MAGENTA}┌─────────────────────────────────────────────────────────────────────┐      {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║    {Color.BRIGHT_MAGENTA}│  {Color.BRIGHT_YELLOW}Version 0.3.0{Color.BRIGHT_WHITE} - macOS Edition  {Color.BRIGHT_CYAN}│{Color.BRIGHT_WHITE}  Offline Only{Color.BRIGHT_CYAN} │{Color.BRIGHT_WHITE}  Read/Write  {Color.BRIGHT_MAGENTA}│      {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║    {Color.BRIGHT_MAGENTA}└─────────────────────────────────────────────────────────────────────┘      {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}║{Color.BRIGHT_WHITE}                                                                                {Color.BRIGHT_CYAN}║
{Color.BRIGHT_CYAN}╚════════════════════════════════════════════════════════════════════════════════╝{Color.RESET}
"""
    print(header)


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