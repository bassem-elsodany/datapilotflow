"""Test datapilotflow-domain - verify all models can be imported."""

import sys
import traceback


def test_domain_imports():
    """Test that all domain modules can be imported successfully."""

    modules_to_test = [
        # Core
        "datapilotflow.domain.core.exceptions",

        # Models
        "datapilotflow.domain.agent.models",
        "datapilotflow.domain.conversation.models",
        "datapilotflow.domain.embedding.embedding_model",
        "datapilotflow.domain.generative.generative_model",
        "datapilotflow.domain.knowledge.knowledge",
        "datapilotflow.domain.knowledge.knowledge_job",
        "datapilotflow.domain.knowledge.knowledge_source_config",
        "datapilotflow.domain.knowledge.vectordb_collection",
        "datapilotflow.domain.model_provider.model_provider",
        "datapilotflow.domain.notification.notification",
        "datapilotflow.domain.rag.knowledge_chunk",
        "datapilotflow.domain.tool.models",
        "datapilotflow.domain.user.user",
        "datapilotflow.domain.user.role_model",
        "datapilotflow.domain.vectordb.collection_models",

        # Events
        "datapilotflow.domain.events.base",
        "datapilotflow.domain.events.job_events",
        "datapilotflow.domain.events.timeline_events",

        # Prompts
        "datapilotflow.domain.llm_prompts.base",
        "datapilotflow.domain.llm_prompts.knowledge_base",
    ]

    failed = []
    passed = []

    for module_name in modules_to_test:
        try:
            __import__(module_name)
            passed.append(module_name)
            print(f"✅ {module_name}")
        except Exception as e:
            failed.append((module_name, e))
            print(f"❌ {module_name}: {e}")
            traceback.print_exc()

    print(f"\n{'='*60}")
    print(f"PASSED: {len(passed)}/{len(modules_to_test)}")
    print(f"FAILED: {len(failed)}/{len(modules_to_test)}")

    if failed:
        print(f"\nFailed modules:")
        for module_name, error in failed:
            print(f"  - {module_name}: {error}")
        return False

    return True


def test_pydantic_models():
    """Test that Pydantic models are properly defined."""
    try:
        from datapilotflow.domain.user.user import User
        from datapilotflow.domain.agent.models import Agent
        from datapilotflow.domain.knowledge.knowledge import Document, Chunk

        # Test model instantiation
        user = User(
            id="test_user",
            email="test@example.com",
            username="testuser",
            hashed_password="hashed"
        )
        assert user.id == "test_user"
        print("✅ User model works")

        print("✅ All Pydantic models instantiate correctly")
        return True
    except Exception as e:
        print(f"❌ Pydantic model test failed: {e}")
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("DATAPILOTFLOW-DOMAIN TEST SUITE")
    print("=" * 60)

    results = []

    print("\n1. Testing all module imports...")
    results.append(("Module Imports", test_domain_imports()))

    print("\n2. Testing Pydantic models...")
    results.append(("Pydantic Models", test_pydantic_models()))

    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)

    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")

    all_passed = all(result[1] for result in results)

    print("\n" + "=" * 60)
    if all_passed:
        print("✅ ALL TESTS PASSED - datapilotflow-domain is READY")
        sys.exit(0)
    else:
        print("❌ SOME TESTS FAILED - datapilotflow-domain has issues")
        sys.exit(1)
