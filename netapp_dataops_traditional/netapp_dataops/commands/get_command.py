"""
Get command module for NetApp DataOps Toolkit CLI.
"""

import getopt
import sys
from .base_command import BaseCommand, logger
from netapp_dataops.help_text import (
    HELP_TEXT_GET_CIFS_SHARE,
    HELP_TEXT_GET_QTREE,
    HELP_TEXT_GET_QTREE_METRICS,
    HELP_TEXT_GET_FLEXCACHE_ORIGIN
)
from netapp_dataops.traditional import (
    get_cifs_share,
    get_qtree,
    get_qtree_metrics,
    get_flexcache_origin,
    InvalidConfigError,
    APIConnectionError,
    InvalidVolumeParameterError,
    InvalidCifsShareParameterError
)


class GetCommand(BaseCommand):
    """Handle get command requests."""
    
    def execute(self) -> None:
        """Execute get command for various targets."""
        # Get desired target from command line args
        target = self.get_target()
        
        # Route to appropriate handler based on target
        if target in ("cifs-share", "cifs", "cifsshare"):
            self._get_cifs_share()
        elif target in ("qtree", "qt"):
            self._get_qtree()
        elif target in ("qtree-metrics", "qtm"):
            self._get_qtree_metrics()
        elif target in ("flexcache-origin", "fco"):
            self._get_flexcache_origin()
        else:
            self.handle_invalid_command()

    def _get_cifs_share(self) -> None:
        """Get CIFS share information."""

        # Initialize variables
        svm = None
        name = None
        cluster_name = None
        
        # Get command line options
        try:
            opts, args = getopt.getopt(
                self.args[3:], 
                "u:h:s:n:", 
                ["cluster-name=", "help", "svm=", "name="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_GET_CIFS_SHARE, invalid_opt_arg=True)

        #Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_GET_CIFS_SHARE)
                return
            elif opt in ("-s", "--svm"):
                svm = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
            elif opt in ("-n", "--name"):
                name = arg

        # Check for required options
        if not name or not svm:
            self.handle_invalid_command(help_text=HELP_TEXT_GET_CIFS_SHARE, invalid_opt_arg=True)

        # Get CIFS share information
        try:
            get_cifs_share(
                svm=svm,
                name=name,
                cluster_name=cluster_name,
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidCifsShareParameterError):
            import sys
            sys.exit(1)
    
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
    
    def _get_flexcache_origin(self) -> None:
        """Handle FlexCache origin retrieval."""
        volume_name = None
        svm_name = None
        cluster_name = None
        
        # Get command line options
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hn:s:u:", 
                ["help", "volume-name=", "svm=", "cluster-name="]
            )
        except Exception as err:
            print(err)
            self.handle_invalid_command(help_text=HELP_TEXT_GET_FLEXCACHE_ORIGIN, invalid_opt_arg=True)
        
        # Parse command line options
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                print(HELP_TEXT_GET_FLEXCACHE_ORIGIN)
                return
            elif opt in ("-n", "--volume-name"):
                volume_name = arg
            elif opt in ("-s", "--svm"):
                svm_name = arg
            elif opt in ("-u", "--cluster-name"):
                cluster_name = arg
        
        # Check for required options
        if not volume_name:
            self.handle_invalid_command(help_text=HELP_TEXT_GET_FLEXCACHE_ORIGIN, invalid_opt_arg=True)
        
        # Get FlexCache origin
        try:
            get_flexcache_origin(
                volume_name=volume_name,
                svm_name=svm_name,
                cluster_name=cluster_name,
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError, InvalidVolumeParameterError):
            sys.exit(1)