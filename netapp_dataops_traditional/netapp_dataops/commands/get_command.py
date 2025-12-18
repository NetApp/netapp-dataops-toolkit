"""
Get command module for NetApp DataOps Toolkit CLI.
"""

import getopt
from .base_command import BaseCommand, logger
from netapp_dataops.help_text import (
    HELP_TEXT_GET_QTREE,
    HELP_TEXT_GET_QTREE_METRICS
)
from netapp_dataops.traditional import (
    get_qtree,
    get_qtree_metrics,
    InvalidConfigError,
    APIConnectionError,
    InvalidVolumeParameterError
)


class GetCommand(BaseCommand):
    """Handle get command requests."""
    
    def execute(self) -> None:
        """Execute get command for various targets."""
        # Get desired target from command line args
        target = self.get_target()
        
        # Route to appropriate handler based on target
        if target in ("qtree", "qt"):
            self._get_qtree()
        elif target in ("qtree-metrics", "qtm"):
            self._get_qtree_metrics()
        else:
            self.handle_invalid_command()
    
    def _get_qtree(self) -> None:
        """Handle qtree retrieval."""
        volume_uuid = None
        qtree_id = None
        cluster_name = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hv:i:u:", 
                ["help", "volume-uuid=", "id=", "cluster-name="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_GET_QTREE, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_GET_QTREE)
                return
            elif opt in ("-v", "--volume-uuid"):
                volume_uuid = arg
            elif opt in ("-i", "--id"):
                try:
                    qtree_id = int(arg)
                except ValueError:
                    logger.error("Error: Qtree ID must be a valid integer.")
                    self.handle_invalid_command(help_text=HELP_TEXT_GET_QTREE, invalid_opt_arg=True)
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        # Check for required options
        if not volume_uuid or qtree_id is None:
            self.handle_invalid_command(help_text=HELP_TEXT_GET_QTREE, invalid_opt_arg=True)
        
        # Validate qtree_id is non-negative
        if qtree_id < 0:
            logger.error("Error: Qtree ID must be a non-negative integer.")
            self.handle_invalid_command(help_text=HELP_TEXT_GET_QTREE, invalid_opt_arg=True)
        
        # Get qtree
        try:
            get_qtree(
                volume_uuid=volume_uuid,
                qtree_id=qtree_id,
                cluster_name=cluster_name,
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            import sys
            sys.exit(1)
    
    def _get_qtree_metrics(self) -> None:
        """Handle qtree metrics retrieval."""
        volume_uuid = None
        qtree_id = None
        cluster_name = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "hv:i:u:", 
                ["help", "volume-uuid=", "id=", "cluster-name="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_GET_QTREE_METRICS, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_GET_QTREE_METRICS)
                return
            elif opt in ("-v", "--volume-uuid"):
                volume_uuid = arg
            elif opt in ("-i", "--id"):
                try:
                    qtree_id = int(arg)
                except ValueError:
                    logger.error("Error: Qtree ID must be a valid integer.")
                    self.handle_invalid_command(help_text=HELP_TEXT_GET_QTREE_METRICS, invalid_opt_arg=True)
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        # Check for required options
        if not volume_uuid or qtree_id is None:
            self.handle_invalid_command(help_text=HELP_TEXT_GET_QTREE_METRICS, invalid_opt_arg=True)
        
        # Validate qtree_id is non-negative
        if qtree_id < 0:
            logger.error("Error: Qtree ID must be a non-negative integer.")
            self.handle_invalid_command(help_text=HELP_TEXT_GET_QTREE_METRICS, invalid_opt_arg=True)
        
        # Get qtree metrics
        try:
            get_qtree_metrics(
                volume_uuid=volume_uuid,
                qtree_id=qtree_id,
                cluster_name=cluster_name,
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            import sys
            sys.exit(1)