#!/usr/bin/env python3
"""
USB LAB - USB Drive Analysis, Testing & Benchmarking Suite
Main entry point for the application.
"""

import sys
from ui.display import clear_screen, print_header, print_error
from ui.colors import Color
from database.db_manager import DatabaseManager
from inspection.disk_inspector import DiskInspector
from ui.menus import MenuSystem
from settings.settings_manager import SettingsManager


def main():
    """Main application entry point"""

    # Check for macOS
    if sys.platform != 'darwin':
        print_error("USB LAB currently requires macOS")
        print("Linux support is planned for future releases")
        sys.exit(1)

    # Initialize database
    db = DatabaseManager()

    # Initialize settings
    settings = SettingsManager()

    # Create inspector with database and settings access
    inspector = DiskInspector(db=db, settings=settings)

    # Create menu system with inspector, database, and settings
    menu = MenuSystem(inspector, db, settings)

    # Main application loop
    while True:
        clear_screen()
        print_header()

        choice = menu.display_main_menu()

        if choice == '1':
            menu.examine_drives_menu()
        elif choice == '2':
            menu.speed_test_menu()
        elif choice == '3':
            menu.test_history_menu()
        elif choice == '4':
            menu.database_menu()
        elif choice == '5':
            menu.settings_menu()
        elif choice == 'Q':
            clear_screen()
            print(f"\n{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
            print(f"{Color.BRIGHT_YELLOW}Thank you for using USB LAB!{Color.RESET}")
            print(f"{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}\n")
            db.close()
            sys.exit(0)
        else:
            print_error("Invalid menu option")
            input(f"\nPress Enter to continue...")


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Color.BRIGHT_YELLOW}Interrupted by user{Color.RESET}")
        sys.exit(0)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)