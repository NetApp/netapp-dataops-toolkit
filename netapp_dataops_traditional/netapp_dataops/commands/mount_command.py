"""
Mount command module for NetApp DataOps Toolkit CLI.
"""

import getopt
from .base_command import BaseCommand
from netapp_dataops.help_text import HELP_TEXT_MOUNT_VOLUME
from netapp_dataops.traditional import (
    mount_volume,
    InvalidConfigError,
    APIConnectionError,
    InvalidVolumeParameterError,
    MountOperationError
)


class MountCommand(BaseCommand):
    """Handle mount command requests."""
    
    def execute(self) -> None:
        """Execute mount command for volumes."""
        # Get desired target from command line args
        target = self.get_target()
        
        if target in ("volume", "vol"):
            self._mount_volume()
        else:
            self.handle_invalid_command()
    
    def _mount_volume(self) -> None:
        """Handle volume mounting."""
        # Initialize variables
        volume_name = None
        svm_name = None
        cluster_name = None
        lif_name = None
        mountpoint = None
        mount_options = None
        readonly = False
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hv:n:l:m:u:o:x", 
                ["cluster-name=", "help", "lif=", "svm=", "name=", "mountpoint=", "readonly", "options="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_MOUNT_VOLUME, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_MOUNT_VOLUME)
                return
            elif opt in ("-v", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-l", "--lif"):
                lif_name = arg
            elif opt in ("-n", "--name"):
                volume_name = arg
            elif opt in ("-m", "--mountpoint"):
                mountpoint = arg
            elif opt in ("-o", "--options"):
                mount_options = arg
            elif opt in ("-x", "--readonly"):
                readonly = True
        
        # Check for required options
        if not volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_MOUNT_VOLUME, invalid_opt_arg=True)
        
        if not mountpoint:
            self.handle_invalid_command(help_text=HELP_TEXT_MOUNT_VOLUME, invalid_opt_arg=True)
        
        # Mount volume
        try:
            mount_volume(
                svm_name=svm_name, 
                cluster_name=cluster_name, 
                lif_name=lif_name, 
                volume_name=volume_name, 
                mountpoint=mountpoint, 
                mount_options=mount_options, 
                readonly=readonly, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
            import sys
            sys.exit(1)
