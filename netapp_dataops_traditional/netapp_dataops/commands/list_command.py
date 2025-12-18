"""List command module for NetApp DataOps Toolkit CLI."""

import getopt
import sys
from .base_command import BaseCommand, logger
from netapp_dataops.help_text import (
    HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS,
    HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS,
    HELP_TEXT_LIST_SNAPSHOTS,
    HELP_TEXT_LIST_VOLUMES,
    HELP_TEXT_LIST_QTREES
)
from netapp_dataops.traditional import (
    list_cloud_sync_relationships,
    list_snap_mirror_relationships,
    list_snapshots,
    list_volumes,
    list_qtrees,
    InvalidConfigError,
    APIConnectionError,
    InvalidVolumeParameterError
)


class ListCommand(BaseCommand):
    """Handle list command requests."""
    
    def execute(self) -> None:
        """Execute list command for various targets."""
        target = self.get_target()
        
        if target in ("cloud-sync-relationship", "cloud-sync", "cloud-sync-relationships", "cloud-syncs"):
            self._list_cloud_sync_relationships()
        elif target in ("snapmirror-relationship", "snapmirror", "snapmirror-relationships", "snapmirrors", "sm"):
            self._list_snapmirror_relationships()
        elif target in ("snapshot", "snap", "snapshots", "snaps"):
            self._list_snapshots()
        elif target in ("volume", "vol", "volumes", "vols"):
            self._list_volumes()
        elif target in ("qtree", "qt", "qtrees", "qts"):
            self._list_qtrees()
        else:
            self.handle_invalid_command()
    
    def _list_cloud_sync_relationships(self) -> None:
        """Handle cloud sync relationships listing."""
        if len(self.args) > 3:
            if self.args[3] in ("-h", "--help"):
                logger.info(HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS)
                return
            else:
                self.handle_invalid_command(HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS, invalid_opt_arg=True)
        
        try:
            list_cloud_sync_relationships(print_output=True)
        except (InvalidConfigError, APIConnectionError):
            sys.exit(1)
    
    def _list_snapmirror_relationships(self) -> None:
        """Handle snapmirror relationships listing."""
        svm_name = None
        cluster_name = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hv:u:", 
                ["cluster-name=", "help", "svm="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS)
                return
            elif opt in ("-v", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        try:
            list_snap_mirror_relationships(print_output=True, cluster_name=cluster_name)
        except (InvalidConfigError, APIConnectionError):
            sys.exit(1)
    
    def _list_snapshots(self) -> None:
        """Handle snapshots listing."""
        volume_name = None
        cluster_name = None
        svm_name = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hv:s:u:", 
                ["cluster-name=", "help", "volume=", "svm="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_SNAPSHOTS, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_LIST_SNAPSHOTS)
                return
            elif opt in ("-v", "--volume"):
                volume_name = arg
            elif opt in ("-s", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        if not volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_SNAPSHOTS, invalid_opt_arg=True)
        
        try:
            list_snapshots(
                volume_name=volume_name, 
                cluster_name=cluster_name, 
                svm_name=svm_name, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            sys.exit(1)
    
    def _list_volumes(self) -> None:
        """Handle volumes listing."""
        include_space_usage_details = False
        svm_name = None
        cluster_name = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hsv:u:", 
                ["cluster-name=", "help", "include-space-usage-details", "svm="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_VOLUMES, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_LIST_VOLUMES)
                return
            elif opt in ("-v", "--svm"):
                svm_name = arg
            elif opt in ("-s", "--include-space-usage-details"):
                include_space_usage_details = True
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        try:
            list_volumes(
                check_local_mounts=True, 
                include_space_usage_details=include_space_usage_details, 
                print_output=True, 
                svm_name=svm_name, 
                cluster_name=cluster_name
            )
        except (InvalidConfigError, APIConnectionError):
            sys.exit(1)
    
    def _list_qtrees(self) -> None:
        """Handle qtrees listing."""
        volume_name = None
        cluster_name = None
        svm_name = None
        
        # Get command line options
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hv:s:u:", 
                ["help", "volume=", "svm=", "cluster-name="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_QTREES, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_LIST_QTREES)
                return
            elif opt in ("-v", "--volume"):
                volume_name = arg
            elif opt in ("-s", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        # List qtrees
        try:
            list_qtrees(
                volume_name=volume_name,
                cluster_name=cluster_name,
                svm_name=svm_name,
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            sys.exit(1)
