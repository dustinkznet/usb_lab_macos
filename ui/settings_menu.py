"""
Settings menu for USB LAB.
Manages user configuration and preferences.
"""

from pathlib import Path
from settings.settings_manager import SettingsManager
from ui.colors import Color
from ui.display import clear_screen, print_header, print_section, print_success, print_error


class SettingsMenu:
    """Settings and configuration interface"""

    def __init__(self, settings: SettingsManager):
        self.settings = settings

    def show_settings_menu(self):
        """Settings and configuration menu"""
        while True:
            clear_screen()
            print_header()

            print_section("Settings & Configuration", Color.BRIGHT_CYAN)

            # Display current settings organized by category
            print(f"{Color.BRIGHT_WHITE}Current Settings:{Color.RESET}\n")

            # Inspection Settings
            print(f"{Color.BRIGHT_YELLOW}Inspection Settings:{Color.RESET}")
            print(
                f"  1. Default Inspection Mode: {Color.CYAN}{self.settings.get('default_inspection_mode')}{Color.RESET}")
            print(
                f"  2. Auto-mount for Inspection: {Color.CYAN}{self.settings.get('auto_mount_for_inspection')}{Color.RESET}")
            print(f"  3. Show Hidden Files: {Color.CYAN}{self.settings.get('show_hidden_files')}{Color.RESET}")
            print()

            # Testing Settings
            print(f"{Color.BRIGHT_YELLOW}Testing Settings:{Color.RESET}")
            print(
                f"  4. Default Test File Size: {Color.CYAN}{self.settings.get('default_test_file_size_mb')} MB{Color.RESET}")
            print(
                f"  5. Random Operations Count: {Color.CYAN}{self.settings.get('default_random_operations')}{Color.RESET}")
            print(
                f"  6. Confirm Before Testing: {Color.CYAN}{self.settings.get('confirm_before_testing')}{Color.RESET}")
            print()

            # Display Settings
            print(f"{Color.BRIGHT_YELLOW}Display Settings:{Color.RESET}")
            print(f"  7. Use Colors: {Color.CYAN}{self.settings.get('use_colors')}{Color.RESET}")
            print(f"  8. Show Debug Info: {Color.CYAN}{self.settings.get('show_debug_info')}{Color.RESET}")
            print(f"  9. Verbose Output: {Color.CYAN}{self.settings.get('verbose_output')}{Color.RESET}")
            print()

            # Safety Settings
            print(f"{Color.BRIGHT_YELLOW}Safety Settings:{Color.RESET}")
            print(
                f"  10. Block Installer Testing: {Color.CYAN}{self.settings.get('block_installer_testing')}{Color.RESET}")
            print(
                f"  11. Read-Only Inspection: {Color.CYAN}{self.settings.get('readonly_inspection_only')}{Color.RESET}")
            print(
                f"  12. Confirm Data Drive Tests: {Color.CYAN}{self.settings.get('require_confirmation_data_drives')}{Color.RESET}")
            print()

            # Actions
            print(f"{Color.BRIGHT_YELLOW}Actions:{Color.RESET}")
            print(f"  R. Reset to Defaults")
            print(f"  E. Export Settings")
            print(f"  I. Import Settings")
            print(f"  B. Back to Main Menu")
            print()

            print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
            choice = input(f"{Color.BRIGHT_GREEN}Select option to modify: {Color.RESET}").strip().upper()

            if choice == 'B':
                break
            elif choice == 'R':
                self._reset_settings()
            elif choice == 'E':
                self._export_settings()
            elif choice == 'I':
                self._import_settings()
            elif choice.isdigit():
                self._modify_setting(int(choice))
            else:
                print_error("Invalid option")
                input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def _modify_setting(self, option: int):
        """Modify a specific setting"""
        clear_screen()
        print_header()

        if option == 1:
            print_section("Default Inspection Mode", Color.BRIGHT_CYAN)
            print(f"Current: {Color.CYAN}{self.settings.get('default_inspection_mode')}{Color.RESET}\n")
            print("Options:")
            print("  1. smart_auto (recommended) - Auto-detect based on mount status")
            print("  2. metadata_only - Only inspect partition metadata")
            print("  3. mounted_readonly - Always scan mounted filesystems")
            print()
            choice = input("Select mode [1-3]: ").strip()

            modes = {'1': 'smart_auto', '2': 'metadata_only', '3': 'mounted_readonly'}
            if choice in modes:
                self.settings.set('default_inspection_mode', modes[choice])
                print_success(f"Updated to {modes[choice]}")
            else:
                print_error("Invalid choice")

        elif option == 2:
            self._toggle_boolean('auto_mount_for_inspection',
                                 "Auto-mount for Inspection",
                                 "Automatically mount unmounted drives for full inspection")

        elif option == 3:
            self._toggle_boolean('show_hidden_files',
                                 "Show Hidden Files",
                                 "Include hidden files in installer detection")

        elif option == 4:
            self._modify_numeric('default_test_file_size_mb',
                                 "Default Test File Size (MB)",
                                 10, 1000, " MB")

        elif option == 5:
            self._modify_numeric('default_random_operations',
                                 "Random Operations Count",
                                 100, 10000, " operations")

        elif option == 6:
            self._toggle_boolean('confirm_before_testing',
                                 "Confirm Before Testing",
                                 "Require confirmation before running speed tests")

        elif option == 7:
            self._toggle_boolean('use_colors',
                                 "Use Colors",
                                 "Enable ANSI color output in terminal")

        elif option == 8:
            self._toggle_boolean('show_debug_info',
                                 "Show Debug Info",
                                 "Display debug messages during operations")

        elif option == 9:
            self._toggle_boolean('verbose_output',
                                 "Verbose Output",
                                 "Show detailed output during all operations")

        elif option == 10:
            self._toggle_boolean('block_installer_testing',
                                 "Block Installer Testing",
                                 "Prevent speed tests on installer media (RECOMMENDED)")

        elif option == 11:
            self._toggle_boolean('readonly_inspection_only',
                                 "Read-Only Inspection",
                                 "Never mount drives read-write for inspection (RECOMMENDED)")

        elif option == 12:
            self._toggle_boolean('require_confirmation_data_drives',
                                 "Confirm Data Drive Tests",
                                 "Require confirmation before testing drives with existing data")

        else:
            print_error("Invalid option")

        input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def _toggle_boolean(self, key: str, title: str, description: str):
        """Toggle a boolean setting"""
        clear_screen()
        print_header()

        print_section(title, Color.BRIGHT_CYAN)
        print(f"{description}\n")
        print(f"Current value: {Color.CYAN}{self.settings.get(key)}{Color.RESET}\n")

        new_value = not self.settings.get(key)
        confirm = input(f"Change to {Color.BRIGHT_YELLOW}{new_value}{Color.RESET}? (y/n): ").strip().lower()

        if confirm == 'y':
            self.settings.set(key, new_value)
            print_success(f"Updated to {new_value}")
        else:
            print(f"{Color.CYAN}No change made{Color.RESET}")

    def _modify_numeric(self, key: str, title: str, min_val: int, max_val: int, unit: str = ""):
        """Modify a numeric setting"""
        clear_screen()
        print_header()

        print_section(title, Color.BRIGHT_CYAN)
        print(f"Current value: {Color.CYAN}{self.settings.get(key)}{unit}{Color.RESET}")
        print(f"Valid range: {min_val} - {max_val}\n")

        try:
            new_value = int(input(f"Enter new value: ").strip())
            if min_val <= new_value <= max_val:
                self.settings.set(key, new_value)
                print_success(f"Updated to {new_value}{unit}")
            else:
                print_error(f"Value must be between {min_val} and {max_val}")
        except ValueError:
            print_error("Invalid number")

    def _reset_settings(self):
        """Reset all settings to defaults"""
        clear_screen()
        print_header()

        print_section("Reset to Defaults", Color.BRIGHT_RED)
        print(f"{Color.BRIGHT_YELLOW}⚠ WARNING{Color.RESET}")
        print("This will reset ALL settings to their default values.\n")

        confirm = input("Are you sure? Type 'yes' to confirm: ").strip().lower()

        if confirm == 'yes':
            self.settings.reset_to_defaults()
            print_success("All settings reset to defaults")
        else:
            print(f"{Color.CYAN}Reset cancelled{Color.RESET}")

        input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def _export_settings(self):
        """Export settings to a file"""
        clear_screen()
        print_header()

        print_section("Export Settings", Color.BRIGHT_CYAN)

        default_path = str(Path.home() / "usb_lab_settings_export.json")
        print(f"Default export path: {Color.CYAN}{default_path}{Color.RESET}\n")

        path = input("Enter export path (or press Enter for default): ").strip()
        if not path:
            path = default_path

        try:
            self.settings.export_settings(path)
            print_success(f"Settings exported to {path}")
        except Exception as e:
            print_error(f"Export failed: {e}")

        input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def _import_settings(self):
        """Import settings from a file"""
        clear_screen()
        print_header()

        print_section("Import Settings", Color.BRIGHT_CYAN)
        print(f"{Color.BRIGHT_YELLOW}⚠ WARNING{Color.RESET}")
        print("This will overwrite your current settings.\n")

        path = input("Enter import file path: ").strip()

        if not path:
            print_error("No path specified")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
            return

        if not Path(path).exists():
            print_error(f"File not found: {path}")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")
            return

        confirm = input(f"Import settings from {path}? (y/n): ").strip().lower()

        if confirm == 'y':
            try:
                self.settings.import_settings(path)
                print_success("Settings imported successfully")
            except Exception as e:
                print_error(f"Import failed: {e}")
        else:
            print(f"{Color.CYAN}Import cancelled{Color.RESET}")

        input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")