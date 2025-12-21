"""Test configuration for persistence tests."""

import sys
import os

# This needs to run BEFORE pytest collects anything
# Add src directories to path
test_dir = os.path.dirname(__file__)
persistence_src = os.path.abspath(os.path.join(test_dir, '..', 'src'))
domain_src = os.path.abspath(os.path.join(test_dir, '..', '..', 'datapilotflow-domain', 'src'))

# Clear datapilotflow from cache if already imported with wrong path
if 'datapilotflow' in sys.modules:
    del sys.modules['datapilotflow']
if 'datapilotflow.domain' in sys.modules:
    del sys.modules['datapilotflow.domain']
if 'datapilotflow.infrastructure' in sys.modules:
    del sys.modules['datapilotflow.infrastructure']

# Add to path FIRST
if persistence_src not in sys.path:
    sys.path.insert(0, persistence_src)
if domain_src not in sys.path:
    sys.path.insert(0, domain_src)
