"""Restore command module for NetApp DataOps Toolkit CLI."""

import getopt
import sys
from .base_command import BaseCommand, logger
from netapp_dataops.help_text import HELP_TEXT_RESTORE_SNAPSHOT
from netapp_dataops.traditional import (
    restore_snapshot,
    InvalidConfigError,
    APIConnectionError,
    InvalidSnapshotParameterError,
    InvalidVolumeParameterError
)


class RestoreCommand(BaseCommand):
    """Handle restore command requests."""
    
    def execute(self) -> None:
        """Execute restore command for snapshots."""
        target = self.get_target()
        
        if target in ("snapshot", "snap"):
            self._restore_snapshot()
        else:
            self.handle_invalid_command()
    
    def _restore_snapshot(self) -> None:
        """Handle snapshot restoration."""
        volume_name = None
        snapshot_name = None
        svm_name = None
        cluster_name = None
        force = False
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hs:n:v:fu:", 
                ["cluster-name=", "help", "svm=", "name=", "volume=", "force"]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_RESTORE_SNAPSHOT, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_RESTORE_SNAPSHOT)
                return
            elif opt in ("-n", "--name"):
                snapshot_name = arg
            elif opt in ("-s", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-v", "--volume"):
                volume_name = arg
            elif opt in ("-f", "--force"):
                force = True
        
        if not volume_name or not snapshot_name:
            self.handle_invalid_command(help_text=HELP_TEXT_RESTORE_SNAPSHOT, invalid_opt_arg=True)
        
        if not force:
            logger.info("Warning: When you restore a snapshot, all subsequent snapshots are deleted.")
            while True:
                proceed = input("Are you sure that you want to proceed? (yes/no): ")
                if proceed in ("yes", "Yes", "YES"):
                    break
                elif proceed in ("no", "No", "NO"):
                    sys.exit(0)
                else:
                    logger.info("Invalid value. Must enter 'yes' or 'no'.")
        
        try:
            restore_snapshot(
                volume_name=volume_name, 
                snapshot_name=snapshot_name, 
                svm_name=svm_name, 
                cluster_name=cluster_name, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidSnapshotParameterError, InvalidVolumeParameterError):
            sys.exit(1)
