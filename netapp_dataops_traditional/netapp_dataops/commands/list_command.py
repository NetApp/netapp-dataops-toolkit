"""
List command module for NetApp DataOps Toolkit CLI.
"""

import getopt
from .base_command import BaseCommand
from netapp_dataops.help_text import (
    HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS,
    HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS,
    HELP_TEXT_LIST_SNAPSHOTS,
    HELP_TEXT_LIST_VOLUMES,
    HELP_TEXT_LIST_CIFS_SHARES
)
from netapp_dataops.traditional import (
    list_cloud_sync_relationships,
    list_snap_mirror_relationships,
    list_snapshots,
    list_volumes,
    list_cifs_shares,
    InvalidConfigError,
    APIConnectionError,
    InvalidVolumeParameterError,
    InvalidCifsShareParameterError
)


class ListCommand(BaseCommand):
    """Handle list command requests."""
    
    def execute(self) -> None:
        """Execute list command for various targets."""
        # Get desired target from command line args
        target = self.get_target()
        
        # Route to appropriate handler based on target
        if target in ("cloud-sync-relationship", "cloud-sync", "cloud-sync-relationships", "cloud-syncs"):
            self._list_cloud_sync_relationships()
        elif target in ("snapmirror-relationship", "snapmirror", "snapmirror-relationships", "snapmirrors", "sm"):
            self._list_snapmirror_relationships()
        elif target in ("snapshot", "snap", "snapshots", "snaps"):
            self._list_snapshots()
        elif target in ("volume", "vol", "volumes", "vols"):
            self._list_volumes()
        elif target in ("cifs-shares", "cifs-share", "cifs", "cifsshare", "cifsshares"):
            self._list_cifs_shares()
        else:
            self.handle_invalid_command()
    
    def _list_cloud_sync_relationships(self) -> None:
        """Handle cloud sync relationships listing."""
        # Check command line options
        if len(self.args) > 3:
            if self.args[3] in ("-h", "--help"):
                print(HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS)
                return
            else:
                self.handle_invalid_command(HELP_TEXT_LIST_CLOUD_SYNC_RELATIONSHIPS, invalid_opt_arg=True)
        
        # List cloud sync relationships
        try:
            list_cloud_sync_relationships(print_output=True)
        except (InvalidConfigError, APIConnectionError):
            import sys
            sys.exit(1)
    
    def _list_snapmirror_relationships(self) -> None:
        """Handle snapmirror relationships listing."""
        svm_name = None
        cluster_name = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hv:u:", 
                ["cluster-name=", "help", "svm="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_LIST_SNAPMIRROR_RELATIONSHIPS)
                return
            elif opt in ("-v", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        # List snapmirror relationships
        try:
            list_snap_mirror_relationships(print_output=True, cluster_name=cluster_name)
        except (InvalidConfigError, APIConnectionError):
            import sys
            sys.exit(1)
    
    def _list_snapshots(self) -> None:
        """Handle snapshots listing."""
        volume_name = None
        cluster_name = None
        svm_name = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hv:s:u:", 
                ["cluster-name=", "help", "volume=", "svm="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_SNAPSHOTS, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_LIST_SNAPSHOTS)
                return
            elif opt in ("-v", "--volume"):
                volume_name = arg
            elif opt in ("-s", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        # Check for required options
        if not volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_SNAPSHOTS, invalid_opt_arg=True)
        
        # List snapshots
        try:
            list_snapshots(
                volume_name=volume_name, 
                cluster_name=cluster_name, 
                svm_name=svm_name, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            import sys
            sys.exit(1)
    
    def _list_volumes(self) -> None:
        """Handle volumes listing."""
        include_space_usage_details = False
        svm_name = None
        cluster_name = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hsv:u:", 
                ["cluster-name=", "help", "include-space-usage-details", "svm="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_VOLUMES, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_LIST_VOLUMES)
                return
            elif opt in ("-v", "--svm"):
                svm_name = arg
            elif opt in ("-s", "--include-space-usage-details"):
                include_space_usage_details = True
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        # List volumes
        try:
            list_volumes(
                check_local_mounts=True, 
                include_space_usage_details=include_space_usage_details, 
                print_output=True, 
                svm_name=svm_name, 
                cluster_name=cluster_name
            )
        except (InvalidConfigError, APIConnectionError):
            import sys
            sys.exit(1)

    def _list_cifs_shares(self) -> None:
        """Handle CIFS shares listing."""
        svm = None
        name_pattern = None
        cluster_name = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hv:u:n:", 
                ["cluster-name=", "help", "svm=", "name-pattern="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_LIST_CIFS_SHARES, invalid_opt_arg=True)

        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_LIST_CIFS_SHARES)
                return
            elif opt in ("-s", "--svm"):
                svm = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-n", "--name-pattern"):
                name_pattern = arg
        
        # List CIFS shares
        try:
            list_cifs_shares(
                svm=svm, 
                name_pattern=name_pattern,
                cluster_name=cluster_name,
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidCifsShareParameterError):
            import sys
            sys.exit(1)