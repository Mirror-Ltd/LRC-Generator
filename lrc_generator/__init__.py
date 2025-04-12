"""
LRC Generator - A tool to generate synchronized lyrics (.lrc) files for MP3 songs
"""

import os
import warnings
import re

# Set environment variables to disable OpenMP warnings
os.environ["KMP_WARNINGS"] = "off"

# Create custom warning filter
def _filter_omp_warnings(message, category, filename, lineno, file=None, line=None):
    if "OMP:" in str(message) or "omp_set_nested" in str(message):
        return None  # Don't show warning
    return True  # Show other warnings

# Install custom warning filter
warnings.showwarning = _filter_omp_warnings

# Filter specific warnings
warnings.filterwarnings("ignore", message="FP16 is not supported on CPU; using FP32 instead")
warnings.filterwarnings("ignore", message=".*omp_set_nested routine deprecated.*")
warnings.filterwarnings("ignore", message="OMP: Info #276: omp_set_nested routine deprecated, please use omp_set_max_active_levels instead.")

__version__ = "0.1.0"