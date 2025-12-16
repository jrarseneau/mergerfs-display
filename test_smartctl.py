#!/usr/bin/env python3
"""
Test script to debug smartctl disk size detection.
Run this with: sudo python3 test_smartctl.py /dev/disk/by-id/your-device-path
"""

import sys
import subprocess
import re

def test_smartctl(device):
    """Test smartctl -i on a device and show debug output."""
    print(f"=" * 80)
    print(f"Testing smartctl on device: {device}")
    print(f"=" * 80)

    try:
        print("\n1. Running smartctl -i command...")
        result = subprocess.run(
            ['smartctl', '-i', device],
            capture_output=True,
            text=True,
            timeout=10
        )

        print(f"\n2. Return code: {result.returncode}")

        if result.returncode > 64:
            print(f"   WARNING: Return code {result.returncode} > 64 - would return None")
        else:
            print(f"   OK: Return code acceptable (0-64)")

        print(f"\n3. STDERR output ({len(result.stderr)} chars):")
        if result.stderr:
            print("   " + result.stderr.replace("\n", "\n   "))
        else:
            print("   (empty)")

        print(f"\n4. STDOUT output ({len(result.stdout)} chars):")
        print("   " + result.stdout.replace("\n", "\n   "))

        print(f"\n5. Searching for User Capacity...")
        found_capacity = False
        for line in result.stdout.split('\n'):
            if 'capacity' in line.lower():
                print(f"   Found capacity line: {line.strip()}")

                if 'User Capacity:' in line or 'user capacity:' in line.lower():
                    found_capacity = True
                    print(f"   ✓ MATCHED User Capacity line!")

                    # Try to extract bytes
                    match = re.search(r'([\d,]+)\s+bytes', line, re.IGNORECASE)
                    if match:
                        bytes_str = match.group(1).replace(',', '').replace(' ', '')
                        print(f"   → Extracted bytes string: {bytes_str}")
                        try:
                            size = int(bytes_str)
                            size_tb = size / (1024**4)
                            print(f"   → Parsed size: {size} bytes ({size_tb:.2f} TiB)")
                            print(f"\n6. SUCCESS! Would return: {size} bytes")
                            return size
                        except ValueError as e:
                            print(f"   → Failed to parse: {e}")

                    # Try TB fallback
                    match = re.search(r'\[(\d+(?:\.\d+)?)\s*TB\]', line, re.IGNORECASE)
                    if match:
                        tb_value = float(match.group(1))
                        size = int(tb_value * 1000 * 1000 * 1000 * 1000)
                        size_tib = size / (1024**4)
                        print(f"   → Extracted TB value: {tb_value} TB")
                        print(f"   → Converted to: {size} bytes ({size_tib:.2f} TiB)")
                        print(f"\n6. SUCCESS! Would return: {size} bytes")
                        return size

        if not found_capacity:
            print("   ✗ No User Capacity line found")
            print(f"\n6. FAILURE! Would return None")
            return None

    except subprocess.TimeoutExpired:
        print("\n   ✗ Command timed out!")
        return None
    except FileNotFoundError:
        print("\n   ✗ smartctl command not found!")
        return None
    except Exception as e:
        print(f"\n   ✗ Exception: {type(e).__name__}: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: sudo python3 test_smartctl.py /dev/disk/by-id/your-device")
        print("\nExample:")
        print("  sudo python3 test_smartctl.py /dev/disk/by-id/ata-ST16000NM001G-2KK103_ZL267HW4")
        sys.exit(1)

    device = sys.argv[1]
    result = test_smartctl(device)

    if result:
        print(f"\n{'='*80}")
        print(f"RESULT: Function would return {result} bytes")
        print(f"        = {result / (1024**4):.2f} TiB")
        print(f"        = {result / (1000**4):.2f} TB")
        print(f"{'='*80}")
    else:
        print(f"\n{'='*80}")
        print(f"RESULT: Function would return None")
        print(f"{'='*80}")
