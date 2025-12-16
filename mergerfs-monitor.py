#!/usr/bin/env python3
"""
MergerFS Pool Monitor - Main entry point

A sophisticated tool for monitoring MergerFS pools and their underlying disks.
Supports both command-line and web interfaces.
"""

import sys
import click
from pathlib import Path

from mergerfs_monitor.config import Config
from mergerfs_monitor.cli import CLI
from mergerfs_monitor.web import run_web_server


@click.group(invoke_without_command=True)
@click.option(
    '--config',
    '-c',
    default='config.yaml',
    help='Path to configuration file',
    type=click.Path(exists=True)
)
@click.pass_context
def main(ctx, config):
    """
    MergerFS Pool Monitor - Monitor your MergerFS pools and disks.

    Run without a subcommand to display pools in CLI mode.
    Use 'web' subcommand to start the web interface.
    """
    # Store config path in context
    ctx.ensure_object(dict)
    ctx.obj['config_path'] = config

    # If no subcommand is provided, run CLI by default
    if ctx.invoked_subcommand is None:
        show_cli(config)


@main.command()
@click.option(
    '--config',
    '-c',
    default='config.yaml',
    help='Path to configuration file',
    type=click.Path(exists=True)
)
def cli(config):
    """Display pool information in the command line (default)."""
    show_cli(config)


@main.command()
@click.option(
    '--config',
    '-c',
    default='config.yaml',
    help='Path to configuration file',
    type=click.Path(exists=True)
)
@click.option(
    '--port',
    '-p',
    default=None,
    type=int,
    help='Port to run the web server on (overrides config file)'
)
@click.option(
    '--host',
    '-h',
    default=None,
    help='Host to bind the web server to (overrides config file)'
)
def web(config, port, host):
    """Start the web interface."""
    try:
        cfg = Config(config)

        # Override config with command-line options if provided
        if port is not None or host is not None:
            web_config = cfg.get_web_config()
            if port is not None:
                web_config['port'] = port
            if host is not None:
                web_config['host'] = host

            # Temporarily override config
            cfg.config_data['web'] = web_config

        run_web_server(cfg)

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except KeyboardInterrupt:
        click.echo("\n\n👋 Shutting down web server...")
        sys.exit(0)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


def show_cli(config_path):
    """
    Display pool information in CLI mode.

    Args:
        config_path: Path to configuration file
    """
    try:
        config = Config(config_path)
        cli_handler = CLI(config)
        cli_handler.display_pools()

    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
    except ValueError as e:
        click.echo(f"Configuration error: {e}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main(obj={})
