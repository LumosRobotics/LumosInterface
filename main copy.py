from lark import Lark

grammar_file = "grammar/message.lark"
msg_file = "interface/simple.msg"

with open(grammar_file) as f:
    grammar = f.read()

parser = Lark(grammar, parser="lalr")

with open(msg_file) as f:
    msg = f.read()

tree = parser.parse(msg)
print(tree.pretty())
