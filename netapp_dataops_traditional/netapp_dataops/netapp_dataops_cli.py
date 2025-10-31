#!/usr/bin/env python3

import sys

# Only import what's needed for the main CLI
from netapp_dataops.help_text import HELP_TEXT_STANDARD


def handleInvalidCommand(helpText: str = HELP_TEXT_STANDARD, invalidOptArg: bool = False):
    """Handle invalid command scenarios and exit."""
    if invalidOptArg:
        print("Error: Invalid option/argument.")
    else:
        print("Error: Invalid command.")
    print(helpText)
    sys.exit(1)


## Main function
if __name__ == '__main__':
    # Get desired action from command line args
    try:
        action = sys.argv[1]
    except:
        handleInvalidCommand()

    # Used Command Pattern and Factory Pattern
    try:
        from netapp_dataops.commands import CommandFactory
        
        # Create command instance using factory
        command = CommandFactory.create_command(action, sys.argv)
        
        if command:
            command.execute()
        else:
            handleInvalidCommand()
            
    except ImportError:
        handleInvalidCommand()

