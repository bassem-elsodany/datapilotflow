"""
Compatibility shim for opik with LangChain 1.0+.

In LangChain 1.0, the `langchain.load` module was moved to `langchain_classic.load`.
This module creates an alias to maintain compatibility with opik.
"""

import sys

import langchain_classic.load as load_module

# Create the langchain.load module alias
sys.modules["langchain.load"] = load_module
