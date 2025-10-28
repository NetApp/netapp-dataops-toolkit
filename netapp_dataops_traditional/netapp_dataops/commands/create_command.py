"""
Create command module for NetApp DataOps Toolkit CLI.
"""

import getopt
import re
from .base_command import BaseCommand
from netapp_dataops.help_text import (
    HELP_TEXT_CREATE_SNAPSHOT,
    HELP_TEXT_CREATE_VOLUME,
    HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP,
    HELP_TEXT_CREATE_QTREE
)
from netapp_dataops.traditional import (
    create_snapshot,
    create_volume,
    create_snap_mirror_relationship,
    create_qtree,
    InvalidConfigError,
    APIConnectionError,
    InvalidVolumeParameterError,
    MountOperationError
)


class CreateCommand(BaseCommand):
    """Handle create command requests."""
    
    def execute(self) -> None:
        """Execute create command for various targets."""
        # Get desired target from command line args
        target = self.get_target()
        
        # Route to appropriate handler based on target
        if target in ("snapshot", "snap"):
            self._create_snapshot()
        elif target in ("volume", "vol"):
            self._create_volume()
        elif target in ("snapmirror-relationship", "sm", "snapmirror"):
            self._create_snapmirror_relationship()
        elif target in ("qtree", "qt"):
            self._create_qtree()
        else:
            self.handle_invalid_command()
    
    def _create_snapshot(self) -> None:
        """Handle snapshot creation."""
        # Initialize variables
        volume_name = None
        snapshot_name = None
        cluster_name = None
        svm_name = None
        retention_count = 0
        retention_days = False
        snapmirror_label = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hn:v:s:r:u:l:", 
                ["cluster-name=", "help", "svm=", "name=", "volume=", "retention=", "snapmirror-label="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_SNAPSHOT, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_CREATE_SNAPSHOT)
                return
            elif opt in ("-n", "--name"):
                snapshot_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-s", "--svm"):
                svm_name = arg
            elif opt in ("-r", "--retention"):
                retention_count = arg
            elif opt in ("-v", "--volume"):
                volume_name = arg
            elif opt in ("-l", "--snapmirror-label"):
                snapmirror_label = arg
        
        # Check for required options
        if not volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_SNAPSHOT, invalid_opt_arg=True)
        
        if retention_count:
            if not retention_count.isnumeric():
                match_obj = re.match(r"^(\d+)d$", retention_count)
                if not match_obj:
                    self.handle_invalid_command(help_text=HELP_TEXT_CREATE_SNAPSHOT, invalid_opt_arg=True)
                else:
                    retention_count = match_obj.group(1)
                    retention_days = True
        
        # Create snapshot
        try:
            create_snapshot(
                volume_name=volume_name, 
                snapshot_name=snapshot_name, 
                retention_count=retention_count, 
                retention_days=retention_days, 
                cluster_name=cluster_name, 
                svm_name=svm_name, 
                snapmirror_label=snapmirror_label, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            import sys
            sys.exit(1)
    
    def _create_volume(self) -> None:
        """Handle volume creation."""
        # Initialize variables
        cluster_name = None
        svm_name = None
        volume_name = None
        volume_size = None
        guarantee_space = False
        volume_type = None
        unix_permissions = None
        unix_uid = None
        unix_gid = None
        export_policy = None
        snapshot_policy = None
        mountpoint = None
        snaplock_type = None
        aggregate = None
        junction = None
        readonly = False
        tiering_policy = None
        vol_dp = False
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "l:hv:t:n:s:rt:p:u:g:e:d:m:a:j:xu:yw:", 
                ["cluster-name=", "help", "svm=", "name=", "size=", "guarantee-space", 
                 "type=", "permissions=", "uid=", "gid=", "export-policy=", 
                 "snapshot-policy=", "mountpoint=", "aggregate=", "junction=", 
                 "readonly", "tiering-policy=", "dp", "snaplock-type="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_VOLUME, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_CREATE_VOLUME)
                return
            elif opt in ("-v", "--svm"):
                svm_name = arg
            elif opt in ("-l", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-n", "--name"):
                volume_name = arg
            elif opt in ("-s", "--size"):
                volume_size = arg
            elif opt in ("-r", "--guarantee-space"):
                guarantee_space = True
            elif opt in ("-t", "--type"):
                volume_type = arg
            elif opt in ("-p", "--permissions"):
                unix_permissions = arg
            elif opt in ("-u", "--uid"):
                unix_uid = arg
            elif opt in ("-g", "--gid"):
                unix_gid = arg
            elif opt in ("-e", "--export-policy"):
                export_policy = arg
            elif opt in ("-d", "--snapshot-policy"):
                snapshot_policy = arg
            elif opt in ("-m", "--mountpoint"):
                mountpoint = arg
            elif opt in ("-a", "--aggregate"):
                aggregate = arg
            elif opt in ("-j", "--junction"):
                junction = arg
            elif opt in ("-x", "--readonly"):
                readonly = True
            elif opt in ("-f", "--tiering-policy"):
                tiering_policy = arg
            elif opt in ("-y", "--dp"):
                vol_dp = True
            elif opt in ("-w", "--snaplock-type"):
                snaplock_type = arg
        
        # Check for required options
        if not volume_name or not volume_size:
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_VOLUME, invalid_opt_arg=True)
        
        if (unix_uid and not unix_gid) or (unix_gid and not unix_uid):
            print("Error: if either one of -u/--uid or -g/--gid is specified, then both must be specified.")
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_VOLUME, invalid_opt_arg=True)
        
        if vol_dp and (junction or mountpoint or snapshot_policy or export_policy):
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_VOLUME, invalid_opt_arg=True)
        
        # Create volume
        try:
            create_volume(
                svm_name=svm_name, 
                volume_name=volume_name, 
                cluster_name=cluster_name, 
                volume_size=volume_size, 
                guarantee_space=guarantee_space, 
                volume_type=volume_type, 
                unix_permissions=unix_permissions, 
                unix_uid=unix_uid,
                unix_gid=unix_gid, 
                export_policy=export_policy, 
                snapshot_policy=snapshot_policy, 
                aggregate=aggregate, 
                mountpoint=mountpoint, 
                junction=junction, 
                readonly=readonly,
                print_output=True, 
                tiering_policy=tiering_policy, 
                vol_dp=vol_dp, 
                snaplock_type=snaplock_type
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
            import sys
            sys.exit(1)
    
    def _create_snapmirror_relationship(self) -> None:
        """Handle SnapMirror relationship creation."""
        # Initialize variables
        cluster_name = None
        source_svm = None
        target_svm = None
        source_vol = None
        target_vol = None
        policy = 'MirrorAllSnapshots'
        schedule = "hourly"
        action = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hn:t:s:v:u:y:c:p:a:h", 
                ["cluster-name=", "help", "target-vol=", "target-svm=", "source-svm=", 
                 "source-vol=", "schedule=", "policy=", "action="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP)
                return
            elif opt in ("-t", "--target-svm"):
                target_svm = arg
            elif opt in ("-n", "--target-vol"):
                target_vol = arg
            elif opt in ("-s", "--source-svm"):
                source_svm = arg
            elif opt in ("-v", "--source-vol"):
                source_vol = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-c", "--schedule"):
                schedule = arg
            elif opt in ("-p", "--policy"):
                policy = arg
            elif opt in ("-a", "--action"):
                action = arg
        
        # Check for required options
        if not target_vol or not source_svm or not source_vol:
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP, invalid_opt_arg=True)
        
        if action not in [None, 'resync', 'initialize']:
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_SNAPMIRROR_RELATIONSHIP, invalid_opt_arg=True)
        
        # Create snapmirror
        try:
            create_snap_mirror_relationship(
                source_svm=source_svm, 
                target_svm=target_svm, 
                source_vol=source_vol, 
                target_vol=target_vol, 
                schedule=schedule, 
                policy=policy,
                cluster_name=cluster_name, 
                action=action, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError, MountOperationError):
            import sys
            sys.exit(1)
    
    def _create_qtree(self) -> None:
        """Handle qtree creation."""
        # Initialize variables
        qtree_name = None
        volume_name = None
        cluster_name = None
        svm_name = None
        security_style = None
        unix_permissions = None
        export_policy = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hn:v:u:s:t:p:e:", 
                ["help", "name=", "volume=", "cluster-name=", "svm=", 
                 "security-style=", "permissions=", "export-policy="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_QTREE, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_CREATE_QTREE)
                return
            elif opt in ("-n", "--name"):
                qtree_name = arg
            elif opt in ("-v", "--volume"):
                volume_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-s", "--svm"):
                svm_name = arg
            elif opt in ("-t", "--security-style"):
                security_style = arg
            elif opt in ("-p", "--permissions"):
                unix_permissions = arg
            elif opt in ("-e", "--export-policy"):
                export_policy = arg
        
        # Check for required options
        if not qtree_name or not volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_QTREE, invalid_opt_arg=True)
        
        # Validate security style if provided
        if security_style and security_style not in ["unix", "ntfs", "mixed"]:
            print("Error: Security style must be one of: unix, ntfs, mixed")
            self.handle_invalid_command(help_text=HELP_TEXT_CREATE_QTREE, invalid_opt_arg=True)
        
        # Create qtree
        try:
            create_qtree(
                qtree_name=qtree_name,
                volume_name=volume_name,
                cluster_name=cluster_name,
                svm_name=svm_name,
                security_style=security_style,
                unix_permissions=unix_permissions,
                export_policy=export_policy,
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            import sys
            sys.exit(1)
