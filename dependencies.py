import ast
import argparse
import subprocess
from collections import defaultdict


class Visitor:
    def __call__(self, filename):
        self.items = {}
        with open(filename) as fp:
            tree = ast.parse(fp.read(), filename=filename)
        assert isinstance(tree, ast.Module)
        for toplevel in tree.body:
            for name in self.visit(toplevel, prefix='name_of_'):
                self.items[name] = toplevel
        self.edge_lists = defaultdict(list)
        for toplevel in tree.body:
            name = self.visit(toplevel, prefix='name_of_')
            self.current = name[0] if len(name) == 1 else None
            if not self.current:
                print("No current", name)
            self.visit(toplevel, prefix='visit_')
        return self.as_graph()

    def visit(self, object, prefix='visit_'):
        try:
            method = getattr(self, prefix + type(object).__name__)
        except AttributeError:
            method = getattr(self, prefix + 'generic')
        return method(object)

    def visit_generic(self, node):
        for c in ast.iter_child_nodes(node):
            self.visit(c)

    def name_of_Import(self, stm):
        return [
            alias.asname or alias.name
            for alias in stm.names
        ]

    def name_of_ImportFrom(self, stm):
        return self.name_of_Import(stm)

    def name_of_Assign(self, stm):
        assert all(isinstance(target, ast.Name)
                   for target in stm.targets)
        return [
            target.id
            for target in stm.targets
        ]

    def name_of_If(self, stm):
        return ['__file_scope__']

    def name_of_Name(self, name):
        return [name.id]

    def name_of_Attribute(self, expr):
        '''
        >>> expr = ast.parse('foo.bar').body[0].value
        >>> Visitor().name_of_Attribute(expr)
        ['foo.bar']
        '''
        tail = '.' + expr.attr
        try:
            return [n + tail for n in self.visit(expr.value, 'name_of_')]
        except TypeError:
            return []

    def name_of_generic(self, stm):
        name = getattr(stm, 'name', None)
        if isinstance(name, str):
            return [name]
        else:
            raise TypeError(type(stm))

    def visit_Attribute(self, node):
        if isinstance(node.ctx, ast.Load):
            name = self.name_of_Attribute(node)
            if name:
                assert len(name) == 1, name
                if name[0] in self.items:
                    print("Add edge", self.current, name[0])
                    self.edge_lists[self.current].append(name[0])
        self.visit_generic(node)

    def visit_Name(self, node):
        if isinstance(node.ctx, ast.Load) and node.id in self.items:
            # print("Add edge", self.current, node.id)
            self.edge_lists[self.current].append(node.id)

    def as_graph(self):
        from graphviz import Digraph

        dot = Digraph()
        for name in sorted(self.items.keys()):
            dot.node(name)
        for name, edges in sorted(self.edge_lists.items()):
            for n in sorted(set(edges)):
                dot.edge(name, n)
        return dot


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('filename')
    args = parser.parse_args()
    dot = Visitor()(args.filename)
    print(dot.source)
    xdot = subprocess.Popen(
        ('xdot', '-'), stdin=subprocess.PIPE, universal_newlines=True)
    with xdot:
        xdot.communicate(dot.source)


if __name__ == '__main__':
    main()
