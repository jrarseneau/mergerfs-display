"""
MergerFS pool information retrieval.
"""

import xattr
import os
from pathlib import Path
from typing import List, Optional


class MergerFSPool:
    """Represents a MergerFS pool and its branches."""

    def __init__(self, pool_path: str):
        """
        Initialize a MergerFS pool.

        Args:
            pool_path: Path to the MergerFS mount point
        """
        self.pool_path = Path(pool_path)
        self.branches = self._get_branches()

    def _get_branches(self) -> List[str]:
        """
        Get the list of branches for this MergerFS pool.

        Returns:
            List of branch paths
        """
        # First verify the pool path itself exists
        if not self.pool_path.exists():
            raise ValueError(
                f"Pool path does not exist: {self.pool_path}\n"
                f"Please verify the path in your configuration file."
            )

        if not self.pool_path.is_dir():
            raise ValueError(
                f"Pool path is not a directory: {self.pool_path}\n"
                f"Please provide a valid MergerFS mount point."
            )

        # .mergerfs is a special MergerFS control interface, not a real file
        # We need to construct the path as a string to access the virtual control interface
        mergerfs_control = os.path.join(str(self.pool_path), ".mergerfs")

        try:
            # Get the user.mergerfs.branches extended attribute
            branches_attr = xattr.getxattr(
                mergerfs_control,
                "user.mergerfs.branches"
            )

            # Decode and split the branches
            branches_str = branches_attr.decode('utf-8')
            branches = [b.strip() for b in branches_str.split(':') if b.strip()]

            if not branches:
                raise ValueError(f"No branches found for pool: {self.pool_path}")

            return branches

        except OSError as e:
            raise ValueError(
                f"Failed to read MergerFS branches from {mergerfs_control}: {e}\n"
                f"Actual path attempted: {mergerfs_control}\n"
                f"This could mean:\n"
                f"  1. The path is not a MergerFS mount\n"
                f"  2. You don't have permission to access extended attributes\n"
                f"  3. MergerFS is not running or configured properly\n"
                f"Try running: xattr -l {mergerfs_control}"
            )

    def get_branches(self) -> List[str]:
        """
        Get the list of branch paths.

        Returns:
            List of branch paths
        """
        return self.branches

    def get_branch_exists(self, branch: str) -> bool:
        """
        Check if a branch path exists.

        Args:
            branch: Branch path to check

        Returns:
            True if the branch exists, False otherwise
        """
        return Path(branch).exists()
