"""
Dataset management for NetApp DataOps traditional environments.

This package provides high-level dataset abstraction functionality for managing
data stored on ONTAP volumes through an intuitive dataset interface.
"""

from .dataset import Dataset, get_datasets
from .exceptions import DatasetError, DatasetNotFoundError, DatasetExistsError
