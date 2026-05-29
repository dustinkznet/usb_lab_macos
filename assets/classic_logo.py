#!/usr/bin/env python3
"""
USB LAB Classic Logo — retro BBS-style ASCII art header.
Preserved from usb_lab_classic (the original version).
Run this file directly to preview the logo in terminal.
"""


class Color:
    """ANSI color codes for retro BBS aesthetic"""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'


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
{Color.BRIGHT_CYAN}║{Color.BRIGHT_WHITE}                                                                                {Color.BRIGHT_CYAN}║{Color.RESET}"""
    print(header)


if __name__ == "__main__":
    print_header()
