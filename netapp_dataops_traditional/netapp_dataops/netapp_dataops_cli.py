"""CLI entry point for NetApp DataOps Toolkit."""

import sys

from netapp_dataops.commands import CommandFactory
from netapp_dataops.help_text import HELP_TEXT_STANDARD
from netapp_dataops.logging_utils import setup_logger
from netapp_dataops.constants import KEYRING_SERVICE_NAME

logger = setup_logger(__name__)

if __name__ == '__main__':
    try:
        action = sys.argv[1]
    except IndexError:
        logger.error("Error: Invalid command.")
        logger.error(HELP_TEXT_STANDARD)
        sys.exit(1)
    
    command = CommandFactory.create_command(action, sys.argv)
    
    if command:
        command.execute()
    else:
        logger.error("Error: Invalid command.")
        logger.error(HELP_TEXT_STANDARD)
        sys.exit(1)
