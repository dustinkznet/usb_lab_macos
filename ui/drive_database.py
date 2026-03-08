"""
Drive database viewer for USB LAB.
Displays registered drives and database statistics.
ADDED: Alerts when known drives reconnect.
"""

from database.db_manager import DatabaseManager
from ui.colors import Color
from ui.display import clear_screen, print_header, print_section, print_warning, print_error


class DriveDatabase:
    """View and manage drive database"""

    def __init__(self, db: DatabaseManager):
        self.db = db

    def show_database_menu(self):
        """Main database menu"""
        clear_screen()
        print_header()

        print_section("Drive Database", Color.BRIGHT_BLUE)

        cursor = self.db.conn.cursor()

        cursor.execute('SELECT COUNT(*) as count FROM drives')
        drive_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM test_runs')
        test_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(*) as count FROM inspection_history')
        inspection_count = cursor.fetchone()['count']

        cursor.execute('SELECT COUNT(DISTINCT drive_id) as count FROM test_runs')
        tested_drive_count = cursor.fetchone()['count']

        print(f"{Color.BRIGHT_WHITE}Database Statistics:{Color.RESET}\n")
        print(f"  Total Drives Registered: {Color.BRIGHT_CYAN}{drive_count}{Color.RESET}")
        print(f"  Total Inspections: {Color.BRIGHT_CYAN}{inspection_count}{Color.RESET}")
        print(f"  Total Test Runs: {Color.BRIGHT_CYAN}{test_count}{Color.RESET}")
        print(f"  Drives with Test Data: {Color.BRIGHT_CYAN}{tested_drive_count}{Color.RESET}")
        print()

        print(f"  Database Location: {Color.CYAN}{self.db.db_path}{Color.RESET}")
        print()

        print(f"{Color.BRIGHT_WHITE}Recent Activity:{Color.RESET}\n")

        cursor.execute('''
            SELECT d.vendor, d.model, d.last_seen, 
                   (SELECT COUNT(*) FROM test_runs WHERE drive_id = d.drive_id) as test_count
            FROM drives d
            ORDER BY d.last_seen DESC
            LIMIT 5
        ''')
        recent_drives = cursor.fetchall()

        if recent_drives:
            for drive in recent_drives:
                # FIXED: Smart vendor/model display
                vendor_model = f"{drive['vendor']} {drive['model']}" if drive['model'] else drive['vendor']
                print(f"  {Color.CYAN}{vendor_model}{Color.RESET}")
                print(f"    Last seen: {drive['last_seen']} | Tests: {drive['test_count']}")
                print()
        else:
            print(f"  {Color.YELLOW}No drives in database yet{Color.RESET}\n")

        print(f"\n{Color.BRIGHT_WHITE}Options:{Color.RESET}\n")
        print(f"  {Color.BRIGHT_YELLOW}[1]{Color.RESET} View all drives")
        print(f"  {Color.BRIGHT_YELLOW}[2]{Color.RESET} Export database (coming soon)")
        print(f"  {Color.BRIGHT_YELLOW}[3]{Color.RESET} Clear database (coming soon)")
        print(f"  {Color.BRIGHT_YELLOW}[B]{Color.RESET} Back to main menu\n")

        print(f"{Color.BRIGHT_CYAN}{'─' * 80}{Color.RESET}")
        choice = input(f"{Color.BRIGHT_GREEN}Select option: {Color.RESET}").strip().upper()

        if choice == '1':
            self.view_all_drives()
        elif choice == 'B':
            return
        else:
            print_warning("Option not yet implemented")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to continue...{Color.RESET}")

    def view_all_drives(self):
        """View all drives in database"""
        clear_screen()
        print_header()

        print_section("All Registered Drives", Color.BRIGHT_BLUE)

        cursor = self.db.conn.cursor()
        cursor.execute('''
            SELECT drive_id, vendor, model, serial_number, capacity_bytes, 
                   bus_protocol, first_seen, last_seen
            FROM drives
            ORDER BY last_seen DESC
        ''')
        drives = cursor.fetchall()

        if not drives:
            print_warning("No drives in database")
            input(f"\n{Color.BRIGHT_WHITE}Press Enter to return...{Color.RESET}")
            return

        print(f"{Color.BRIGHT_WHITE}Total Drives: {len(drives)}{Color.RESET}\n")

        for i, drive in enumerate(drives, 1):
            # FIXED: Smart vendor/model display
            vendor_model = f"{drive['vendor']} {drive['model']}" if drive['model'] else drive['vendor']

            print(f"{Color.BRIGHT_YELLOW}[{i}] {vendor_model}{Color.RESET}")
            print(f"    Serial: {drive['serial_number']}")
            print(f"    Capacity: {drive['capacity_bytes'] / (1024 ** 3):.1f} GB")
            print(f"    Bus: {drive['bus_protocol']}")
            print(f"    First seen: {drive['first_seen']}")
            print(f"    Last seen: {drive['last_seen']}")

            cursor.execute('SELECT COUNT(*) as count FROM test_runs WHERE drive_id = ?', (drive['drive_id'],))
            test_count = cursor.fetchone()['count']
            print(f"    {Color.CYAN}Tests recorded: {test_count}{Color.RESET}")
            print()

        input(f"\n{Color.BRIGHT_WHITE}Press Enter to return...{Color.RESET}")

    def check_for_known_drive(self, drive_id: str) -> bool:
        """
        Check if a drive is already in the database.
        Display alert if it's a known drive.

        Args:
            drive_id: Drive identifier to check

        Returns:
            True if known drive, False if new
        """
        cursor = self.db.conn.cursor()
        cursor.execute('SELECT vendor, model, last_seen FROM drives WHERE drive_id = ?', (drive_id,))
        result = cursor.fetchone()

        if result:
            vendor_model = f"{result['vendor']} {result['model']}" if result['model'] else result['vendor']
            print(f"\n{Color.BRIGHT_GREEN} KNOWN DRIVE DETECTED{Color.RESET}")
            print(f"  {Color.BRIGHT_CYAN}{vendor_model}{Color.RESET}")
            print(f"  Last tested: {result['last_seen']}\n")
            return True

        return False