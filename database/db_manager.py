"""
SQLite database manager for USB LAB.
"""

import sqlite3
import hashlib
import json
from pathlib import Path
from typing import Dict, Optional

from ..core import PhysicalDisk, DiskType
from ..core.constants import DB_DIR_NAME, DB_FILE_NAME

class DatabaseManager:
    """
    SQLite database manager for USB LAB.
    
    Stores comprehensive drive information, test results, and benchmarks.
    Database location: ~/.usb_lab/usb_lab.db
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None:
            # Default location: ~/.usb_lab/usb_lab.db
            home = Path.home()
            db_dir = home / '.usb_lab'
            db_dir.mkdir(exist_ok=True)
            db_path = db_dir / 'usb_lab.db'
        
        self.db_path = Path(db_path)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row  # Enable column access by name
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Create database schema if it doesn't exist"""
        cursor = self.conn.cursor()
        
        # Drives table - comprehensive drive identification
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drives (
                drive_id TEXT PRIMARY KEY,
                vendor TEXT,
                model TEXT,
                serial_number TEXT,
                capacity_bytes INTEGER,
                bus_protocol TEXT,
                controller_chip TEXT,
                usb_version TEXT,
                device_location TEXT,
                partition_scheme TEXT,
                firmware_version TEXT,
                first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                notes TEXT
            )
        ''')
        
        # Partitions table - track partition configurations over time
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS partitions (
                partition_id INTEGER PRIMARY KEY AUTOINCREMENT,
                drive_id TEXT,
                scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                partition_identifier TEXT,
                partition_name TEXT,
                filesystem_type TEXT,
                size_bytes INTEGER,
                mount_point TEXT,
                is_mounted BOOLEAN,
                volume_name TEXT,
                partition_scheme_type TEXT,
                FOREIGN KEY (drive_id) REFERENCES drives(drive_id)
            )
        ''')
        
        # Test runs table - all benchmark results
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_runs (
                run_id INTEGER PRIMARY KEY AUTOINCREMENT,
                drive_id TEXT,
                test_type TEXT,
                test_subtype TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                filesystem_tested TEXT,
                mount_point TEXT,
                partition_identifier TEXT,
                file_size_bytes INTEGER,
                block_size_bytes INTEGER,
                duration_seconds REAL,
                bytes_transferred INTEGER,
                speed_mbps REAL,
                iops REAL,
                cpu_usage_percent REAL,
                temperature_start_celsius REAL,
                temperature_end_celsius REAL,
                test_file_pattern TEXT,
                num_files INTEGER,
                success BOOLEAN,
                error_message TEXT,
                notes TEXT,
                FOREIGN KEY (drive_id) REFERENCES drives(drive_id)
            )
        ''')
        
        # Drive metadata - user-provided or advertised specs
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS drive_metadata (
                metadata_id INTEGER PRIMARY KEY AUTOINCREMENT,
                drive_id TEXT,
                advertised_read_speed_mbps REAL,
                advertised_write_speed_mbps REAL,
                warranty_years INTEGER,
                purchase_date DATE,
                purchase_price_usd REAL,
                purchase_location TEXT,
                drive_color TEXT,
                physical_condition TEXT,
                expected_use_case TEXT,
                FOREIGN KEY (drive_id) REFERENCES drives(drive_id)
            )
        ''')
        
        # Inspection history - track every time we examine a drive
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inspection_history (
                inspection_id INTEGER PRIMARY KEY AUTOINCREMENT,
                drive_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                disk_type TEXT,
                classification_confidence TEXT,
                num_partitions INTEGER,
                total_free_space_bytes INTEGER,
                contains_installer_markers BOOLEAN,
                installer_type TEXT,
                detected_markers TEXT,
                classification_notes TEXT,
                FOREIGN KEY (drive_id) REFERENCES drives(drive_id)
            )
        ''')
        
        # Connection events - track mount/unmount/connection issues
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS connection_events (
                event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                drive_id TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                event_type TEXT,
                success BOOLEAN,
                error_code TEXT,
                error_message TEXT,
                FOREIGN KEY (drive_id) REFERENCES drives(drive_id)
            )
        ''')
        
        # Create indices for common queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_test_runs_drive 
            ON test_runs(drive_id, timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_test_runs_type 
            ON test_runs(test_type, test_subtype)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_partitions_drive 
            ON partitions(drive_id, scan_timestamp DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_inspection_drive 
            ON inspection_history(drive_id, timestamp DESC)
        ''')
        
        self.conn.commit()
    
    def generate_drive_id(self, vendor: str, model: str, serial: str) -> str:
        """
        Generate unique drive ID from vendor, model, and serial.
        
        Args:
            vendor: Drive vendor/manufacturer
            model: Drive model
            serial: Drive serial number
        
        Returns:
            Unique drive ID (SHA256 hash)
        """
        # Create unique string from drive identifiers
        unique_str = f"{vendor}:{model}:{serial}".lower()
        return hashlib.sha256(unique_str.encode()).hexdigest()[:16]
    
    def register_drive(self, disk: 'PhysicalDisk') -> str:
        """
        Register or update a drive in the database.
        
        Args:
            disk: PhysicalDisk object
        
        Returns:
            drive_id
        """
        # Extract drive identifiers (we'll need to enhance PhysicalDisk to include these)
        vendor = disk.name.split()[0] if disk.name else "Unknown"
        model = disk.name if disk.name else "Unknown"
        serial = disk.identifier  # Temporary - should use actual serial
        
        drive_id = self.generate_drive_id(vendor, model, serial)
        
        cursor = self.conn.cursor()
        
        # Check if drive exists
        cursor.execute('SELECT drive_id FROM drives WHERE drive_id = ?', (drive_id,))
        exists = cursor.fetchone()
        
        if exists:
            # Update last_seen
            cursor.execute('''
                UPDATE drives 
                SET last_seen = CURRENT_TIMESTAMP,
                    capacity_bytes = ?,
                    bus_protocol = ?,
                    device_location = ?,
                    partition_scheme = ?
                WHERE drive_id = ?
            ''', (disk.size_bytes, disk.bus_protocol, disk.device_location, 
                  disk.partition_scheme, drive_id))
        else:
            # Insert new drive
            cursor.execute('''
                INSERT INTO drives (
                    drive_id, vendor, model, serial_number, capacity_bytes,
                    bus_protocol, device_location, partition_scheme
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (drive_id, vendor, model, serial, disk.size_bytes,
                  disk.bus_protocol, disk.device_location, disk.partition_scheme))
        
        self.conn.commit()
        return drive_id
    
    def log_inspection(self, drive_id: str, disk: 'PhysicalDisk'):
        """
        Log an inspection event.
        
        Args:
            drive_id: Unique drive identifier
            disk: PhysicalDisk object with inspection results
        """
        cursor = self.conn.cursor()
        
        # Prepare markers and notes
        detected_markers = []
        for part in disk.partitions:
            detected_markers.extend(part.detected_markers)
        
        markers_json = json.dumps(detected_markers) if detected_markers else None
        notes_json = json.dumps(disk.classification_notes) if disk.classification_notes else None
        
        cursor.execute('''
            INSERT INTO inspection_history (
                drive_id, disk_type, classification_confidence,
                num_partitions, contains_installer_markers,
                installer_type, detected_markers, classification_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            drive_id,
            disk.disk_type.value,
            disk.classification_confidence,
            len(disk.partitions),
            any(p.contains_installer_markers for p in disk.partitions),
            disk.disk_type.value if disk.disk_type != DiskType.DATA_DISK else None,
            markers_json,
            notes_json
        ))
        
        # Log partitions
        for partition in disk.partitions:
            cursor.execute('''
                INSERT INTO partitions (
                    drive_id, partition_identifier, partition_name,
                    filesystem_type, size_bytes, mount_point,
                    is_mounted, volume_name
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                drive_id,
                partition.identifier,
                partition.name,
                partition.filesystem.value,
                partition.size_bytes,
                partition.mount_point,
                partition.is_mounted,
                partition.volume_name
            ))
        
        self.conn.commit()
    
    def log_test_run(self, drive_id: str, test_type: str, **kwargs):
        """
        Log a benchmark test run.
        
        Args:
            drive_id: Unique drive identifier
            test_type: Type of test (sequential_read, random_4k_write, etc.)
            **kwargs: Additional test parameters and results
        """
        cursor = self.conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_runs (
                drive_id, test_type, test_subtype, filesystem_tested,
                mount_point, partition_identifier, file_size_bytes,
                block_size_bytes, duration_seconds, bytes_transferred,
                speed_mbps, iops, cpu_usage_percent, temperature_start_celsius,
                temperature_end_celsius, test_file_pattern, num_files,
                success, error_message, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            drive_id,
            test_type,
            kwargs.get('test_subtype'),
            kwargs.get('filesystem_tested'),
            kwargs.get('mount_point'),
            kwargs.get('partition_identifier'),
            kwargs.get('file_size_bytes'),
            kwargs.get('block_size_bytes'),
            kwargs.get('duration_seconds'),
            kwargs.get('bytes_transferred'),
            kwargs.get('speed_mbps'),
            kwargs.get('iops'),
            kwargs.get('cpu_usage_percent'),
            kwargs.get('temperature_start_celsius'),
            kwargs.get('temperature_end_celsius'),
            kwargs.get('test_file_pattern'),
            kwargs.get('num_files'),
            kwargs.get('success', True),
            kwargs.get('error_message'),
            kwargs.get('notes')
        ))
        
        self.conn.commit()
    
    def get_drive_history(self, drive_id: str) -> Dict:
        """
        Get complete history for a drive.
        
        Args:
            drive_id: Unique drive identifier
        
        Returns:
            Dictionary with drive info, inspections, and test results
        """
        cursor = self.conn.cursor()
        
        # Get drive info
        cursor.execute('SELECT * FROM drives WHERE drive_id = ?', (drive_id,))
        drive = cursor.fetchone()
        
        # Get inspections
        cursor.execute('''
            SELECT * FROM inspection_history 
            WHERE drive_id = ? 
            ORDER BY timestamp DESC
        ''', (drive_id,))
        inspections = cursor.fetchall()
        
        # Get test runs
        cursor.execute('''
            SELECT * FROM test_runs 
            WHERE drive_id = ? 
            ORDER BY timestamp DESC
        ''', (drive_id,))
        tests = cursor.fetchall()
        
        return {
            'drive': dict(drive) if drive else None,
            'inspections': [dict(i) for i in inspections],
            'tests': [dict(t) for t in tests]
        }
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()


# ============================================================================
# MENU SYSTEM
# ============================================================================
