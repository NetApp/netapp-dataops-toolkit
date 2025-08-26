"""
Prepopulate command module for NetApp DataOps Toolkit CLI.
"""

import getopt
from .base_command import BaseCommand
from netapp_dataops.help_text import HELP_TEXT_PREPOPULATE_FLEXCACHE
from netapp_dataops.traditional import (
    prepopulate_flex_cache,
    InvalidConfigError,
    APIConnectionError,
    InvalidVolumeParameterError
)


class PrepopulateCommand(BaseCommand):
    """Handle prepopulate command requests."""
    
    def execute(self) -> None:
        """Execute prepopulate command for FlexCache."""
        # Get desired target from command line args
        target = self.get_target()
        
        if target in ("flexcache", "cache"):
            self._prepopulate_flexcache()
        else:
            self.handle_invalid_command()
    
    def _prepopulate_flexcache(self) -> None:
        """Handle FlexCache prepopulation."""
        volume_name = None
        paths = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hn:p:", 
                ["help", "name=", "paths="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_PREPOPULATE_FLEXCACHE, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_PREPOPULATE_FLEXCACHE)
                return
            elif opt in ("-n", "--name"):
                volume_name = arg
            elif opt in ("-p", "--paths"):
                paths = arg
        
        # Check for required options
        if not volume_name or not paths:
            self.handle_invalid_command(help_text=HELP_TEXT_PREPOPULATE_FLEXCACHE, invalid_opt_arg=True)
        
        # Convert paths string to list
        paths_list = paths.split(",")
        
        # Prepopulate FlexCache
        try:
            prepopulate_flex_cache(
                volume_name=volume_name, 
                paths=paths_list, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            import sys
            sys.exit(1)
