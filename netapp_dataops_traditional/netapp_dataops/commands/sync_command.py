"""Sync command module for NetApp DataOps Toolkit CLI."""

import getopt
import sys
from .base_command import BaseCommand, logger
from netapp_dataops.help_text import (
    HELP_TEXT_SYNC_CLOUD_SYNC_RELATIONSHIP,
    HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP
)
from netapp_dataops.traditional import (
    sync_cloud_sync_relationship,
    sync_snap_mirror_relationship,
    InvalidConfigError,
    APIConnectionError,
    CloudSyncSyncOperationError,
    InvalidSnapMirrorParameterError,
    SnapMirrorSyncOperationError
)


class SyncCommand(BaseCommand):
    """Handle sync command requests."""
    
    def execute(self) -> None:
        """Execute sync command for various relationships."""
        target = self.get_target()
        
        if target in ("cloud-sync-relationship", "cloud-sync"):
            self._sync_cloud_sync_relationship()
        elif target in ("snapmirror-relationship", "snapmirror"):
            self._sync_snapmirror_relationship()
        else:
            self.handle_invalid_command()
    
    def _sync_cloud_sync_relationship(self) -> None:
        """Handle cloud sync relationship synchronization."""
        relationship_id = None
        wait_until_complete = False
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hi:w", 
                ["help", "id=", "wait"]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_SYNC_CLOUD_SYNC_RELATIONSHIP, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_SYNC_CLOUD_SYNC_RELATIONSHIP)
                return
            elif opt in ("-i", "--id"):
                relationship_id = arg
            elif opt in ("-w", "--wait"):
                wait_until_complete = True
        
        if not relationship_id:
            self.handle_invalid_command(help_text=HELP_TEXT_SYNC_CLOUD_SYNC_RELATIONSHIP, invalid_opt_arg=True)
        
        try:
            sync_cloud_sync_relationship(
                relationship_id=relationship_id, 
                wait_until_complete=wait_until_complete, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, CloudSyncSyncOperationError):
            sys.exit(1)
    
    def _sync_snapmirror_relationship(self) -> None:
        """Handle SnapMirror relationship synchronization."""
        uuid = None
        volume_name = None
        svm_name = None
        cluster_name = None
        wait_until_complete = False
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hi:wn:u:v:", 
                ["help", "cluster-name=", "svm=", "name=", "uuid=", "wait"]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP)
                return
            elif opt in ("-v", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-n", "--name"):
                volume_name = arg
            elif opt in ("-i", "--uuid"):
                uuid = arg
            elif opt in ("-w", "--wait"):
                wait_until_complete = True
        
        if not uuid and not volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP, invalid_opt_arg=True)
        
        if uuid and volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_SYNC_SNAPMIRROR_RELATIONSHIP, invalid_opt_arg=True)
        
        try:
            sync_snap_mirror_relationship(
                uuid=uuid, 
                svm_name=svm_name, 
                volume_name=volume_name, 
                cluster_name=cluster_name, 
                wait_until_complete=wait_until_complete, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidSnapMirrorParameterError, SnapMirrorSyncOperationError):
            sys.exit(1)
