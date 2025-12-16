"""
Disk information collector for branches.
"""

import os
import re
import subprocess
import psutil
from pathlib import Path
from typing import Dict, Optional, Tuple


class DiskInfo:
    """Collects information about disks and branches."""

    @staticmethod
    def get_physical_disk(path: str) -> Optional[str]:
        """
        Determine the physical disk device for a given path.
        Supports ZFS pools, device mappers, and standard block devices.

        Args:
            path: Path to check

        Returns:
            Physical disk device (e.g., /dev/sda or disk model) or None if not found
        """
        try:
            # First check if this is a ZFS filesystem
            zfs_disk = DiskInfo._get_zfs_physical_disk(path)
            if zfs_disk:
                return zfs_disk

            # Use df to find the device
            result = subprocess.run(
                ['df', path],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse df output to get the device
            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return None

            device = lines[1].split()[0]

            # Handle various device naming schemes
            # /dev/sda1 -> /dev/sda
            # /dev/nvme0n1p1 -> /dev/nvme0n1
            # /dev/mapper/xxx or /dev/dm-X -> try to resolve to physical disk
            if device.startswith('/dev/mapper/') or device.startswith('/dev/dm-'):
                # Try to get the underlying device
                physical = DiskInfo._resolve_device_mapper(device)
                if physical:
                    return physical

            # Strip partition numbers for standard disks
            # Match patterns like sda1, nvme0n1p1, mmcblk0p1, etc.
            match = re.match(r'(/dev/[a-z]+)', device)
            if match:
                return match.group(1)

            # For NVMe devices
            match = re.match(r'(/dev/nvme\d+n\d+)', device)
            if match:
                return match.group(1)

            # For MMC devices
            match = re.match(r'(/dev/mmcblk\d+)', device)
            if match:
                return match.group(1)

            # If we can't determine, return the device as-is
            return device

        except (subprocess.CalledProcessError, IndexError, Exception):
            return None

    @staticmethod
    def _resolve_disk_by_id(disk_name: str) -> Optional[str]:
        """
        Resolve a disk name to a /dev/disk/by-id/ path.

        Args:
            disk_name: Disk model/serial name (e.g., ST16000NM001G-2KK103_ZL267HW4)

        Returns:
            Path to /dev/disk/by-id/ device or None
        """
        try:
            by_id_path = Path('/dev/disk/by-id')
            if not by_id_path.exists():
                return None

            # Look for a device that contains the disk name
            # Prefer devices without partition suffixes
            candidates = []
            for device_link in by_id_path.iterdir():
                link_name = device_link.name

                if disk_name in link_name:
                    # Skip partition links (ending with -partN or -pN)
                    if re.search(r'-part\d+$', link_name) or re.search(r'-p\d+$', link_name):
                        continue

                    # This is a candidate (non-partition device)
                    candidates.append(str(device_link))

            # Return the shortest matching candidate (most likely to be the base device)
            if candidates:
                return min(candidates, key=len)

        except Exception:
            pass

        return None

    @staticmethod
    def _get_zfs_disk_device_for_temp(path: str) -> Optional[str]:
        """
        Get the device path for temperature monitoring of a ZFS disk.

        Args:
            path: Path to check

        Returns:
            Device path suitable for smartctl or None if not ZFS
        """
        try:
            # Check if the path is on a ZFS filesystem
            result = subprocess.run(
                ['df', '-T', path],
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return None

            # Check if filesystem type is ZFS
            parts = lines[1].split()
            if len(parts) < 2 or parts[1] != 'zfs':
                return None

            # Get the ZFS pool name (first part before /)
            filesystem = parts[0]
            pool_name = filesystem.split('/')[0]

            # Get the physical device from zpool status
            zpool_result = subprocess.run(
                ['zpool', 'status', pool_name],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse zpool status output to find the physical device
            lines = zpool_result.stdout.split('\n')
            in_config = False

            for line in lines:
                if 'config:' in line.lower():
                    in_config = True
                    continue

                if in_config and line.strip():
                    if 'NAME' in line and 'STATE' in line:
                        continue

                    stripped = line.strip()
                    if stripped and not stripped.startswith('errors:'):
                        parts = stripped.split()
                        if len(parts) >= 1:
                            device_name = parts[0]

                            # Skip the pool name itself and special vdev types
                            if device_name in [pool_name, 'mirror', 'raidz', 'raidz1', 'raidz2', 'raidz3', 'cache', 'log', 'spare']:
                                continue

                            # Found a physical device - return it with full path
                            # Try /dev/disk/by-id/ first (preserving full name)
                            by_id_device = f"/dev/disk/by-id/{device_name}"
                            if Path(by_id_device).exists():
                                return by_id_device

                            # If that doesn't exist, try stripping -part suffix
                            device_without_part = re.sub(r'-part\d+$', '', device_name)
                            by_id_device_no_part = f"/dev/disk/by-id/{device_without_part}"
                            if Path(by_id_device_no_part).exists():
                                return by_id_device_no_part

            return None

        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            return None

    @staticmethod
    def _get_zfs_physical_disk(path: str) -> Optional[str]:
        """
        Get the physical disk for a ZFS filesystem.

        Args:
            path: Path to check

        Returns:
            Cleaned physical disk name or None if not ZFS
        """
        try:
            # Check if the path is on a ZFS filesystem
            result = subprocess.run(
                ['df', '-T', path],
                capture_output=True,
                text=True,
                check=True
            )

            lines = result.stdout.strip().split('\n')
            if len(lines) < 2:
                return None

            # Check if filesystem type is ZFS
            parts = lines[1].split()
            if len(parts) < 2:
                return None

            fs_type = parts[1]
            if fs_type != 'zfs':
                return None

            # Get the ZFS pool name (first part before /)
            filesystem = parts[0]
            pool_name = filesystem.split('/')[0]

            # Get the physical device from zpool status
            zpool_result = subprocess.run(
                ['zpool', 'status', pool_name],
                capture_output=True,
                text=True,
                check=True
            )

            # Parse zpool status output to find the physical device
            # Example output:
            #   disk1                                      ONLINE       0     0     0
            #     ata-ST16000NM001G-2KK103_ZL267HW4-part1  ONLINE       0     0     0
            lines = zpool_result.stdout.split('\n')
            in_config = False
            devices = []

            for line in lines:
                if 'config:' in line.lower():
                    in_config = True
                    continue

                if in_config and line.strip():
                    # Look for device lines (indented with device names)
                    # Skip lines with NAME, STATE, READ, WRITE, CKSUM headers
                    if 'NAME' in line and 'STATE' in line:
                        continue

                    # Match lines that look like devices
                    stripped = line.strip()
                    if stripped and not stripped.startswith('errors:'):
                        parts = stripped.split()
                        if len(parts) >= 1:
                            device_name = parts[0]

                            # Skip the pool name itself and special vdev types
                            if device_name in [pool_name, 'mirror', 'raidz', 'raidz1', 'raidz2', 'raidz3', 'cache', 'log', 'spare']:
                                continue

                            # This looks like a physical device
                            devices.append(device_name)

            if not devices:
                return None

            # Take the first device and clean it up
            device = devices[0]

            # Strip partition suffixes like -part1, -part2, p1, p2, etc.
            device = re.sub(r'-part\d+$', '', device)
            device = re.sub(r'p\d+$', '', device)

            # Strip disk type prefixes like ata-, scsi-, nvme-, etc.
            device = re.sub(r'^(ata|scsi|nvme|usb|wwn)-', '', device)

            return device

        except (subprocess.CalledProcessError, FileNotFoundError, Exception):
            return None

    @staticmethod
    def _resolve_device_mapper(device: str) -> Optional[str]:
        """
        Resolve a device mapper device to its underlying physical device.

        Args:
            device: Device mapper path (e.g., /dev/mapper/xxx or /dev/dm-X)

        Returns:
            Physical device path or None
        """
        try:
            # Try to use dmsetup to find the underlying device
            if device.startswith('/dev/mapper/'):
                # Get the dm device name
                dm_name = device.replace('/dev/mapper/', '')
                result = subprocess.run(
                    ['dmsetup', 'deps', '-o', 'devname', dm_name],
                    capture_output=True,
                    text=True
                )
                if result.returncode == 0:
                    # Parse output like: 1 dependencies : (sda1)
                    match = re.search(r'\(([^)]+)\)', result.stdout)
                    if match:
                        dep_device = match.group(1)
                        # Strip partition number
                        base_match = re.match(r'([a-z]+)\d*', dep_device)
                        if base_match:
                            return f"/dev/{base_match.group(1)}"

            # Alternative: read from sysfs
            if device.startswith('/dev/dm-'):
                dm_num = device.replace('/dev/dm-', '')
                slaves_path = f"/sys/block/dm-{dm_num}/slaves"
                if os.path.exists(slaves_path):
                    slaves = os.listdir(slaves_path)
                    if slaves:
                        # Get the first slave device
                        slave = slaves[0]
                        # Strip partition number
                        base_match = re.match(r'([a-z]+)\d*', slave)
                        if base_match:
                            return f"/dev/{base_match.group(1)}"

        except Exception:
            pass

        return None

    @staticmethod
    def get_disk_usage(path: str) -> Optional[Dict[str, any]]:
        """
        Get disk usage statistics for a path.

        Args:
            path: Path to check

        Returns:
            Dictionary with total, used, free (in bytes), and percent used
        """
        try:
            usage = psutil.disk_usage(path)
            return {
                'total': usage.total,
                'used': usage.used,
                'free': usage.free,
                'percent': usage.percent
            }
        except Exception:
            return None

    @staticmethod
    def get_disk_temperature(device: str) -> Optional[float]:
        """
        Get the temperature of a disk device.

        Args:
            device: Physical disk device (e.g., /dev/sda)

        Returns:
            Temperature in Celsius or None if not available
        """
        # Try smartctl first
        temp = DiskInfo._get_temperature_smartctl(device)
        if temp is not None:
            return temp

        # Try sysfs hwmon as fallback
        temp = DiskInfo._get_temperature_sysfs(device)
        if temp is not None:
            return temp

        return None

    @staticmethod
    def _get_temperature_smartctl(device: str) -> Optional[float]:
        """
        Get disk temperature using smartctl.

        Args:
            device: Physical disk device

        Returns:
            Temperature in Celsius or None
        """
        try:
            result = subprocess.run(
                ['smartctl', '-A', device],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode not in [0, 4]:  # 0 = success, 4 = success with previous errors
                return None

            # Parse smartctl output for temperature
            # Look for lines like: "194 Temperature_Celsius     0x0022   042   055   000    Old_age   Always       -       42"
            # or "Temperature:" lines
            for line in result.stdout.split('\n'):
                # Match Temperature_Celsius attribute
                if 'Temperature_Celsius' in line:
                    parts = line.split()
                    if len(parts) >= 10:
                        try:
                            return float(parts[9])
                        except ValueError:
                            pass

                # Match "Temperature:" line
                if line.strip().startswith('Temperature:'):
                    match = re.search(r'(\d+)\s*Celsius', line)
                    if match:
                        return float(match.group(1))

                # Match "Current Drive Temperature:" line
                if 'Current Drive Temperature:' in line:
                    match = re.search(r'(\d+)\s*C', line)
                    if match:
                        return float(match.group(1))

        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            pass

        return None

    @staticmethod
    def _get_temperature_sysfs(device: str) -> Optional[float]:
        """
        Get disk temperature from sysfs hwmon.

        Args:
            device: Physical disk device

        Returns:
            Temperature in Celsius or None
        """
        try:
            # Extract device name (e.g., sda from /dev/sda)
            dev_name = os.path.basename(device)

            # Look in /sys/class/hwmon for temperature sensors
            hwmon_path = Path('/sys/class/hwmon')
            if not hwmon_path.exists():
                return None

            for hwmon_dir in hwmon_path.iterdir():
                if not hwmon_dir.is_dir():
                    continue

                # Check if this hwmon device is associated with our disk
                name_file = hwmon_dir / 'name'
                if name_file.exists():
                    name = name_file.read_text().strip()
                    if dev_name in name or name in dev_name:
                        # Look for temp*_input files
                        for temp_file in hwmon_dir.glob('temp*_input'):
                            temp_millidegrees = int(temp_file.read_text().strip())
                            return temp_millidegrees / 1000.0

        except Exception:
            pass

        return None

    @staticmethod
    def format_bytes(bytes_value: int) -> str:
        """
        Format bytes into human-readable format.

        Args:
            bytes_value: Number of bytes

        Returns:
            Formatted string (e.g., "1.5 TB")
        """
        for unit in ['B', 'KB', 'MB', 'GB', 'TB', 'PB']:
            if bytes_value < 1024.0:
                return f"{bytes_value:.2f} {unit}"
            bytes_value /= 1024.0
        return f"{bytes_value:.2f} EB"

    @staticmethod
    def get_branch_info(branch_path: str) -> Dict[str, any]:
        """
        Get comprehensive information about a branch.

        Args:
            branch_path: Path to the branch

        Returns:
            Dictionary with branch information
        """
        info = {
            'branch': branch_path,
            'physical_disk': 'N/A',
            'temperature': None,
            'temperature_str': 'N/A',
            'total': 0,
            'used': 0,
            'free': 0,
            'percent_used': 0,
            'total_str': 'N/A',
            'used_str': 'N/A',
            'free_str': 'N/A',
            'free_percent': 0,
            'exists': os.path.exists(branch_path)
        }

        if not info['exists']:
            return info

        # Get physical disk
        physical_disk = DiskInfo.get_physical_disk(branch_path)
        if physical_disk:
            info['physical_disk'] = physical_disk

            # Get temperature
            # Try direct ZFS device resolution first (most reliable for ZFS)
            temp_device = DiskInfo._get_zfs_disk_device_for_temp(branch_path)

            # If not ZFS or resolution failed, fall back to standard resolution
            if not temp_device:
                temp_device = physical_disk
                if not physical_disk.startswith('/dev/'):
                    # Try to find the device in /dev/disk/by-id/
                    resolved = DiskInfo._resolve_disk_by_id(physical_disk)
                    if resolved:
                        temp_device = resolved

            if temp_device:
                temp = DiskInfo.get_disk_temperature(temp_device)
                if temp is not None:
                    info['temperature'] = temp
                    info['temperature_str'] = f"{temp:.1f}°C"

        # Get disk usage
        usage = DiskInfo.get_disk_usage(branch_path)
        if usage:
            info['total'] = usage['total']
            info['used'] = usage['used']
            info['free'] = usage['free']
            info['percent_used'] = usage['percent']
            info['free_percent'] = 100 - usage['percent']

            info['total_str'] = DiskInfo.format_bytes(usage['total'])
            info['used_str'] = DiskInfo.format_bytes(usage['used'])
            info['free_str'] = DiskInfo.format_bytes(usage['free'])

        return info
