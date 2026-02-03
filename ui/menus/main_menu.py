"""
Main menu orchestrator for USB LAB.
Coordinates navigation between different menu modules.
"""

from typing import Optional
from database.db_manager import DatabaseManager
from inspection.disk_inspector import DiskInspector
from ui.display import clear_screen, print_header, print_error
from ui.colors import Color
from ui.menus.examine_drives_menu import ExamineDrivesMenu
from ui.menus.speed_test_menu import SpeedTestMenu
from ui.test_history import TestHistoryViewer
from ui.drive_database import DriveDatabase
from ui.settings_menu import SettingsMenu


class MenuSystem:
    """
    Main menu system coordinator.

    Delegates to specialized menu classes for different functions.
    """

    def __init__(self, inspector: DiskInspector, db: DatabaseManager, settings):
        self.inspector = inspector
        self.db = db
        self.settings = settings

        # Initialize menu modules
        self.examine_menu = ExamineDrivesMenu(inspector, db, settings)
        self.speed_test_menu = SpeedTestMenu(inspector, db, settings)
        self.test_history = TestHistoryViewer(db)
        self.drive_db = DriveDatabase(db)
        self.settings_ui = SettingsMenu(settings)

    def display_main_menu(self) -> Optional[str]:
        """
        Display main menu and get user choice.

        Returns:
            Menu choice or None to exit
        """
        print(f"\n{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BRIGHT_WHITE}MAIN MENU{Color.RESET}")
        print(f"{Color.BRIGHT_CYAN}{'═' * 80}{Color.RESET}\n")

        menu_items = [
            ("1", "Examine Drives", "Inspect USB drives (read-only, auto-detect)"),
            ("2", "Read/Write Speed Tests", "Benchmark drive performance"),
            ("3", "View Test History", "Review past test results"),
            ("4", "Drive Database", "Manage drive records"),
            ("5", "Settings", "Configure USB LAB"),
            ("Q", "Quit", "Exit USB LAB"),
        ]

        for key, title, desc in menu_items:
            print(f"  {Color.BRIGHT_YELLOW}[{key}]{Color.RESET} {Color.BRIGHT_WHITE}{title}{Color.RESET}")
            print(f"      {Color.CYAN}{desc}{Color.RESET}\n")

        print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
        choice = input(f"{Color.BRIGHT_GREEN}Select option: {Color.RESET}").strip().upper()

        return choice if choice else None

    def handle_choice(self, choice: str) -> bool:
        """
        Handle main menu choice.

        Args:
            choice: User's menu selection

        Returns:
            True to continue running, False to quit
        """
        if choice == '1':
            self.examine_menu.show()
        elif choice == '2':
            self.speed_test_menu.show()
        elif choice == '3':
            self.test_history.show_test_history_menu()
        elif choice == '4':
            self.drive_db.show_database_menu()
        elif choice == '5':
            self.settings_ui.show_settings_menu()
        elif choice == 'Q':
            return False
        else:
            print_error("Invalid menu option")
            input(f"\nPress Enter to continue...")

        return True