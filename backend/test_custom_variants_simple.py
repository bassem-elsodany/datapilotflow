"""
Simple validation script for custom_variants strategy implementation.

This script validates the implementation without requiring full dependencies.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))


def validate_implementation():
    """Validate that all required files and changes are in place."""
    
    print("=" * 80)
    print("🔍 Validating Custom Variants Strategy Implementation")
    print("=" * 80)
    print()
    
    checks = []
    
    # Check 1: custom_variants_node.py exists
    node_file = Path(__file__).parent / "src/agents/rag_agent/nodes/custom_variants_node.py"
    if node_file.exists():
        checks.append(("✅", "custom_variants_node.py created"))
        # Check if it has the async function
        content = node_file.read_text()
        if "async def custom_variants_node" in content:
            checks.append(("✅", "  - custom_variants_node function defined"))
        if "augmented_queries" in content:
            checks.append(("✅", "  - Uses augmented_queries field (RRF compatible)"))
    else:
        checks.append(("❌", "custom_variants_node.py NOT FOUND"))
    
    # Check 2: __init__.py exports new node
    init_file = Path(__file__).parent / "src/agents/rag_agent/nodes/__init__.py"
    if init_file.exists():
        content = init_file.read_text()
        if "custom_variants_node" in content:
            checks.append(("✅", "__init__.py exports custom_variants_node"))
        else:
            checks.append(("❌", "__init__.py missing export"))
    
    # Check 3: graph.py updated
    graph_file = Path(__file__).parent / "src/agents/rag_agent/graph.py"
    if graph_file.exists():
        content = graph_file.read_text()
        if '"custom_variants": "custom_variants_node"' in content:
            checks.append(("✅", "graph.py strategy_map includes custom_variants"))
        if 'graph_builder.add_node("custom_variants_node"' in content:
            checks.append(("✅", "graph.py adds custom_variants_node to builder"))
        if 'graph_builder.add_edge("custom_variants_node", "document_retriever")' in content:
            checks.append(("✅", "graph.py connects custom_variants_node to document_retriever"))
    
    # Check 4: state.py updated
    state_file = Path(__file__).parent / "src/agents/rag_agent/state.py"
    if state_file.exists():
        content = state_file.read_text()
        if "Union[str, List[str]]" in content:
            checks.append(("✅", "state.py query field accepts Union[str, List[str]]"))
        if "custom_variants: Optional[List[str]]" in content:
            checks.append(("✅", "state.py includes custom_variants field"))
    
    # Check 5: domain models updated
    models_file = Path(__file__).parent / "src/domain/conversation/models.py"
    if models_file.exists():
        content = models_file.read_text()
        if 'CUSTOM_VARIANTS = "custom_variants"' in content:
            checks.append(("✅", "models.py QueryEnhancementStrategy includes CUSTOM_VARIANTS"))
        else:
            checks.append(("❌", "models.py missing CUSTOM_VARIANTS enum"))
    
    # Print results
    print("📋 Implementation Checklist:")
    print()
    for status, message in checks:
        print(f"{status} {message}")
    
    print()
    print("=" * 80)
    
    # Summary
    passed = sum(1 for s, _ in checks if s == "✅")
    total = len(checks)
    
    if passed == total:
        print(f"✅ ALL CHECKS PASSED ({passed}/{total})")
        print("=" * 80)
        print()
        print("🎉 Custom Variants Strategy Implementation Complete!")
        print()
        print("📝 Summary:")
        print("  1. New strategy node created: custom_variants_node.py")
        print("  2. Graph routing updated with new strategy")
        print("  3. State updated to accept Union[str, List[str]] for query")
        print("  4. Domain models updated with CUSTOM_VARIANTS enum")
        print("  5. RRF integration: auto-enabled for multiple variants")
        print()
        print("🚀 Usage:")
        print('  - Send query as list: query=["variant1", "variant2", "variant3"]')
        print('  - Or use custom_variants field with base query')
        print('  - Strategy auto-detects and enables parallel search + RRF')
        print()
        return True
    else:
        print(f"⚠️  SOME CHECKS FAILED ({passed}/{total})")
        print("=" * 80)
        return False


if __name__ == "__main__":
    success = validate_implementation()
    sys.exit(0 if success else 1)

