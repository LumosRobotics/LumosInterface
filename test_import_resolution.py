#!/usr/bin/env python3.9
"""
Test import resolution and cross-file validation.
"""

from pathlib import Path
from lumos_idl import IDLProcessor, Config
from lumos_idl.validator.import_resolver import ImportResolver


def test_resolve_import():
    """Test basic import path resolution."""
    print("Test 1: Basic import path resolution")
    print("-" * 70)

    # Create test files
    test_dir = Path("tests/test_files/imports")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create a simple file to import
    common_types = test_dir / "common_types.msg"
    common_types.write_text("""struct Vector3
    float32 x
    float32 y
    float32 z
""")

    # Test resolver
    config = Config.default()
    config.search_paths = [test_dir]
    resolver = ImportResolver(config.search_paths)

    # Should resolve to the file we created
    resolved = resolver.resolve_import("common_types", None)

    if resolved and resolved.exists():
        print(f"✓ Import resolved to: {resolved}")
        return True
    else:
        print("✗ Failed to resolve import")
        return False


def test_resolve_with_dots():
    """Test import paths with dots (like common/geo.types)."""
    print("\nTest 2: Import paths with dots")
    print("-" * 70)

    test_dir = Path("tests/test_files/imports")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create file with dots in name
    dotted_file = test_dir / "geo.types.msg"
    dotted_file.write_text("""struct Point
    float32 x
    float32 y
""")

    config = Config.default()
    config.search_paths = [test_dir]
    resolver = ImportResolver(config.search_paths)

    resolved = resolver.resolve_import("geo.types", None)

    if resolved and resolved.exists():
        print(f"✓ Dotted import resolved to: {resolved}")
        return True
    else:
        print("✗ Failed to resolve dotted import")
        return False


def test_import_not_found():
    """Test detection of missing imports."""
    print("\nTest 3: Missing import detection")
    print("-" * 70)

    processor = IDLProcessor()

    code = """import nonexistent/module

struct Test
    uint32 id
"""

    result = processor.process_string(code, "test.msg")

    # Should fail due to missing import
    if not result.success:
        print("✓ Correctly detected missing import")
        for error in result.errors:
            if error.error_type == "import_not_found":
                print(f"  - {error.message}")
        return True
    else:
        print("✗ Should have detected missing import")
        return False


def test_circular_dependency_simple():
    """Test detection of simple circular dependency (A -> B -> A)."""
    print("\nTest 4: Simple circular dependency")
    print("-" * 70)

    test_dir = Path("tests/test_files/circular")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create file A that imports B
    file_a = test_dir / "file_a.msg"
    file_a.write_text("""import file_b

struct TypeA
    uint32 id
""")

    # Create file B that imports A (circular!)
    file_b = test_dir / "file_b.msg"
    file_b.write_text("""import file_a

struct TypeB
    string name
""")

    config = Config.default()
    config.search_paths = [test_dir]
    processor = IDLProcessor(config)

    # Process both files - need to have all files in the system to detect cycles
    result_a = processor.process_file(str(file_a))
    result_b = processor.process_file(str(file_b))

    # Manually build a combined file set and check for cycles using the resolver
    from lumos_idl.validator.import_resolver import ImportResolver
    resolver = ImportResolver(config.search_paths)

    all_files = {**result_a.parsed_files, **result_b.parsed_files}
    import_errors = resolver.validate_imports(all_files)

    # Should detect circular dependency
    has_circular_error = False
    for error in import_errors:
        if error.error_type == "circular_dependency":
            has_circular_error = True
            print(f"✓ Detected circular dependency: {error.message}")
            break

    if has_circular_error:
        return True
    else:
        print("✗ Should have detected circular dependency")
        return False


def test_dependency_graph():
    """Test dependency graph construction."""
    print("\nTest 5: Dependency graph construction")
    print("-" * 70)

    test_dir = Path("tests/test_files/deps")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create a dependency chain: C -> B -> A
    file_a = test_dir / "base.msg"
    file_a.write_text("""struct Base
    uint32 id
""")

    file_b = test_dir / "middle.msg"
    file_b.write_text("""import base

struct Middle
    uint32 id
""")

    file_c = test_dir / "top.msg"
    file_c.write_text("""import middle

struct Top
    uint32 id
""")

    config = Config.default()
    config.search_paths = [test_dir]
    resolver = ImportResolver(config.search_paths)

    # Process all files
    processor = IDLProcessor(config)
    result_a = processor.process_file(str(file_a))
    result_b = processor.process_file(str(file_b))
    result_c = processor.process_file(str(file_c))

    # Build dependency graph
    all_files = {
        **result_a.parsed_files,
        **result_b.parsed_files,
        **result_c.parsed_files,
    }

    graph = resolver.build_dependency_graph(all_files)

    # Check that graph is correct
    if len(graph) > 0:
        print(f"✓ Built dependency graph with {len(graph)} files")
        for file_path, deps in graph.items():
            print(f"  - {file_path.name} depends on {len(deps)} file(s)")
        return True
    else:
        print("✗ Failed to build dependency graph")
        return False


