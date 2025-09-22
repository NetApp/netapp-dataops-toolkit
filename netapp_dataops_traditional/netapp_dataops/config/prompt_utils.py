"""
Prompt utilities for NetApp DataOps Toolkit configuration.

This module provides reusable prompt functions for interactive configuration
operations across different configuration modules.
"""

import getpass
from typing import List


class PromptUtils:
    """
    Utility class for handling user prompts during configuration.
    
    This class provides standard prompt methods that can be used across
    different configuration modules to maintain consistency.
    """
    
    @staticmethod
    def prompt_required(prompt: str) -> str:
        """Prompt for required input with validation."""
        while True:
            value = input(f"{prompt}: ").strip()
            if value:
                return value
            print("This field is required. Please enter a value.")
    
    @staticmethod
    def prompt_with_default(prompt: str, default: str) -> str:
        """Prompt with default value."""
        value = input(f"{prompt} [{default}]: ").strip()
        return value if value else default
    
    @staticmethod
    def prompt_password(prompt: str) -> str:
        """Prompt for password input (hidden)."""
        while True:
            password = getpass.getpass(f"{prompt}: ")
            if password:
                return password
            print("Password cannot be empty. Please enter a password.")
    
    @staticmethod
    def prompt_yes_no(prompt: str, default: bool = False) -> bool:
        """Prompt for yes/no input."""
        default_str = "Y/n" if default else "y/N"
        
        while True:
            value = input(f"{prompt} [{default_str}]: ").strip().lower()
            
            if not value:
                return default
            elif value in ['y', 'yes']:
                return True
            elif value in ['n', 'no']:
                return False
            else:
                print("Please enter 'y' for yes or 'n' for no.")
    
    @staticmethod
    def prompt_choice(prompt: str, choices: List[str], default: str = None) -> str:
        """Prompt for choice from list of options."""
        choices_str = "/".join(choices)
        if default:
            choices_str = choices_str.replace(default, default.upper())
            
        while True:
            value = input(f"{prompt} [{choices_str}]: ").strip().lower()
            
            if not value and default:
                return default
            elif value in choices:
                return value
            else:
                print(f"Please choose from: {', '.join(choices)}")
