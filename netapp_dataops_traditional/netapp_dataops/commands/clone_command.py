"""Clone command module for NetApp DataOps Toolkit CLI"""

import getopt
from .base_command import BaseCommand
from netapp_dataops.help_text import HELP_TEXT_CLONE_VOLUME
from netapp_dataops.traditional import (
    clone_volume,
    InvalidConfigError,
    APIConnectionError,
    InvalidSnapshotParameterError,
    InvalidVolumeParameterError,
    MountOperationError
)


class CloneCommand(BaseCommand):
    """Handle clone command requests."""
    
    def execute(self) -> None:
        """Execute clone command for volumes."""
        target = self.get_target()
        
        # Invoke desired action based on target
        if target in ("volume", "vol"):
            self._clone_volume()
        else:
            self.handle_invalid_command()
    
    def _clone_volume(self) -> None:
        """Handle volume cloning operations."""
        # Initialize variables
        new_volume_name = None
        cluster_name = None
        source_svm = None
        target_svm = None
        source_volume_name = None
        source_snapshot_name = None
        mountpoint = None
        unix_uid = None
        unix_gid = None
        junction = None
        readonly = False
        split = False
        refresh = False
        export_policy = None
        snapshot_policy = None
        export_hosts = None
        svm_dr_unprotect = False
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hl:c:t:n:v:s:m:u:g:j:xe:p:i:srd", 
                ["help", "cluster-name=", "source-svm=", "target-svm=", "name=", 
                 "source-volume=", "source-snapshot=", "mountpoint=", "uid=", "gid=", 
                 "junction=", "readonly", "export-hosts=", "export-policy=", 
                 "snapshot-policy=", "split", "refresh", "svm-dr-unprotect"]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_CLONE_VOLUME, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_CLONE_VOLUME)
                return
            elif opt in ("-l", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-n", "--name"):
                new_volume_name = arg
            elif opt in ("-c", "--source-svm"):
                source_svm = arg
            elif opt in ("-t", "--target-svm"):
                target_svm = arg
            elif opt in ("-v", "--source-volume"):
                source_volume_name = arg
            elif opt in ("-s", "--source-snapshot"):
                source_snapshot_name = arg
            elif opt in ("-m", "--mountpoint"):
                mountpoint = arg
            elif opt in ("-u", "--uid"):
                unix_uid = arg
            elif opt in ("-g", "--gid"):
                unix_gid = arg
            elif opt in ("-j", "--junction"):
                junction = arg
            elif opt in ("-x", "--readonly"):
                readonly = True
            elif opt in ("-s", "--split"):
                split = True
            elif opt in ("-r", "--refresh"):
                refresh = True
            elif opt in ("-d", "--svm-dr-unprotect"):
                svm_dr_unprotect = True
            elif opt in ("-p", "--export-policy"):
                export_policy = arg
            elif opt in ("-i", "--snapshot-policy"):
                snapshot_policy = arg
            elif opt in ("-e", "--export-hosts"):
                export_hosts = arg
        
        # Check for required options
        if not new_volume_name or not source_volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_CLONE_VOLUME, invalid_opt_arg=True)
        
        if (unix_uid and not unix_gid) or (unix_gid and not unix_uid):
            logger.error("Error: if either one of -u/--uid or -g/--gid is specified, then both must be specified.")
            self.handle_invalid_command(help_text=HELP_TEXT_CLONE_VOLUME, invalid_opt_arg=True)
        
        if export_hosts and export_policy:
            logger.error("Error: cannot use both --export-policy and --export-hosts. only one of them can be specified.")
            self.handle_invalid_command(help_text=HELP_TEXT_CLONE_VOLUME, invalid_opt_arg=True)
        
        # Clone volume
        try:
            clone_volume(
                new_volume_name=new_volume_name, 
                source_volume_name=source_volume_name, 
                source_snapshot_name=source_snapshot_name,
                cluster_name=cluster_name, 
                source_svm=source_svm, 
                target_svm=target_svm, 
                export_policy=export_policy, 
                export_hosts=export_hosts,
                snapshot_policy=snapshot_policy, 
                split=split, 
                refresh=refresh, 
                mountpoint=mountpoint, 
                unix_uid=unix_uid, 
                unix_gid=unix_gid,
                junction=junction, 
                svm_dr_unprotect=svm_dr_unprotect, 
                readonly=readonly, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidSnapshotParameterError, 
                InvalidVolumeParameterError, MountOperationError):
            import sys
            sys.exit(1)
