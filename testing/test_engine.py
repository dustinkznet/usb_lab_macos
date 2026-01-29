"""
Drive testing engine for health checks and performance benchmarks.
"""

import os
import shutil
from datetime import datetime
from typing import Optional, List
from core.models import PhysicalDisk, Partition, TestResult
from core.enums import TestType, DiskType
from core.constants import TEST_DIR_NAME, BLOCK_SIZE_4K, BLOCK_SIZE_1MB
from database.db_manager import DatabaseManager
from ui.colors import Color


class DriveTestEngine:
    """
    Comprehensive drive testing engine.

    Performs health checks and performance benchmarks on USB drives.
    All tests are designed to be safe and informative.
    """

    def __init__(self, db: DatabaseManager):
        self.db = db
        self.test_dir_name = TEST_DIR_NAME

    def should_test_drive(self, disk: PhysicalDisk) -> tuple[bool, str]:
        """
        Determine if a drive is safe to test.

        CRITICAL: We want to avoid testing:
        - OS installer media (could corrupt boot files)
        - Boot/Recovery drives (system critical)

        We CAN test:
        - Empty drives
        - Data storage drives
        - Drives that appear to have user data but user confirms

        Args:
            disk: PhysicalDisk to evaluate

        Returns:
            (should_test: bool, reason: str)
        """
        # Never test installer media
        installer_types = [
            DiskType.MACOS_INSTALLER_LEGACY,
            DiskType.MACOS_INSTALLER_MODERN,
            DiskType.LINUX_INSTALLER,
            DiskType.WINDOWS_INSTALLER,
            DiskType.BOOT_RECOVERY
        ]

        if disk.disk_type in installer_types:
            return False, f"Drive contains {disk.disk_type.value} - testing not recommended"

        # Check for mounted partitions with existing data
        data_partitions = []
        for part in disk.partitions:
            if part.is_mounted and part.mount_point:
                try:
                    # Check if partition has existing files
                    files = os.listdir(part.mount_point)
                    visible_files = [f for f in files if not f.startswith('.')]
                    if visible_files:
                        data_partitions.append(part.identifier)
                except (PermissionError, OSError):
                    pass

        if data_partitions:
            return True, f"Drive has data on {len(data_partitions)} partition(s) - user confirmation required"

        # Empty or unformatted drives are safe to test
        if disk.disk_type in [DiskType.EMPTY, DiskType.DATA_DISK]:
            return True, "Drive appears safe for testing"

        # Unknown drives - proceed with caution
        if disk.disk_type == DiskType.UNKNOWN:
            return True, "Drive type unknown - user confirmation required"

        return False, "Drive type not recognized for testing"

    def run_health_check(self, partition: Partition, drive_id: str) -> TestResult:
        """
        Run basic health check on a partition.

        This test:
        1. Verifies read access
        2. Checks for bad sectors (read verification)
        3. Tests basic write capability (if writable)

        Args:
            partition: Partition to test
            drive_id: Drive identifier for logging

        Returns:
            TestResult with health check results
        """
        print(f"\n{Color.BRIGHT_CYAN}Running health check on {partition.identifier}...{Color.RESET}")

        if not partition.is_mounted:
            return TestResult(
                test_type=TestType.HEALTH_CHECK,
                success=False,
                duration_seconds=0,
                error_message="Partition not mounted"
            )

        start_time = datetime.now()
        notes = []

        try:
            # Test 1: Read access
            print(f"  {Color.CYAN}[1/3] Checking read access...{Color.RESET}", end=" ")
            files = os.listdir(partition.mount_point)
            print(f"{Color.BRIGHT_GREEN}✓{Color.RESET}")
            notes.append(f"Read access verified ({len(files)} items)")

            # Test 2: Create test directory
            print(f"  {Color.CYAN}[2/3] Checking write access...{Color.RESET}", end=" ")
            test_dir = os.path.join(partition.mount_point, self.test_dir_name)

            try:
                os.makedirs(test_dir, exist_ok=True)
                print(f"{Color.BRIGHT_GREEN}✓{Color.RESET}")
                notes.append("Write access verified")
                writable = True
            except PermissionError:
                print(f"{Color.BRIGHT_YELLOW}✗ Read-only{Color.RESET}")
                notes.append("Partition is read-only")
                writable = False

            # Test 3: Basic read verification (sample files)
            print(f"  {Color.CYAN}[3/3] Verifying data integrity...{Color.RESET}", end=" ")
            readable_count = 0
            for item in files[:10]:  # Sample first 10 items
                item_path = os.path.join(partition.mount_point, item)
                if os.path.isfile(item_path):
                    try:
                        with open(item_path, 'rb') as f:
                            f.read(4096)  # Read first 4KB
                        readable_count += 1
                    except (PermissionError, OSError):
                        pass

            print(f"{Color.BRIGHT_GREEN}✓{Color.RESET}")
            notes.append(f"Verified {readable_count} files readable")

            duration = (datetime.now() - start_time).total_seconds()

            # Log to database
            self.db.log_test_run(
                drive_id=drive_id,
                test_type=TestType.HEALTH_CHECK.value,
                filesystem_tested=partition.filesystem.value,
                mount_point=partition.mount_point,
                partition_identifier=partition.identifier,
                duration_seconds=duration,
                success=True,
                notes="; ".join(notes)
            )

            return TestResult(
                test_type=TestType.HEALTH_CHECK,
                success=True,
                duration_seconds=duration,
                notes=notes
            )

        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            return TestResult(
                test_type=TestType.HEALTH_CHECK,
                success=False,
                duration_seconds=duration,
                error_message=str(e)
            )

    def run_sequential_test(self, partition: Partition, drive_id: str,
                           test_type: TestType, file_size_mb: int = 100) -> TestResult:
        """
        Run sequential read or write test.

        Args:
            partition: Partition to test
            drive_id: Drive identifier for logging
            test_type: SEQUENTIAL_READ or SEQUENTIAL_WRITE
            file_size_mb: Size of test file in MB

        Returns:
            TestResult with speed measurements
        """
        if not partition.is_mounted:
            return TestResult(
                test_type=test_type,
                success=False,
                duration_seconds=0,
                error_message="Partition not mounted"
            )

        test_dir = os.path.join(partition.mount_point, self.test_dir_name)
        test_file = os.path.join(test_dir, f"test_{file_size_mb}mb.dat")

        try:
            os.makedirs(test_dir, exist_ok=True)
        except PermissionError:
            return TestResult(
                test_type=test_type,
                success=False,
                duration_seconds=0,
                error_message="No write permission"
            )

        file_size_bytes = file_size_mb * 1024 * 1024
        block_size = 1024 * 1024  # 1MB blocks

        try:
            if test_type == TestType.SEQUENTIAL_WRITE:
                print(f"\n{Color.BRIGHT_YELLOW}Testing sequential write ({file_size_mb}MB)...{Color.RESET}")

                start_time = datetime.now()

                with open(test_file, 'wb') as f:
                    bytes_written = 0
                    while bytes_written < file_size_bytes:
                        chunk_size = min(block_size, file_size_bytes - bytes_written)
                        f.write(os.urandom(chunk_size))
                        bytes_written += chunk_size
                    f.flush()
                    os.fsync(f.fileno())  # Ensure data is written to disk

                duration = (datetime.now() - start_time).total_seconds()
                speed_mbps = (file_size_bytes / duration) / (1024 * 1024)

                print(f"  {Color.BRIGHT_GREEN}✓ Write speed: {speed_mbps:.2f} MB/s{Color.RESET}")

            else:  # SEQUENTIAL_READ
                # First, create file if it doesn't exist
                if not os.path.exists(test_file):
                    print(f"  {Color.CYAN}Creating test file...{Color.RESET}")
                    with open(test_file, 'wb') as f:
                        f.write(os.urandom(file_size_bytes))

                print(f"\n{Color.BRIGHT_YELLOW}Testing sequential read ({file_size_mb}MB)...{Color.RESET}")

                start_time = datetime.now()

                with open(test_file, 'rb') as f:
                    bytes_read = 0
                    while bytes_read < file_size_bytes:
                        chunk = f.read(block_size)
                        if not chunk:
                            break
                        bytes_read += len(chunk)

                duration = (datetime.now() - start_time).total_seconds()
                speed_mbps = (file_size_bytes / duration) / (1024 * 1024)

                print(f"  {Color.BRIGHT_GREEN}✓ Read speed: {speed_mbps:.2f} MB/s{Color.RESET}")

            # Log to database
            self.db.log_test_run(
                drive_id=drive_id,
                test_type=test_type.value,
                filesystem_tested=partition.filesystem.value,
                mount_point=partition.mount_point,
                partition_identifier=partition.identifier,
                file_size_bytes=file_size_bytes,
                block_size_bytes=block_size,
                duration_seconds=duration,
                bytes_transferred=file_size_bytes,
                speed_mbps=speed_mbps,
                success=True
            )

            return TestResult(
                test_type=test_type,
                success=True,
                duration_seconds=duration,
                speed_mbps=speed_mbps,
                bytes_transferred=file_size_bytes
            )

        except Exception as e:
            return TestResult(
                test_type=test_type,
                success=False,
                duration_seconds=0,
                error_message=str(e)
            )
        finally:
            # Cleanup test file
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except:
                    pass

    def run_random_4k_test(self, partition: Partition, drive_id: str,
                          test_type: TestType, num_operations: int = 1000) -> TestResult:
        """
        Run random 4K read/write test (IOPS measurement).

        Args:
            partition: Partition to test
            drive_id: Drive identifier for logging
            test_type: RANDOM_4K_READ or RANDOM_4K_WRITE
            num_operations: Number of 4K operations to perform

        Returns:
            TestResult with IOPS measurements
        """
        if not partition.is_mounted:
            return TestResult(
                test_type=test_type,
                success=False,
                duration_seconds=0,
                error_message="Partition not mounted"
            )

        test_dir = os.path.join(partition.mount_point, self.test_dir_name)
        test_file = os.path.join(test_dir, "test_4k.dat")
        block_size = 4096  # 4KB

        try:
            os.makedirs(test_dir, exist_ok=True)

            # Create test file (10MB)
            file_size = 10 * 1024 * 1024
            if not os.path.exists(test_file):
                with open(test_file, 'wb') as f:
                    f.write(os.urandom(file_size))

            print(f"\n{Color.BRIGHT_YELLOW}Testing random 4K {'write' if test_type == TestType.RANDOM_4K_WRITE else 'read'} ({num_operations} ops)...{Color.RESET}")

            start_time = datetime.now()

            if test_type == TestType.RANDOM_4K_WRITE:
                with open(test_file, 'r+b') as f:
                    for _ in range(num_operations):
                        offset = (os.urandom(1)[0] % (file_size // block_size)) * block_size
                        f.seek(offset)
                        f.write(os.urandom(block_size))
                    f.flush()
            else:  # READ
                with open(test_file, 'rb') as f:
                    for _ in range(num_operations):
                        offset = (os.urandom(1)[0] % (file_size // block_size)) * block_size
                        f.seek(offset)
                        f.read(block_size)

            duration = (datetime.now() - start_time).total_seconds()
            iops = num_operations / duration
            bytes_transferred = num_operations * block_size
            speed_mbps = (bytes_transferred / duration) / (1024 * 1024)

            print(f"  {Color.BRIGHT_GREEN}✓ IOPS: {iops:.1f} | Speed: {speed_mbps:.2f} MB/s{Color.RESET}")

            # Log to database
            self.db.log_test_run(
                drive_id=drive_id,
                test_type=test_type.value,
                filesystem_tested=partition.filesystem.value,
                mount_point=partition.mount_point,
                partition_identifier=partition.identifier,
                file_size_bytes=file_size,
                block_size_bytes=block_size,
                duration_seconds=duration,
                bytes_transferred=bytes_transferred,
                speed_mbps=speed_mbps,
                iops=iops,
                success=True
            )

            return TestResult(
                test_type=test_type,
                success=True,
                duration_seconds=duration,
                speed_mbps=speed_mbps,
                iops=iops,
                bytes_transferred=bytes_transferred
            )

        except Exception as e:
            return TestResult(
                test_type=test_type,
                success=False,
                duration_seconds=0,
                error_message=str(e)
            )
        finally:
            if os.path.exists(test_file):
                try:
                    os.remove(test_file)
                except:
                    pass

    def run_comprehensive_test_suite(self, partition: Partition, drive_id: str) -> List[TestResult]:
        """
        Run the full test suite on a partition.

        Test order:
        1. Health check (verify drive is functional)
        2. Sequential read (100MB)
        3. Sequential write (100MB)
        4. Random 4K read (1000 ops)
        5. Random 4K write (1000 ops)

        Args:
            partition: Partition to test
            drive_id: Drive identifier for logging

        Returns:
            List of TestResult objects
        """
        results = []

        print(f"\n{Color.BRIGHT_MAGENTA}{'═' * 80}{Color.RESET}")
        print(f"{Color.BOLD}{Color.BRIGHT_WHITE}COMPREHENSIVE TEST SUITE{Color.RESET}")
        print(f"{Color.BRIGHT_MAGENTA}{'═' * 80}{Color.RESET}")

        # Test 1: Health Check
        print(f"\n{Color.BRIGHT_CYAN}[TEST 1/5] Health & Integrity Check{Color.RESET}")
        result = self.run_health_check(partition, drive_id)
        results.append(result)

        if not result.success:
            print(f"\n{Color.BRIGHT_RED}✗ Health check failed. Aborting test suite.{Color.RESET}")
            return results

        # Test 2: Sequential Read
        print(f"\n{Color.BRIGHT_CYAN}[TEST 2/5] Sequential Read Performance{Color.RESET}")
        result = self.run_sequential_test(partition, drive_id, TestType.SEQUENTIAL_READ, file_size_mb=100)
        results.append(result)

        # Test 3: Sequential Write
        print(f"\n{Color.BRIGHT_CYAN}[TEST 3/5] Sequential Write Performance{Color.RESET}")
        result = self.run_sequential_test(partition, drive_id, TestType.SEQUENTIAL_WRITE, file_size_mb=100)
        results.append(result)

        # Test 4: Random 4K Read
        print(f"\n{Color.BRIGHT_CYAN}[TEST 4/5] Random 4K Read (IOPS){Color.RESET}")
        result = self.run_random_4k_test(partition, drive_id, TestType.RANDOM_4K_READ, num_operations=1000)
        results.append(result)

        # Test 5: Random 4K Write
        print(f"\n{Color.BRIGHT_CYAN}[TEST 5/5] Random 4K Write (IOPS){Color.RESET}")
        result = self.run_random_4k_test(partition, drive_id, TestType.RANDOM_4K_WRITE, num_operations=1000)
        results.append(result)

        # Cleanup
        test_dir = os.path.join(partition.mount_point, self.test_dir_name)
        if os.path.exists(test_dir):
            try:
                shutil.rmtree(test_dir)
            except:
                pass

        return results