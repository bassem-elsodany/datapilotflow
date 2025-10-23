"""
SkillPilot Tools Package

This package contains all utility tools for the SkillPilot system, organized into logical subpackages.

Subpackages:
    - core: Core data processing and management tools
    - search: Search-related tools and comparisons
    - debug: Debugging and diagnostic tools
    - data: Data import, export, and management tools
    - testing: Testing and validation tools
    - examples: Example and demonstration scripts
    - ml: Machine learning tools

Usage:
    from tools.core import create_long_term_memory
    from tools.search import comprehensive_search_comparison
    from tools.data import import_weaviate_data
    from tools.testing import test_bge_embedding
    from tools.examples import batch_extraction_example
    from tools.ml import cluster_analysis
"""

__version__ = "2.0.0"
__author__ = "SkillPilot Team"

# Import main subpackages for easy access
from . import core
from . import search
from . import data
from . import testing
from . import examples
from . import ml

__all__ = [
    'core',
    'search', 
    'data',
    'testing',
    'examples',
    'ml'
] 