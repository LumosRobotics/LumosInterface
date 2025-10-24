#!/usr/bin/env python3.9
"""
Standalone test for collection types (array, matrix, tensor) - no pytest required.
"""

from lark import Lark
from lark.exceptions import LarkError
from pathlib import Path
from indentation_preprocessor import IndentationPreprocessor


def load_parser():
    """Load the grammar file and create parser."""
    grammar_file = Path("grammar/message.lark")

    with open(grammar_file) as f:
        grammar = f.read()

    return Lark(grammar, parser="lalr", start="start", propagate_positions=True)


def preprocess(code):
    """Preprocess indentation."""
    preprocessor = IndentationPreprocessor()
    return preprocessor.process(code)


def test_array_dynamic_size():
    """Test dynamic arrays (no size specified)."""
    parser = load_parser()

    code = """struct Test
    array<uint8> data
    array<string> messages
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        arrays = list(tree.find_data("array_type"))
        if len(arrays) == 2:
            print("✓ dynamic size arrays")
            passed += 1
        else:
            print(f"✗ expected 2 arrays, got {len(arrays)}")
            failed += 1
    except LarkError as e:
        print(f"✗ dynamic arrays: {e}")
        failed += 1

    return passed, failed


def test_array_fixed_size():
    """Test fixed-size arrays."""
    parser = load_parser()

    code = """struct Test
    array<uint8, 12> satellite_ids
    array<float32, 3> position_xyz
    array<string, 50> log_entries
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        arrays = list(tree.find_data("array_type"))
        fixed_sizes = list(tree.find_data("fixed_size"))

        if len(arrays) == 3 and len(fixed_sizes) == 3:
            print("✓ fixed size arrays")
            passed += 1
        else:
            print(f"✗ fixed arrays: got {len(arrays)} arrays, {len(fixed_sizes)} sizes")
            failed += 1
    except LarkError as e:
        print(f"✗ fixed arrays: {e}")
        failed += 1

    return passed, failed


def test_array_max_size():
    """Test arrays with max size constraint."""
    parser = load_parser()

    code = """struct Test
    array<uint8, max=100> sensor_readings
    array<string, max=50> log_entries
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        arrays = list(tree.find_data("array_type"))
        max_sizes = list(tree.find_data("max_size"))

        if len(arrays) == 2 and len(max_sizes) == 2:
            print("✓ max size arrays")
            passed += 1
        else:
            print(f"✗ max arrays: got {len(arrays)} arrays, {len(max_sizes)} max specs")
            failed += 1
    except LarkError as e:
        print(f"✗ max size arrays: {e}")
        failed += 1

    return passed, failed


def test_array_user_types():
    """Test arrays with user-defined element types."""
    parser = load_parser()

    code = """struct Test
    array<Vector3, 10> positions
    array<Quaternion> rotations
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        arrays = list(tree.find_data("array_type"))
        user_elem_types = list(tree.find_data("user_element_type"))

        if len(arrays) == 2 and len(user_elem_types) == 2:
            print("✓ arrays with user-defined types")
            passed += 1
        else:
            print(f"✗ user type arrays failed")
            failed += 1
    except LarkError as e:
        print(f"✗ user type arrays: {e}")
        failed += 1

    return passed, failed


def test_array_qualified_types():
    """Test arrays with qualified element types."""
    parser = load_parser()

    code = """struct Test
    array<common::geometry::Vector3, 5> path
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        arrays = list(tree.find_data("array_type"))
        qualified_elem_types = list(tree.find_data("qualified_element_type"))

        if len(arrays) == 1 and len(qualified_elem_types) == 1:
            print("✓ arrays with qualified types")
            passed += 1
        else:
            print(f"✗ qualified type arrays failed")
            failed += 1
    except LarkError as e:
        print(f"✗ qualified type arrays: {e}")
        failed += 1

    return passed, failed


def test_matrix_fixed_size():
    """Test matrix with fixed dimensions."""
    parser = load_parser()

    code = """struct Test
    matrix<uint8, 640, 480> image
    matrix<float32, 3, 3> rotation_matrix
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        matrices = list(tree.find_data("matrix_type"))
        fixed_sizes = list(tree.find_data("fixed_size"))

        if len(matrices) == 2 and len(fixed_sizes) == 4:  # 2 dimensions per matrix
            print("✓ fixed size matrices")
            passed += 1
        else:
            print(f"✗ matrices: got {len(matrices)} matrices, {len(fixed_sizes)} sizes")
            failed += 1
    except LarkError as e:
        print(f"✗ fixed matrices: {e}")
        failed += 1

    return passed, failed


