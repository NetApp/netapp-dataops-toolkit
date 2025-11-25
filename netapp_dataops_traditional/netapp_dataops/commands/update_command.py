"""Update command module for NetApp DataOps Toolkit CLI."""

import getopt
import sys
from .base_command import BaseCommand, logger
from netapp_dataops.help_text import (
    HELP_TEXT_UPDATE_FLEXCACHE
)
from netapp_dataops.traditional import (
    update_flexcache,
    InvalidConfigError,
    APIConnectionError,
    InvalidVolumeParameterError
)


class UpdateCommand(BaseCommand):
    """Handle update command requests."""
    
    def execute(self) -> None:
        """Execute update command for various targets."""
        target = self.get_target()
        
        if target in ("flexcache", "fc"):
            self._update_flexcache()
        else:
            self.handle_invalid_command()
    
    def _update_flexcache(self) -> None:
        """Handle FlexCache volume update."""
        uuid = None
        volume_name = None
        svm_name = None
        cluster_name = None
        prepopulate_paths = None
        prepopulate_exclude_paths = None
        writeback_enabled = None
        relative_size_enabled = None
        relative_size_percentage = None
        atime_scrub_enabled = None
        atime_scrub_period = None
        cifs_change_notify_enabled = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hi:n:v:u:p:x:w:r:a:c:", 
                [
                    "help", 
                    "uuid=", 
                    "name=", 
                    "svm=", 
                    "cluster-name=",
                    "prepopulate-paths=",
                    "prepopulate-exclude-paths=",
                    "writeback-enabled=",
                    "relative-size-enabled=",
                    "relative-size-percentage=",
                    "atime-scrub-enabled=",
                    "atime-scrub-period=",
                    "cifs-change-notify-enabled="
                ]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_UPDATE_FLEXCACHE)
                return
            elif opt in ("-i", "--uuid"):
                uuid = arg
            elif opt in ("-n", "--name"):
                volume_name = arg
            elif opt in ("-v", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-p", "--prepopulate-paths"):
                prepopulate_paths = arg.split(',')
            elif opt in ("-x", "--prepopulate-exclude-paths"):
                prepopulate_exclude_paths = arg.split(',')
            elif opt in ("-w", "--writeback-enabled"):
                if arg.lower() in ('true', '1', 'yes', 'y'):
                    writeback_enabled = True
                elif arg.lower() in ('false', '0', 'no', 'n'):
                    writeback_enabled = False
                else:
                    logger.error("Error: Invalid value for writeback-enabled. Use 'true' or 'false'.")
                    self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
            elif opt in ("-r", "--relative-size-enabled"):
                if arg.lower() in ('true', '1', 'yes', 'y'):
                    relative_size_enabled = True
                elif arg.lower() in ('false', '0', 'no', 'n'):
                    relative_size_enabled = False
                else:
                    logger.error("Error: Invalid value for relative-size-enabled. Use 'true' or 'false'.")
                    self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
            elif opt == "--relative-size-percentage":
                try:
                    relative_size_percentage = int(arg)
                    if not (1 <= relative_size_percentage <= 100):
                        logger.error("Error: relative-size-percentage must be between 1 and 100.")
                        self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
                except ValueError:
                    logger.error("Error: relative-size-percentage must be an integer.")
                    self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
            elif opt in ("-a", "--atime-scrub-enabled"):
                if arg.lower() in ('true', '1', 'yes', 'y'):
                    atime_scrub_enabled = True
                elif arg.lower() in ('false', '0', 'no', 'n'):
                    atime_scrub_enabled = False
                else:
                    logger.error("Error: Invalid value for atime-scrub-enabled. Use 'true' or 'false'.")
                    self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
            elif opt == "--atime-scrub-period":
                try:
                    atime_scrub_period = int(arg)
                    if not (1 <= atime_scrub_period <= 365):
                        logger.error("Error: atime-scrub-period must be between 1 and 365 days.")
                        self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
                except ValueError:
                    logger.error("Error: atime-scrub-period must be an integer.")
                    self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
            elif opt in ("-c", "--cifs-change-notify-enabled"):
                if arg.lower() in ('true', '1', 'yes', 'y'):
                    cifs_change_notify_enabled = True
                elif arg.lower() in ('false', '0', 'no', 'n'):
                    cifs_change_notify_enabled = False
                else:
                    logger.error("Error: Invalid value for cifs-change-notify-enabled. Use 'true' or 'false'.")
                    self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
        
        # Validate that either uuid or volume_name is provided
        if not uuid and not volume_name:
            logger.error("Error: Either --uuid or --name must be provided.")
            self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
        
        # Check if at least one update parameter is provided
        if all(param is None for param in [
            prepopulate_paths, prepopulate_exclude_paths, writeback_enabled,
            relative_size_enabled, relative_size_percentage, atime_scrub_enabled,
            atime_scrub_period, cifs_change_notify_enabled
        ]):
            logger.error("Error: At least one update parameter must be provided.")
            self.handle_invalid_command(help_text=HELP_TEXT_UPDATE_FLEXCACHE, invalid_opt_arg=True)
        
        try:
            update_flexcache(
                uuid=uuid,
                volume_name=volume_name,
                svm_name=svm_name,
                cluster_name=cluster_name,
                prepopulate_paths=prepopulate_paths,
                prepopulate_exclude_paths=prepopulate_exclude_paths,
                writeback_enabled=writeback_enabled,
                relative_size_enabled=relative_size_enabled,
                relative_size_percentage=relative_size_percentage,
                atime_scrub_enabled=atime_scrub_enabled,
                atime_scrub_period=atime_scrub_period,
                cifs_change_notify_enabled=cifs_change_notify_enabled,
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            sys.exit(1)
