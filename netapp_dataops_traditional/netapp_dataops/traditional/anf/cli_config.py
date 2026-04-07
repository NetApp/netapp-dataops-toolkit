#!/usr/bin/env python3
"""
CLI entry point for ANF configuration wizard.

This script provides a clean entry point for running the ANF configuration
wizard without import conflicts.

Usage:
    python3 -m netapp_dataops.traditional.anf.cli_config
"""

import sys


def main():
    """Run the ANF configuration wizard."""
    try:
        from .config import create_anf_config_interactive
        create_anf_config_interactive()
    except KeyboardInterrupt:
        print("\n\nConfiguration cancelled by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\nError: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
