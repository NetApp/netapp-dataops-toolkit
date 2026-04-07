"""Unmount command module for NetApp DataOps Toolkit CLI."""

import getopt
import sys
from .base_command import BaseCommand, logger
from netapp_dataops.help_text import HELP_TEXT_UNMOUNT_VOLUME
from netapp_dataops.traditional import unmount_volume, MountOperationError


class UnmountCommand(BaseCommand):
    """Handle unmount command requests."""
    
    def execute(self) -> None:
        """Execute unmount command for volumes."""
        target = self.get_target()
        
        if target in ("volume", "vol"):
            self._unmount_volume()
        else:
            self.handle_invalid_command()
    
    def _unmount_volume(self) -> None:
        """Handle volume unmounting."""
        mountpoint = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hm:", 
                ["help", "mountpoint="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_UNMOUNT_VOLUME, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_UNMOUNT_VOLUME)
                return
            elif opt in ("-m", "--mountpoint"):
                mountpoint = arg
        
        if not mountpoint:
            self.handle_invalid_command(help_text=HELP_TEXT_UNMOUNT_VOLUME, invalid_opt_arg=True)
        
        try:
            unmount_volume(mountpoint=mountpoint, print_output=True)
        except MountOperationError:
            sys.exit(1)
