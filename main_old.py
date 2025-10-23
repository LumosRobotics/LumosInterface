import os
from pathlib import Path
from collections import defaultdict
from lark import Lark, Transformer, Tree, Token

GRAMMAR_PATH = "grammar/message.lark"
INTERFACE_ROOT = Path("interface")

with open(GRAMMAR_PATH) as f:
    grammar = f.read()

parser = Lark(grammar, parser="lalr", start="start", propagate_positions=True)

parsed_files = {}  # Path -> Tree
defined_types_by_file = defaultdict(set)  # Path -> set of fully-qualified type names
imported_files_by_file = defaultdict(set)  # Path -> set of imported Paths


def file_namespace(path: Path) -> str:
    rel_path = path.relative_to(INTERFACE_ROOT).with_suffix("")
    return ".".join(rel_path.parts)


def parse_interface_file(file_path: Path):
    if file_path in parsed_files:
        return parsed_files[file_path]

    with open(file_path) as f:
        content = f.read()

    tree = parser.parse(content)
    parsed_files[file_path] = tree

    for import_stmt in tree.find_data("import_stmt"):
        import_path_tree = import_stmt.children[0]
        parts = [child.value for child in import_path_tree.children if child.type == "CNAME"]
        import_rel_path = Path(*parts).with_suffix(".msg")
        import_file = INTERFACE_ROOT / import_rel_path

        if not import_file.exists():
            raise FileNotFoundError(f"Import not found: {import_file}")

        parse_interface_file(import_file)
        imported_files_by_file[file_path].add(import_file)

    return tree


def parse_all_interfaces():
    for path in INTERFACE_ROOT.rglob("*.msg"):
        parse_interface_file(path)

    print("Parsed files:")
    for f in parsed_files:
        print(" -", f)

    return parsed_files


def extract_namespaced_type(field_node: Tree):
    """
    Given a struct_or_enum_ref field node, extracts namespace parts and typename.

    Returns:
        (namespaces: list[str], typename: str)
    """
    namespaced_type_node = field_node.children[0]

    if isinstance(namespaced_type_node, Tree) and namespaced_type_node.data == "namespaced_type":
        parts = [token.value for token in namespaced_type_node.children]
    elif isinstance(namespaced_type_node, Token):  # fallback: single unqualified type
        parts = [namespaced_type_node.value]
    else:
        raise TypeError(f"Unexpected type node: {namespaced_type_node}")

    if len(parts) == 1:
        return [], parts[0]
    else:
        return parts[:-1], parts[-1]



def collect_defined_types():
    for file_path, tree in parsed_files.items():
        namespace = file_namespace(file_path)

        for node in tree.find_data("struct_def"):
            typename = node.children[0].value
            fq_name = f"{namespace}.{typename}"
            defined_types_by_file[file_path].add(fq_name)

        for node in tree.find_data("enum_def"):
            typename = node.children[0].value
            fq_name = f"{namespace}.{typename}"
            defined_types_by_file[file_path].add(fq_name)


def get_visible_types_for(file_path: Path) -> set[str]:
    visible = set(defined_types_by_file[file_path])
    for imported in imported_files_by_file[file_path]:
        visible |= defined_types_by_file[imported]
    return visible


def validate_types():
    print("\nValidating types...")
    errors = []

    primitive_types = {
        "bool", "float32", "float64",
        "int8", "int16", "int32", "int64",
        "uint8", "uint16", "uint32", "uint64"
    }

    for file_path, tree in parsed_files.items():
        current_ns = file_namespace(file_path)
        visible_types = get_visible_types_for(file_path)

        for field_node in tree.find_data("struct_or_enum_ref"):
            namespaces, typename = extract_namespaced_type(field_node)
            full_name = ".".join(namespaces + [typename]) if namespaces else f"{current_ns}.{typename}"
            field_name = field_node.children[1].value

            if typename in primitive_types:
                continue

            if full_name not in visible_types:
                errors.append(
                    f" - {file_path}: Unknown type '{full_name}' used in field '{field_name}'"
                )

    if errors:
        print("Errors found:")
        for err in errors:
            print(err)
    else:
        print("All types valid!")


if __name__ == "__main__":
    trees = parse_all_interfaces()
    collect_defined_types()
    validate_types()
