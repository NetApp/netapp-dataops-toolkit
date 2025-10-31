"""
Get command module for NetApp DataOps Toolkit.
"""

import getopt
from .base_command import BaseCommand
from netapp_dataops.help_text import (
    HELP_TEXT_GET_CIFS_SHARE
)
from netapp_dataops.traditional import (
    get_cifs_share,
    InvalidConfigError, 
    APIConnectionError, 
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