def test_matrix_dynamic_dimensions():
    """Test matrix with dynamic dimensions (?)."""
    parser = load_parser()

    code = """struct Test
    matrix<uint8, ?, 480> camera_image
    matrix<float32, ?, ?> dynamic_matrix
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        matrices = list(tree.find_data("matrix_type"))
        dynamic_sizes = list(tree.find_data("dynamic_size"))
        fixed_sizes = list(tree.find_data("fixed_size"))

        if len(matrices) == 2 and len(dynamic_sizes) == 3 and len(fixed_sizes) == 1:
            print("✓ matrices with dynamic dimensions")
            passed += 1
        else:
            print(f"✗ dynamic matrices: {len(matrices)} matrices, {len(dynamic_sizes)} dynamic, {len(fixed_sizes)} fixed")
            failed += 1
    except LarkError as e:
        print(f"✗ dynamic matrices: {e}")
        failed += 1

    return passed, failed


def test_tensor_fixed_dimensions():
    """Test tensor with fixed dimensions."""
    parser = load_parser()

    code = """struct Test
    tensor<float32, 10, 10, 10> grid_3d
    tensor<float32, 10, 10, 10, 4> tensor_4d
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        tensors = list(tree.find_data("tensor_type"))
        fixed_sizes = list(tree.find_data("fixed_size"))

        if len(tensors) == 2 and len(fixed_sizes) == 7:  # 3 + 4 dimensions
            print("✓ fixed size tensors")
            passed += 1
        else:
            print(f"✗ tensors: got {len(tensors)} tensors, {len(fixed_sizes)} sizes")
            failed += 1
    except LarkError as e:
        print(f"✗ fixed tensors: {e}")
        failed += 1

    return passed, failed


def test_tensor_mixed_dimensions():
    """Test tensor with mixed fixed and dynamic dimensions."""
    parser = load_parser()

    code = """struct Test
    tensor<float32, 100, ?, 3> voxel_grid
    tensor<uint8, ?, ?, ?> fully_dynamic
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        tensors = list(tree.find_data("tensor_type"))
        dynamic_sizes = list(tree.find_data("dynamic_size"))
        fixed_sizes = list(tree.find_data("fixed_size"))

        if len(tensors) == 2 and len(dynamic_sizes) == 4 and len(fixed_sizes) == 2:
            print("✓ tensors with mixed dimensions")
            passed += 1
        else:
            print(f"✗ mixed tensors: {len(tensors)} tensors, {len(dynamic_sizes)} dynamic, {len(fixed_sizes)} fixed")
            failed += 1
    except LarkError as e:
        print(f"✗ mixed tensors: {e}")
        failed += 1

    return passed, failed


def test_collections_with_optional():
    """Test optional collection fields."""
    parser = load_parser()

    code = """struct Test
    optional array<uint8, 100> data
    optional matrix<float32, 3, 3> transform
    optional tensor<float32, 10, 10, 10> grid
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        collection_fields = list(tree.find_data("collection_type_field"))

        # Check all are optional
        all_optional = all(
            field.children[0].type == "OPTIONAL" if hasattr(field.children[0], "type") else False
            for field in collection_fields
        )

        if len(collection_fields) == 3 and all_optional:
            print("✓ optional collection fields")
            passed += 1
        else:
            print(f"✗ optional collections: {len(collection_fields)} fields, all_optional={all_optional}")
            failed += 1
    except LarkError as e:
        print(f"✗ optional collections: {e}")
        failed += 1

    return passed, failed


