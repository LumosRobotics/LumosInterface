import os
from pathlib import Path
from lark import Lark, Transformer, Tree

GRAMMAR_PATH = "grammar/message.lark"
INTERFACE_ROOT = Path("interface")

with open(GRAMMAR_PATH) as f:
    grammar = f.read()

parser = Lark(grammar, parser="lalr", start="start", propagate_positions=True)

parsed_files = {}  # path -> Tree

def parse_interface_file(file_path: Path):
    if file_path in parsed_files:
        return parsed_files[file_path]

    with open(file_path) as f:
        content = f.read()

    tree = parser.parse(content)
    parsed_files[file_path] = tree

    # Handle imports
    for import_stmt in tree.find_data("import_stmt"):
        # import_stmt.children[0] is the import_path (a Tree)
        import_path_tree = import_stmt.children[0]

        # Reconstruct path from its tokens
        parts = [child.value for child in import_path_tree.children if child.type == "CNAME"]
        import_rel_path = Path(*parts).with_suffix(".msg")
        import_file = INTERFACE_ROOT / import_rel_path

        if not import_file.exists():
            raise FileNotFoundError(f"Import not found: {import_file}")

        parse_interface_file(import_file)


    return tree


def parse_all_interfaces():
    for path in INTERFACE_ROOT.rglob("*.msg"):
        parse_interface_file(path)

    print("Parsed files:")
    for f in parsed_files:
        print(" -", f)

    return parsed_files

if __name__ == "__main__":
    trees = parse_all_interfaces()
    for path, tree in trees.items():
        print(f"\n==== {path} ====")
        print(tree.pretty())
