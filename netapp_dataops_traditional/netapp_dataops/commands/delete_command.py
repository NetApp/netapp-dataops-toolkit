"""Delete command module for NetApp DataOps Toolkit CLI."""

import getopt
import sys
from .base_command import BaseCommand, logger
from netapp_dataops.help_text import (
    HELP_TEXT_DELETE_SNAPSHOT,
    HELP_TEXT_DELETE_VOLUME
)
from netapp_dataops.traditional import (
    delete_snapshot,
    delete_volume,
    InvalidConfigError,
    APIConnectionError,
    InvalidSnapshotParameterError,
    InvalidVolumeParameterError
)


class DeleteCommand(BaseCommand):
    """Handle delete command requests."""
    
    def execute(self) -> None:
        """Execute delete command for various targets."""
        target = self.get_target()
        
        if target in ("snapshot", "snap"):
            self._delete_snapshot()
        elif target in ("volume", "vol"):
            self._delete_volume()
        else:
            self.handle_invalid_command()
    
    def _delete_snapshot(self) -> None:
        """Handle snapshot deletion."""
        volume_name = None
        snapshot_name = None
        svm_name = None
        cluster_name = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hn:v:s:u:", 
                ["cluster-name=", "help", "svm=", "name=", "volume="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_DELETE_SNAPSHOT, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_DELETE_SNAPSHOT)
                return
            elif opt in ("-n", "--name"):
                snapshot_name = arg
            elif opt in ("-s", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-v", "--volume"):
                volume_name = arg
        
        if not volume_name or not snapshot_name:
            self.handle_invalid_command(help_text=HELP_TEXT_DELETE_SNAPSHOT, invalid_opt_arg=True)
        
        try:
            delete_snapshot(
                volume_name=volume_name, 
                svm_name=svm_name, 
                cluster_name=cluster_name, 
                snapshot_name=snapshot_name, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidSnapshotParameterError, InvalidVolumeParameterError):
            sys.exit(1)
    
    def _delete_volume(self) -> None:
        """Handle volume deletion."""
        volume_name = None
        svm_name = None
        cluster_name = None
        force = False
        delete_mirror = False
        delete_non_clone = False
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hfv:n:u:m", 
                ["cluster-name=", "help", "svm=", "name=", "force", "delete-non-clone", "delete-mirror"]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_DELETE_VOLUME, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_DELETE_VOLUME)
                return
            elif opt in ("-v", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-n", "--name"):
                volume_name = arg
            elif opt in ("-f", "--force"):
                force = True
            elif opt in ("-m", "--delete-mirror"):
                delete_mirror = True
            elif opt in ("--delete-non-clone",):
                delete_non_clone = True
        
        if not volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_DELETE_VOLUME, invalid_opt_arg=True)
        
        if not force:
            logger.info("Warning: All data and snapshots associated with the volume will be permanently deleted.")
            while True:
                proceed = input("Are you sure that you want to proceed? (yes/no): ")
                if proceed in ("yes", "Yes", "YES"):
                    break
                elif proceed in ("no", "No", "NO"):
                    sys.exit(0)
                else:
                    logger.info("Invalid value. Must enter 'yes' or 'no'.")
        
        try:
            delete_volume(
                volume_name=volume_name, 
                svm_name=svm_name, 
                cluster_name=cluster_name, 
                delete_mirror=delete_mirror, 
                delete_non_clone=delete_non_clone, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            sys.exit(1)
