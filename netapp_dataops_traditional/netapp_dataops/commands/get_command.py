"""
Get command module for NetApp DataOps Toolkit CLI.
"""

import getopt
import sys
from .base_command import BaseCommand
from netapp_dataops.help_text import (
    HELP_TEXT_GET_FLEXCACHE_ORIGIN
)
from netapp_dataops.traditional import (
    get_flexcache_origin,
    InvalidConfigError,
    APIConnectionError,
    InvalidVolumeParameterError
)


class GetCommand(BaseCommand):
    """Handle get command requests."""
    
    def execute(self) -> None:
        """Execute get command for various targets."""
        # Get desired target from command line args
        target = self.get_target()
        
        # Route to appropriate handler based on target
        if target in ("flexcache-origin", "fco"):
            self._get_flexcache_origin()
        else:
            self.handle_invalid_command()
    
    def _get_flexcache_origin(self) -> None:
        """Handle FlexCache origin retrieval."""
        volume_name = None
        svm_name = None
        cluster_name = None
        
        # Get command line options
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hn:s:u:", 
                ["help", "volume-name=", "svm=", "cluster-name="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_GET_FLEXCACHE_ORIGIN, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_GET_FLEXCACHE_ORIGIN)
                return
            elif opt in ("-n", "--volume-name"):
                volume_name = arg
            elif opt in ("-s", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        # Check for required options
        if not volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_GET_FLEXCACHE_ORIGIN, invalid_opt_arg=True)
        
        # Get FlexCache origin
        try:
            get_flexcache_origin(
                volume_name=volume_name,
                svm_name=svm_name,
                cluster_name=cluster_name,
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            sys.exit(1)
