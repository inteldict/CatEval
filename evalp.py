from node import Node, Terminal
from utils import open_gold_eval_files


class EvalStat(object):

    def __init__(self, num_gold_spans=0, num_test_spans=0, num_matching_spans=0, num_matching_tags=0, num_all_tags=0):
        self.num_gold_spans = num_gold_spans
        self.num_test_spans = num_test_spans
        self.num_matching_spans = num_matching_spans
        self.num_matching_tags = num_matching_tags
        self.num_all_tags = num_all_tags

    def row_str(self, sentece_id: int) -> str:
        return "{:>5}\t{:>5}\t{:>5}\t{:>5}\t{:.2f}".format(sentece_id, self.num_matching_spans, self.num_gold_spans,
                                                           self.num_test_spans,
                                                           self.num_matching_tags / self.num_all_tags)

    def bottom_str(self) -> str:
        result = f"Gold spans: {self.num_gold_spans}\nProposed spans: {self.num_test_spans}\nCorrect spans: {self.num_matching_spans}\n"

        recall = self.num_matching_spans / self.num_gold_spans
        result += "Recall:\t{:.2f}\n".format(recall * 100)

        precision = self.num_matching_spans / self.num_test_spans
        result += "Precision:\t{:.2f}\n".format(precision * 100)

        f1 = (2 * precision * recall) / (precision + recall)
        result += "F-score:\t{:.2f}\n".format(f1 * 100)

        result += "Tagging accuracy:\t{:.2f}\n".format(self.num_matching_tags / self.num_all_tags * 100)
        return result

    def header(self) -> str:
        return """  Sent.                        Matched  Bracket   Cross        Correct Tag
 ID  Len.  Recal  Prec.  Bracket gold test Bracket Words  Tags Accracy
============================================================================
"""

    def __add__(self, o):
        return EvalStat(self.num_gold_spans + o.num_gold_spans,
                        self.num_test_spans + o.num_test_spans,
                        self.num_matching_spans + o.num_matching_spans,
                        self.num_matching_tags + o.num_matching_tags,
                        self.num_all_tags + o.num_all_tags)


def parseBrackets(brackets):
    unmatched_brackets = 0
    parent_node = None
    node = ''
    word_index = 0
    for ch in brackets:
        if ch == '(':
            node = node.strip()
            unmatched_brackets += 1
            if node:
                nonterminal = Node(node, word_index, word_index)
                if parent_node:
                    parent_node.add_child(nonterminal)
                    parent_node.end = nonterminal.end
                parent_node = nonterminal
                node = ''
        elif ch == ')':
            unmatched_brackets -= 1
            node = node.strip()
            if node:
                terms = node.split()
                if len(terms) > 1:
                    preterm = Node(terms[0], word_index, word_index)
                    term = Terminal(' '.join(terms[1:]), word_index)
                    word_index += 1
                    preterm.add_leaf(term)
                    if parent_node:
                        parent_node.add_child(preterm)
                        parent_node.end = preterm.end
                    else:
                        return preterm
                node = ''
            else:
                if unmatched_brackets:
                    parent_node.parent.end = parent_node.end
                    parent_node = parent_node.parent
        else:
            node += ch
    assert unmatched_brackets == 0, "Malformed sentence: unmatched brackets: {} in {}".format(unmatched_brackets,
                                                                                              brackets)
    return parent_node


def compare_parses(gold, eval, labeled=False):
    gold_spans = gold.spans()
    eval_spans = eval.spans()

    if labeled:
        matched_spans = len(set(gold_spans).intersection(set(eval_spans)))
    else:
        gold_bracketed_spans = set((span[0], span[1]) for span in gold_spans)
        matched_spans = 0
        eval_bracketed_spans = set((span[0], span[1]) for span in eval_spans)
        for span in eval_bracketed_spans:
            if span in gold_bracketed_spans:
                matched_spans += 1

    return len(gold_spans), len(eval_spans), matched_spans


def label_accuracy(gold_pos, eval_pos):
    total_tags = len(eval_pos)
    correct_tags = 0
    for gold, eval in zip(gold_pos, eval_pos):
        if gold == eval:
            correct_tags += 1
    return correct_tags, total_tags


