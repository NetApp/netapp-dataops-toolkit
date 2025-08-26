"""
Unmount command module for NetApp DataOps Toolkit CLI.
"""

import getopt
from .base_command import BaseCommand
from netapp_dataops.help_text import HELP_TEXT_UNMOUNT_VOLUME
from netapp_dataops.traditional import unmount_volume, MountOperationError


class UnmountCommand(BaseCommand):
    """Handle unmount command requests."""
    
    def execute(self) -> None:
        """Execute unmount command for volumes."""
        # Get desired target from command line args
        target = self.get_target()
        
        if target in ("volume", "vol"):
            self._unmount_volume()
        else:
            self.handle_invalid_command()
    
    def _unmount_volume(self) -> None:
        """Handle volume unmounting."""
        mountpoint = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hm:", 
                ["help", "mountpoint="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_UNMOUNT_VOLUME, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_UNMOUNT_VOLUME)
                return
            elif opt in ("-m", "--mountpoint"):
                mountpoint = arg
        
        # Check for required options
        if not mountpoint:
            self.handle_invalid_command(help_text=HELP_TEXT_UNMOUNT_VOLUME, invalid_opt_arg=True)
        
        # Unmount volume
        try:
            unmount_volume(mountpoint=mountpoint, print_output=True)
        except MountOperationError:
            import sys
            sys.exit(1)
