"""
Configuration file parser for MergerFS Pool Monitor.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any


class Config:
    """Configuration manager for the application."""

    def __init__(self, config_path: str = "config.yaml"):
        """
        Initialize configuration from a YAML file.

        Args:
            config_path: Path to the configuration file
        """
        self.config_path = Path(config_path)
        self.config_data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load and parse the YAML configuration file."""
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_path}\n"
                f"Please create a config.yaml file. See config.example.yaml for reference."
            )

        with open(self.config_path, 'r') as f:
            config = yaml.safe_load(f)

        # Validate required fields
        if not config or 'pools' not in config:
            raise ValueError("Configuration must contain 'pools' section")

        if not isinstance(config['pools'], list) or len(config['pools']) == 0:
            raise ValueError("Configuration must contain at least one pool")

        for pool in config['pools']:
            if 'path' not in pool:
                raise ValueError(f"Pool configuration missing 'path' field: {pool}")

        return config

    def get_pools(self) -> List[Dict[str, str]]:
        """
        Get list of configured pools.

        Returns:
            List of pool configurations with 'name' and 'path' keys
        """
        pools = []
        for idx, pool in enumerate(self.config_data['pools']):
            pools.append({
                'name': pool.get('name', f"Pool {idx + 1}"),
                'path': pool['path']
            })
        return pools

    def get_web_config(self) -> Dict[str, Any]:
        """
        Get web server configuration.

        Returns:
            Dictionary with 'host' and 'port' keys
        """
        web_config = self.config_data.get('web', {})
        return {
            'host': web_config.get('host', '0.0.0.0'),
            'port': web_config.get('port', 8090)
        }
