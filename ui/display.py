"""
Display utilities for USB LAB terminal interface.
"""

import os
from .colors import Color

def print_header():
    """Display ASCII art header - retro BBS style with large intricate character-based art"""
    # Color palette: Cyan, Yellow, Magenta for different sections
    header = f"""
    
{Color.BRIGHT_GREEN}            @@@  @@@  {Color.BRIGHT_MAGENTA} @@@@@@   {Color.BRIGHT_RED}@@@@@@@       {Color.BRIGHT_CYAN}@@@       {Color.BRIGHT_YELLOW} @@@@@@   {Color.BRIGHT_BLUE}@@@@@@@   
{Color.BRIGHT_GREEN}            @@@  @@@  {Color.BRIGHT_MAGENTA}@@@@@@@   {Color.BRIGHT_RED}@@@@@@@@      {Color.BRIGHT_CYAN}@@@       {Color.BRIGHT_YELLOW}@@@@@@@@  {Color.BRIGHT_BLUE}@@@@@@@@  
{Color.BRIGHT_GREEN}            @@!  @@@  {Color.BRIGHT_MAGENTA}!@@       {Color.BRIGHT_RED}@@!  @@@      {Color.BRIGHT_CYAN}@@!       {Color.BRIGHT_YELLOW}@@!  @@@  {Color.BRIGHT_BLUE}@@!  @@@  
{Color.BRIGHT_GREEN}            !@!  @!@  {Color.BRIGHT_MAGENTA}!@!       {Color.BRIGHT_RED}!@   @!@      {Color.BRIGHT_CYAN}!@!       {Color.BRIGHT_YELLOW}!@!  @!@  {Color.BRIGHT_BLUE}!@   @!@  
{Color.BRIGHT_GREEN}            @!@  !@!  {Color.BRIGHT_MAGENTA}!!@@!!    {Color.BRIGHT_RED}@!@!@!@       {Color.BRIGHT_CYAN}@!!       {Color.BRIGHT_YELLOW}@!@!@!@!  {Color.BRIGHT_BLUE}@!@!@!@   
{Color.BRIGHT_GREEN}            !@!  !!!  {Color.BRIGHT_MAGENTA} !!@!!!   {Color.BRIGHT_RED}!!!@!!!!      {Color.BRIGHT_CYAN}!!!       {Color.BRIGHT_YELLOW}!!!@!!!!  {Color.BRIGHT_BLUE}!!!@!!!!  
{Color.BRIGHT_GREEN}            !!:  !!!  {Color.BRIGHT_MAGENTA}    !:!   {Color.BRIGHT_RED}!!:  !!!      {Color.BRIGHT_CYAN}!!:       {Color.BRIGHT_YELLOW}!!:  !!!  {Color.BRIGHT_BLUE}!!:  !!!  
{Color.BRIGHT_GREEN}            :!:  !:!  {Color.BRIGHT_MAGENTA}   !:!    {Color.BRIGHT_RED}:!:  !:!      {Color.BRIGHT_CYAN} :!:      {Color.BRIGHT_YELLOW}:!:  !:!  {Color.BRIGHT_BLUE}:!:  !:!  
{Color.BRIGHT_GREEN}            ::::: ::  {Color.BRIGHT_MAGENTA}:::: ::   {Color.BRIGHT_RED} :: ::::      {Color.BRIGHT_CYAN} :: ::::  {Color.BRIGHT_YELLOW}::   :::  {Color.BRIGHT_BLUE} :: ::::  
{Color.BRIGHT_GREEN}             : :  :   {Color.BRIGHT_MAGENTA}:: : :    {Color.BRIGHT_RED}:: : ::       {Color.BRIGHT_CYAN}: :: : :  {Color.BRIGHT_YELLOW} :   : :  {Color.BRIGHT_BLUE}:: : ::    
                                                         
                                                         
        {Color.BRIGHT_MAGENTA}══════════════════════════════════════════════════════════════════════
                {Color.WHITE}USB DRIVE ANALYSIS · TESTING · BENCHMARKING SUITE
        {Color.BRIGHT_MAGENTA}══════════════════════════════════════════════════════════════════════

{Color.BRIGHT_CYAN}            [{Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN}] Read-Only Inspection        [{Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN}] Sequential R/W Testing
{Color.BRIGHT_CYAN}            [{Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN}] Drive Classification        [{Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN}] Random 4K IOPS Testing
{Color.BRIGHT_CYAN}            [{Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN}] Health Verification         [{Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN}] Sustained Performance Tests
{Color.BRIGHT_CYAN}            [{Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN}] Performance Logging         [{Color.BRIGHT_YELLOW}●{Color.BRIGHT_CYAN}] Small File Operation Tests

            {Color.BRIGHT_YELLOW}Version 0.3.0{Color.WHITE} - macOS Edition  {Color.BRIGHT_CYAN}|{Color.WHITE}  Offline Only  {Color.BRIGHT_CYAN}|{Color.WHITE}  Read/Write

{Color.RESET}

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