def evalp(gold_file, eval_file, labeled=False):
    num_sentences = 0
    num_error_sentences = 0
    num_skipped_sentences = 0

    total_eval = EvalStat()

    print(total_eval.header())

    for gold_brackets in gold_file:
        num_sentences += 1
        gold_brackets = gold_brackets.strip()
        if not gold_brackets:
            continue
        test_brackets = next(eval_file).strip()
        if not test_brackets:
            num_error_sentences += 1
            continue
        gold = parseBrackets(gold_brackets)
        eval = parseBrackets(test_brackets)

        if eval.end != gold.end:
            print(f"{num_sentences}: Dismatch of number of words in\ngold:{gold}\ntest:{eval}")
            num_error_sentences += 1
            continue

        eval_set = set(str(l) for l in eval.leaves())
        gold_set = set(str(l) for l in gold.leaves())
        if eval_set != gold_set:
            new_eval_words = eval_set - gold_set
            new_gold_words = gold_set - eval_set
            print(f"{num_sentences}: Words unmatch {new_gold_words} | {new_eval_words}")
            num_skipped_sentences += 1
            continue

        num_gold_spans, num_test_spans, num_matching_spans = compare_parses(gold, eval, labeled)
        num_matching_tags, num_all_tags = label_accuracy(tuple(gold.pos_tags()), tuple(eval.pos_tags()))
        row = EvalStat(num_gold_spans, num_test_spans, num_matching_spans, num_matching_tags, num_all_tags)
        print(row.row_str(num_sentences))
        total_eval += row

    return total_eval, num_error_sentences, num_skipped_sentences, num_sentences


def nodes_to_spans(nodes):
    for node in nodes:
        yield node.start, node.end


def nodes_to_parent_spans(nodes):
    for node in nodes:
        parent = node.parent
        yield parent.start, parent.end


def nodes_to_parent_spans_of_cat(nodes, cat):
    for node in nodes:
        parent = node.parent
        if parent.label.startswith(cat):
            yield parent.start, parent.end


def no_sentence_coord(nodes):
    for node in nodes:
        parent = node.parent
        parent_lab = parent.label
        if any(parent_lab.startswith(cat) for cat in COMPLEX_COORD):
            continue
        print("GOLD: {},{} {}".format(parent.start, parent.end, parent.label))
        yield parent.start, parent.end


def no_tueba_sentence_coord(nodes):
    for node in nodes:
        parent = node.parent
        while len(parent.children) <= 1:
            parent = parent.parent

        parent_lab = parent.label
        if any(parent_lab.startswith(cat) for cat in TUEBA_COMPLEX_COORD):
            continue
        print("EVAL: {},{} {}".format(parent.start, parent.end, parent.label))
        yield parent.start, parent.end


def find_mismatched_labels(gold, eval):
    gold_spans = set(gold.spans())
    mismatched_spans = []
    for eval_span in eval.spans():
        if eval_span not in gold_spans:
            mismatched_spans.append(eval_span)
    mismatched_spans.sort(key=lambda span: (span[0], span[1]))
    return mismatched_spans


def find_mismatched_brackets(gold, eval):
    gold_spans = set((span[0], span[1]) for span in gold.spans())
    mismatched_spans = []
    for eval_span in eval.spans():
        sub_span = (eval_span[0], eval_span[1])
        if sub_span not in gold_spans:
            mismatched_spans.append(eval_span)
    mismatched_spans.sort(key=lambda span: (span[0], span[1]))
    return mismatched_spans


if __name__ == "__main__":
    gold_file, eval_file = open_gold_eval_files()

    total_eval, num_error_sentences, num_skipped_sentences, num_sentences = evalp(
        gold_file,
        eval_file,
        labeled=False)

    print("Number of analyzed sentences: {}".format(num_sentences))
    print("Error sentences: {}".format(num_error_sentences))
    print("Skipped sentences: {}".format(num_skipped_sentences))
    print(total_eval.bottom_str())

    gold_file.close()
    eval_file.close()