def test_collections_with_inline_attributes():
    """Test collection fields with inline attributes."""
    parser = load_parser()

    code = """struct Test
    array<uint8, 100> data @description("Sensor data"), @encoding("binary")
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        collection_fields = list(tree.find_data("collection_type_field"))
        inline_attrs = list(tree.find_data("inline_attribute"))

        if len(collection_fields) == 1 and len(inline_attrs) == 2:
            print("✓ collections with inline attributes")
            passed += 1
        else:
            print(f"✗ collections with inline attrs failed")
            failed += 1
    except LarkError as e:
        print(f"✗ collections with inline attributes: {e}")
        failed += 1

    return passed, failed


def test_collections_with_indented_attributes():
    """Test collection fields with indented attributes."""
    parser = load_parser()

    code = """struct Test
    matrix<float32, 640, 480> image
        description: "Camera image"
        format: "RGB"
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        collection_fields = list(tree.find_data("collection_type_field"))
        field_attrs = list(tree.find_data("field_attributes"))

        if len(collection_fields) == 1 and len(field_attrs) == 1:
            print("✓ collections with indented attributes")
            passed += 1
        else:
            print(f"✗ collections with indented attrs failed")
            failed += 1
    except LarkError as e:
        print(f"✗ collections with indented attributes: {e}")
        failed += 1

    return passed, failed


def test_full_example():
    """Test comprehensive example with all collection features."""
    parser = load_parser()

    code = """struct SensorData
    // Fixed size arrays
    array<uint8, 12> satellite_ids
    array<float32, 3> position_xyz

    // Dynamic arrays
    array<uint8> data_payload

    // Max size arrays
    array<uint8, max=100> sensor_readings

    // Matrix
    matrix<uint8, 640, 480> mat

    // Dynamic matrix
    matrix<uint8, ?, 480> camera_image

    // Tensors
    tensor<float32, 100, ?, 3> voxel_grid
    tensor<float32, 10, 10, 10, 4> tensor_4d

    // Optional collection
    optional array<string, max=50> log_entries
"""

    passed = 0
    failed = 0

    try:
        processed = preprocess(code)
        tree = parser.parse(processed)

        arrays = list(tree.find_data("array_type"))
        matrices = list(tree.find_data("matrix_type"))
        tensors = list(tree.find_data("tensor_type"))

        if len(arrays) == 5 and len(matrices) == 2 and len(tensors) == 2:
            print(f"✓ full example ({len(arrays)} arrays, {len(matrices)} matrices, {len(tensors)} tensors)")
            passed += 1
        else:
            print(f"✗ full example: {len(arrays)} arrays, {len(matrices)} matrices, {len(tensors)} tensors")
            failed += 1
    except LarkError as e:
        print(f"✗ full example: {e}")
        failed += 1

    return passed, failed


def main():
    """Run all tests."""
    print("=" * 70)
    print("Collection Type Tests (Array, Matrix, Tensor)")
    print("=" * 70)
    print()

    print("Array Tests:")
    print("-" * 70)
    results = [test_array_dynamic_size()]
    results.append(test_array_fixed_size())
    results.append(test_array_max_size())
    results.append(test_array_user_types())
    results.append(test_array_qualified_types())

    print()
    print("Matrix Tests:")
    print("-" * 70)
    results.append(test_matrix_fixed_size())
    results.append(test_matrix_dynamic_dimensions())

    print()
    print("Tensor Tests:")
    print("-" * 70)
    results.append(test_tensor_fixed_dimensions())
    results.append(test_tensor_mixed_dimensions())

    print()
    print("Collections with Modifiers and Attributes:")
    print("-" * 70)
    results.append(test_collections_with_optional())
    results.append(test_collections_with_inline_attributes())
    results.append(test_collections_with_indented_attributes())

    print()
    print("Comprehensive Example:")
    print("-" * 70)
    results.append(test_full_example())

    print()
    print("=" * 70)

    total_pass = sum(p for p, f in results)
    total_fail = sum(f for p, f in results)
    total = total_pass + total_fail

    print(f"Results: {total_pass}/{total} tests passed")

    if total_fail > 0:
        print(f"⚠ {total_fail} tests failed")
        return 1
    else:
        print("✓ All tests passed!")
        return 0


if __name__ == "__main__":
    exit(main())
