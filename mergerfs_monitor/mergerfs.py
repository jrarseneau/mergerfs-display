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
        mergerfs_control = self.pool_path / ".mergerfs"

        if not mergerfs_control.exists():
            raise ValueError(
                f"Path does not appear to be a MergerFS mount: {self.pool_path}\n"
                f"Expected to find .mergerfs control file at: {mergerfs_control}"
            )

        try:
            # Get the user.mergerfs.branches extended attribute
            branches_attr = xattr.getxattr(
                str(mergerfs_control),
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
                f"Make sure this is a valid MergerFS mount and you have appropriate permissions."
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
