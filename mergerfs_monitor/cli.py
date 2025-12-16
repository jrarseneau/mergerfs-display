"""
Command-line interface for MergerFS Pool Monitor.
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box
from typing import List, Dict
from .config import Config
from .mergerfs import MergerFSPool
from .disk_info import DiskInfo


class CLI:
    """Command-line interface handler."""

    def __init__(self, config: Config):
        """
        Initialize CLI.

        Args:
            config: Configuration object
        """
        self.config = config
        self.console = Console()

    def display_pools(self):
        """Display all configured pools in formatted tables."""
        pools = self.config.get_pools()

        if not pools:
            self.console.print("[red]No pools configured![/red]")
            return

        for pool_config in pools:
            self._display_pool(pool_config)

    def _display_pool(self, pool_config: Dict[str, str]):
        """
        Display information for a single pool.

        Args:
            pool_config: Pool configuration dictionary
        """
        pool_name = pool_config['name']
        pool_path = pool_config['path']

        self.console.print()  # Empty line
        self.console.print(Panel(
            f"[bold cyan]{pool_name}[/bold cyan]\n[dim]{pool_path}[/dim]",
            box=box.ROUNDED
        ))

        try:
            # Get MergerFS branches
            pool = MergerFSPool(pool_path)
            branches = pool.get_branches()

            if not branches:
                self.console.print("[yellow]No branches found for this pool.[/yellow]")
                return

            # Create table
            table = Table(
                show_header=True,
                header_style="bold magenta",
                box=box.ROUNDED,
                show_lines=True
            )

            # Add columns
            table.add_column("Branch", style="cyan", no_wrap=False)
            table.add_column("Physical Disk", style="blue")
            table.add_column("Temp", justify="right", style="yellow")
            table.add_column("Size", justify="right", style="green")
            table.add_column("Used Space", justify="right", style="red")
            table.add_column("Free Space", justify="right", style="green")
            table.add_column("Free %", justify="right", style="bright_green")

            # Collect and display branch information
            for branch in branches:
                info = DiskInfo.get_branch_info(branch)

                # Format free percentage with color coding
                free_percent = info['free_percent']
                if free_percent > 20:
                    free_color = "green"
                elif free_percent > 10:
                    free_color = "yellow"
                else:
                    free_color = "red"

                free_percent_str = f"[{free_color}]{free_percent:.1f}%[/{free_color}]"

                # Add row to table
                table.add_row(
                    info['branch'],
                    info['physical_disk'],
                    info['temperature_str'],
                    info['size_str'],
                    info['used_str'],
                    info['free_str'],
                    free_percent_str
                )

            # Display table
            self.console.print(table)

            # Summary statistics
            self._display_pool_summary(branches)

        except ValueError as e:
            self.console.print(f"[red]Error:[/red] {str(e)}")
        except Exception as e:
            self.console.print(f"[red]Unexpected error:[/red] {str(e)}")

    def _display_pool_summary(self, branches: List[str]):
        """
        Display summary statistics for a pool.

        Args:
            branches: List of branch paths
        """
        total_space = 0
        total_used = 0
        total_free = 0
        valid_branches = 0

        for branch in branches:
            info = DiskInfo.get_branch_info(branch)
            if info['exists'] and info['total'] > 0:
                total_space += info['total']
                total_used += info['used']
                total_free += info['free']
                valid_branches += 1

        if valid_branches > 0:
            total_percent_used = (total_used / total_space * 100) if total_space > 0 else 0
            total_percent_free = 100 - total_percent_used

            summary = Table.grid(padding=(0, 2))
            summary.add_column(style="bold")
            summary.add_column(justify="right")

            summary.add_row("Total Branches:", f"{len(branches)}")
            summary.add_row("Total Space:", DiskInfo.format_bytes(total_space))
            summary.add_row("Total Used:", DiskInfo.format_bytes(total_used))
            summary.add_row("Total Free:", DiskInfo.format_bytes(total_free))
            summary.add_row("Overall Free:", f"{total_percent_free:.1f}%")

            self.console.print()
            self.console.print(Panel(summary, title="[bold]Pool Summary[/bold]", box=box.ROUNDED))
