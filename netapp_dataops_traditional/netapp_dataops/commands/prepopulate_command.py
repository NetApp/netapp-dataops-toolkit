"""Prepopulate command module for NetApp DataOps Toolkit CLI."""

import getopt
import sys
from .base_command import BaseCommand, logger
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
        target = self.get_target()
        
        if target in ("flexcache", "cache"):
            self._prepopulate_flexcache()
        else:
            self.handle_invalid_command()
    
    def _prepopulate_flexcache(self) -> None:
        """Handle FlexCache prepopulation."""
        volume_name = None
        paths = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hn:p:", 
                ["help", "name=", "paths="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_PREPOPULATE_FLEXCACHE, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_PREPOPULATE_FLEXCACHE)
                return
            elif opt in ("-n", "--name"):
                volume_name = arg
            elif opt in ("-p", "--paths"):
                paths = arg
        
        if not volume_name or not paths:
            self.handle_invalid_command(help_text=HELP_TEXT_PREPOPULATE_FLEXCACHE, invalid_opt_arg=True)
        
        paths_list = paths.split(",")
        
        try:
            prepopulate_flex_cache(
                volume_name=volume_name, 
                paths=paths_list, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            sys.exit(1)
