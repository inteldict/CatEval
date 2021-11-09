from collections import OrderedDict


class Terminal:

    def __init__(self, label, index):
        self.label = label
        self.index = index

    def __str__(self):
        return self.label

    def __repr__(self):
        return str(self)

    def neat_str(self, level=0):
        return str(self)

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        else:
            return False

    def __ne__(self, other):
        return not self.__eq__(other)


class Node:

    def __init__(self, label, start_index, end_index):
        self.label = label
        self.children = []
        self.start = start_index
        self.end = end_index
        self.parent = None
        self.keep = False

    def add_child(self, child):
        self.children.append(child)
        child.parent = self

    def add_leaf(self, leaf):
        self.children.append(leaf)

    def neat_str(self, level=0):
        result = '(' + self.label
        spacing = '\t' * (level + 1)
        if len(self.children) > 1:
            for child in self.children:
                result += os.linesep + spacing + child.neat_str(level + 1)
        else:
            result += ' ' + self.children[0].neat_str(level)
        return result + ')'

    def single_str(self):
        result = '(' + self.label
        for child in self.children:
            if isinstance(child, Terminal):
                result += ' ' + child.label
            else:
                result += child.single_str()
        return result + ')'

    def core_label(self):
        if '-' in self.label:
            return self.label.split('-')[0]
        elif '=' in self.label:
            return self.label.split('=')[0]

        return self.label

    def __repr__(self):
        return self.single_str()

    def leaves(self):
        for child in self.children:
            if isinstance(child, Terminal):
                yield child
            else:
                yield from child.leaves()

    def nonterminals(self):
        yield self
        for child in self.children:
            if isinstance(child, Node):
                yield from child.nonterminals()

    def pos_tags(self):
        has_nonterm = False
        for child in self.children:
            if isinstance(child, Node):
                has_nonterm = True
                yield from child.pos_tags()
        if not has_nonterm:
            yield self.label

    def nonterminal_spans(self):
        spans = [(self.start, self.end, self.core_label()), ]
        for child in self.children:
            if not isinstance(child, Terminal):
                spans.extend(child.spans())
        return spans

    def layered_spans(self):
        visited = OrderedDict()
        queue = [(self, 0)]
        while queue:
            vertex, depth = queue.pop(0)
            non_terminal = False
            if vertex not in visited and isinstance(vertex, Node):
                for child in vertex.children:
                    if isinstance(child, Node):
                        non_terminal = True
                        if child not in visited:
                            queue.append((child, depth + 1))
                if non_terminal:
                    visited[vertex] = depth
        return visited

    def spans(self):
        spans = [(self.start, self.end, self.label), ]
        non_terminal = False
        for child in self.children:
            if isinstance(child, Node):
                non_terminal = True
                spans.extend(child.spans())
        if not non_terminal:  # by EVALB convention POS spans do not participate in evaluation (not even for labelled prec and recall)
            return []
        return spans

    def find_by_POS(self, pos):
        labels = []
        for child in self.children:
            if isinstance(child, Terminal):
                if self.label.startswith(pos):
                    labels.append(child.label)
            else:
                labels.extend(child.find_by_POS(pos))
        return labels

    def find_by_WORD(self, keywords):
        nodes = []
        for child in self.children:
            if isinstance(child, Terminal):
                if child.label.lower() in keywords:
                    nodes.append(self)
            else:
                nodes.extend(child.find_by_WORD(keywords))
        return nodes