def test_topological_sort():
    """Test topological sorting of dependencies."""
    print("\nTest 6: Topological sort (import order)")
    print("-" * 70)

    test_dir = Path("tests/test_files/topo")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create diamond dependency: D -> B, D -> C, B -> A, C -> A
    file_a = test_dir / "a.msg"
    file_a.write_text("""struct A
    uint32 id
""")

    file_b = test_dir / "b.msg"
    file_b.write_text("""import a

struct B
    uint32 id
""")

    file_c = test_dir / "c.msg"
    file_c.write_text("""import a

struct C
    uint32 id
""")

    file_d = test_dir / "d.msg"
    file_d.write_text("""import b
import c

struct D
    uint32 id
""")

    config = Config.default()
    config.search_paths = [test_dir]
    resolver = ImportResolver(config.search_paths)
    processor = IDLProcessor(config)

    # Process all files
    all_files = {}
    for f in [file_a, file_b, file_c, file_d]:
        result = processor.process_file(str(f))
        all_files.update(result.parsed_files)

    # Get import order
    order = resolver.get_import_order(all_files)

    if order is not None:
        print(f"✓ Computed import order:")
        for i, file_path in enumerate(order):
            print(f"  {i+1}. {file_path.name}")

        # Verify A comes before B and C, and B,C come before D
        order_names = [p.name for p in order]
        a_idx = order_names.index("a.msg")
        b_idx = order_names.index("b.msg")
        c_idx = order_names.index("c.msg")
        d_idx = order_names.index("d.msg")

        if a_idx < b_idx and a_idx < c_idx and b_idx < d_idx and c_idx < d_idx:
            print("  Order is correct!")
            return True
        else:
            print("✗ Order is incorrect")
            return False
    else:
        print("✗ Failed to compute import order")
        return False


def test_transitive_dependencies():
    """Test transitive dependency collection."""
    print("\nTest 7: Transitive dependencies")
    print("-" * 70)

    test_dir = Path("tests/test_files/transitive")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create chain: C -> B -> A
    file_a = test_dir / "a.msg"
    file_a.write_text("""struct A
    uint32 id
""")

    file_b = test_dir / "b.msg"
    file_b.write_text("""import a

struct B
    uint32 id
""")

    file_c = test_dir / "c.msg"
    file_c.write_text("""import b

struct C
    uint32 id
""")

    config = Config.default()
    config.search_paths = [test_dir]
    resolver = ImportResolver(config.search_paths)
    processor = IDLProcessor(config)

    # Process all files
    all_files = {}
    for f in [file_a, file_b, file_c]:
        result = processor.process_file(str(f))
        all_files.update(result.parsed_files)

    # Get transitive dependencies of C
    c_path = file_c.resolve()
    deps = resolver.get_transitive_dependencies(c_path, all_files)

    if len(deps) == 2:  # Should have B and A
        print(f"✓ Found {len(deps)} transitive dependencies for c.msg:")
        for dep in deps:
            print(f"  - {dep.name}")
        return True
    else:
        print(f"✗ Expected 2 transitive dependencies, got {len(deps)}")
        return False


def test_valid_imports():
    """Test that valid imports pass validation."""
    print("\nTest 8: Valid imports")
    print("-" * 70)

    test_dir = Path("tests/test_files/valid_imports")
    test_dir.mkdir(parents=True, exist_ok=True)

    # Create valid import structure
    base_file = test_dir / "geometry.msg"
    base_file.write_text("""struct Vector3
    float32 x
    float32 y
    float32 z
""")

    using_file = test_dir / "transform.msg"
    using_file.write_text("""import geometry

struct Transform
    uint32 id
""")

    config = Config.default()
    config.search_paths = [test_dir]
    processor = IDLProcessor(config)

    result = processor.process_file(str(using_file))

    if result.success:
        print("✓ Valid imports accepted")
        return True
    else:
        print("✗ Valid imports should be accepted")
        result.print_errors()
        return False


def main():
    """Run all import resolution tests."""
    print("=" * 70)
    print("LumosInterface Import Resolution Tests")
    print("=" * 70)
    print()

    tests = [
        test_resolve_import,
        test_resolve_with_dots,
        test_import_not_found,
        test_circular_dependency_simple,
        test_dependency_graph,
        test_topological_sort,
        test_transitive_dependencies,
        test_valid_imports,
    ]

    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"\n✗ Test failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append(False)

    print()
    print("=" * 70)
    passed = sum(results)
    total = len(results)
    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("✓ All import resolution tests passed!")
        return 0
    else:
        print(f"⚠ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
