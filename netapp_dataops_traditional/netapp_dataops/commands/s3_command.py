"""S3 command module for NetApp DataOps Toolkit CLI."""

import getopt
import sys
from .base_command import BaseCommand, logger
from netapp_dataops.help_text import (
    HELP_TEXT_PULL_FROM_S3_BUCKET,
    HELP_TEXT_PULL_FROM_S3_OBJECT,
    HELP_TEXT_PUSH_TO_S3_DIRECTORY,
    HELP_TEXT_PUSH_TO_S3_FILE
)
from netapp_dataops.traditional import (
    pull_bucket_from_s3,
    pull_object_from_s3,
    push_directory_to_s3,
    push_file_to_s3,
    InvalidConfigError,
    APIConnectionError
)


class S3Command(BaseCommand):
    """Handle S3-related command requests."""
    
    def execute(self) -> None:
        """Execute S3 command based on action."""
        if self.action in ("pull-from-s3", "pull-s3", "s3-pull"):
            self._handle_pull_from_s3()
        elif self.action in ("push-to-s3", "push-s3", "s3-push"):
            self._handle_push_to_s3()
        else:
            self.handle_invalid_command()
    
    def _handle_pull_from_s3(self) -> None:
        """Handle pull from S3 operations."""
        target = self.get_target()
        
        if target == "bucket":
            self._pull_bucket_from_s3()
        elif target in ("object", "file"):
            self._pull_object_from_s3()
        else:
            self.handle_invalid_command()
    
    def _handle_push_to_s3(self) -> None:
        """Handle push to S3 operations."""
        target = self.get_target()
        
        if target in ("directory", "dir"):
            self._push_directory_to_s3()
        elif target == "file":
            self._push_file_to_s3()
        else:
            self.handle_invalid_command()
    
    def _pull_bucket_from_s3(self) -> None:
        """Handle pulling bucket from S3."""
        s3_bucket = None
        s3_object_key_prefix = ""
        local_directory = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hb:p:d:e:", 
                ["help", "bucket=", "key-prefix=", "directory="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_PULL_FROM_S3_BUCKET, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_PULL_FROM_S3_BUCKET)
                return
            elif opt in ("-b", "--bucket"):
                s3_bucket = arg
            elif opt in ("-p", "--key-prefix"):
                s3_object_key_prefix = arg
            elif opt in ("-d", "--directory"):
                local_directory = arg
        
        if not s3_bucket or not local_directory:
            self.handle_invalid_command(help_text=HELP_TEXT_PULL_FROM_S3_BUCKET, invalid_opt_arg=True)
        
        try:
            pull_bucket_from_s3(
                s3_bucket=s3_bucket, 
                local_directory=local_directory, 
                s3_object_key_prefix=s3_object_key_prefix, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError):
            sys.exit(1)
    
    def _pull_object_from_s3(self) -> None:
        """Handle pulling object from S3."""
        s3_bucket = None
        s3_object_key = None
        local_file = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hb:k:f:", 
                ["help", "bucket=", "key=", "file=", "extra-args="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_PULL_FROM_S3_OBJECT, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_PULL_FROM_S3_OBJECT)
                return
            elif opt in ("-b", "--bucket"):
                s3_bucket = arg
            elif opt in ("-k", "--key"):
                s3_object_key = arg
            elif opt in ("-f", "--file"):
                local_file = arg
        
        if not s3_bucket or not s3_object_key:
            self.handle_invalid_command(help_text=HELP_TEXT_PULL_FROM_S3_OBJECT, invalid_opt_arg=True)
        
        try:
            pull_object_from_s3(
                s3_bucket=s3_bucket, 
                s3_object_key=s3_object_key, 
                local_file=local_file, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError):
            sys.exit(1)
    
    def _push_directory_to_s3(self) -> None:
        """Handle pushing directory to S3."""
        s3_bucket = None
        s3_object_key_prefix = ""
        local_directory = None
        s3_extra_args = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hb:p:d:e:", 
                ["help", "bucket=", "key-prefix=", "directory=", "extra-args="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_PUSH_TO_S3_DIRECTORY, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_PUSH_TO_S3_DIRECTORY)
                return
            elif opt in ("-b", "--bucket"):
                s3_bucket = arg
            elif opt in ("-p", "--key-prefix"):
                s3_object_key_prefix = arg
            elif opt in ("-d", "--directory"):
                local_directory = arg
            elif opt in ("-e", "--extra-args"):
                s3_extra_args = arg
        
        if not s3_bucket or not local_directory:
            self.handle_invalid_command(help_text=HELP_TEXT_PUSH_TO_S3_DIRECTORY, invalid_opt_arg=True)
        
        try:
            push_directory_to_s3(
                s3_bucket=s3_bucket, 
                local_directory=local_directory, 
                s3_object_key_prefix=s3_object_key_prefix, 
                s3_extra_args=s3_extra_args, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError):
            sys.exit(1)
    
    def _push_file_to_s3(self) -> None:
        """Handle pushing file to S3."""
        s3_bucket = None
        s3_object_key = None
        local_file = None
        s3_extra_args = None
        
        try:
            opts, _ = getopt.getopt(
                self.args[3:], 
                "hb:k:f:e:", 
                ["help", "bucket=", "key=", "file=", "extra-args="]
            )
        except Exception as err:
            logger.error(err)
            self.handle_invalid_command(help_text=HELP_TEXT_PUSH_TO_S3_FILE, invalid_opt_arg=True)
        
        for opt, arg in opts:
            if opt in ("-h", "--help"):
                logger.info(HELP_TEXT_PUSH_TO_S3_FILE)
                return
            elif opt in ("-b", "--bucket"):
                s3_bucket = arg
            elif opt in ("-k", "--key"):
                s3_object_key = arg
            elif opt in ("-f", "--file"):
                local_file = arg
            elif opt in ("-e", "--extra-args"):
                s3_extra_args = arg
        
        if not s3_bucket or not local_file:
            self.handle_invalid_command(help_text=HELP_TEXT_PUSH_TO_S3_FILE, invalid_opt_arg=True)
        
        try:
            push_file_to_s3(
                s3_bucket=s3_bucket, 
                s3_object_key=s3_object_key, 
                local_file=local_file, 
                s3_extra_args=s3_extra_args, 
                print_output=True
            )
        except (InvalidConfigError, APIConnectionError):
            sys.exit(1)
