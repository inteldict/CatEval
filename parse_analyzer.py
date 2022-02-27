import os
from collections import Counter

from evalp import parseBrackets
from utils import open_gold_eval_files

ERROR_CATEGORIES = ("PART_TAG_MISMATCH", "TAG_MISMATCH", "PART_WRONG_LABEL_SPAN", "WRONG_LABEL_SPAN", "WRONG_SPAN")


class FailureAnalyzer:

    def __init__(self, mismatched_tag_spans=None, part_mismatched_tag_spans=None, failed_spans=None,
                 wrong_label_spans=None, part_wrong_label_spans=None, proposal=None, node_counter=None, sentence_id=0,
                 alternative_id=0, sentence_len=0):
        self.mismatched_tag_spans = mismatched_tag_spans
        self.part_mismatched_tag_spans = part_mismatched_tag_spans
        self.failed_spans = failed_spans
        self.wrong_label_spans = wrong_label_spans
        self.part_wrong_label_spans = part_wrong_label_spans
        self.proposal = proposal
        self.node_counter = node_counter

        self.sentence_id = sentence_id
        self.alternative_id = alternative_id
        self.sentence_len = sentence_len

    @staticmethod
    def init_default():
        return FailureAnalyzer([], [], [], [], [], Proposal({}, {}, {}, {}), Counter())

    def all_errors(self) -> list:
        yield from self.part_mismatched_tag_spans
        yield from self.mismatched_tag_spans
        yield from self.part_wrong_label_spans
        yield from self.wrong_label_spans
        yield from self.failed_spans

    def __str__(self):
        prefix = "{:>5} {:>5} {:>3}\t".format(self.sentence_id, self.alternative_id, self.sentence_len)
        tag = f"{ERROR_CATEGORIES[0]}\t"
        result = ''
        for span in self.part_mismatched_tag_spans:
            result += prefix + tag + str(span) + os.linesep

        tag = f"{ERROR_CATEGORIES[1]}\t"
        for span in self.mismatched_tag_spans:
            result += prefix + tag + str(span) + os.linesep

        tag = f"{ERROR_CATEGORIES[2]}\t"
        for span in self.part_wrong_label_spans:
            result += prefix + tag + str(span) + os.linesep

        tag = f"{ERROR_CATEGORIES[3]}\t"
        for span in self.wrong_label_spans:
            result += prefix + tag + str(span) + os.linesep

        tag = f"{ERROR_CATEGORIES[4]}\t"
        for span in self.failed_spans:
            result += prefix + tag + str(span) + os.linesep

        # result += str(dict(self.node_counter)) + os.linesep

        return result

    def print_most_common(self, n):
        print(f"{ERROR_CATEGORIES[0]}")
        print(Counter(t[1] for t in self.part_mismatched_tag_spans).most_common(n))

        print(f"{ERROR_CATEGORIES[1]}")
        print(Counter(t[1] for t in self.mismatched_tag_spans).most_common(n))

        print(f"{ERROR_CATEGORIES[2]}")
        print(Counter(t[1] for t in self.part_wrong_label_spans).most_common(n))

        print(f"{ERROR_CATEGORIES[3]}")
        print(Counter(t[1] for t in self.wrong_label_spans).most_common(n))

        print(f"{ERROR_CATEGORIES[4]}")
        print(Counter(t[1] for t in self.failed_spans).most_common(n))

    def print_by_tags(self, tags, n):
        print_proposed_alternatives(ERROR_CATEGORIES[0], self.part_mismatched_tag_spans,
                                    self.proposal.proposed_part_mismatched_tag_spans,
                                    tags, n)

        print_proposed_alternatives(ERROR_CATEGORIES[1], self.mismatched_tag_spans,
                                    self.proposal.proposed_mismatched_tag_spans,
                                    tags, n)

        print_proposed_alternatives(ERROR_CATEGORIES[2], self.part_wrong_label_spans,
                                    self.proposal.proposed_part_wrong_label_spans,
                                    tags, n)

        print_proposed_alternatives(ERROR_CATEGORIES[3], self.wrong_label_spans,
                                    self.proposal.proposed_wrong_label_spans,
                                    tags, n)

    def __add__(self, o):
        return FailureAnalyzer(self.mismatched_tag_spans + o.mismatched_tag_spans,
                               self.part_mismatched_tag_spans + o.part_mismatched_tag_spans,
                               self.failed_spans + o.failed_spans,
                               self.wrong_label_spans + o.wrong_label_spans,
                               self.part_wrong_label_spans + o.part_wrong_label_spans,
                               self.proposal + o.proposal,
                               self.node_counter + o.node_counter)


def print_proposed_alternatives(label, error_type, proposed, tags, n):
    c = Counter(t[1] for t in error_type)
    result = []
    for k, v in c.most_common(n):
        for tag in tags:
            if tag in k:
                proposed_str = ', '.join(
                    (f"{k}: {v}" for (k, v) in sorted(proposed[k].items(), key=lambda item: item[1], reverse=True)))
                result.append(f"{k}[{v}] => {proposed_str}")
    if result:
        print(f"{label}:")
        print('\n'.join(result))
        print()


class Proposal(object):

    def __init__(self, proposed_mismatched_tag_spans, proposed_part_mismatched_tag_spans, proposed_wrong_label_spans,
                 proposed_part_wrong_label_spans):
        self.proposed_mismatched_tag_spans = proposed_mismatched_tag_spans
        self.proposed_part_mismatched_tag_spans = proposed_part_mismatched_tag_spans
        self.proposed_wrong_label_spans = proposed_wrong_label_spans
        self.proposed_part_wrong_label_spans = proposed_part_wrong_label_spans

    def __add__(self, o):
        return Proposal(merge_counter_dicts(self.proposed_mismatched_tag_spans, o.proposed_mismatched_tag_spans),
                        merge_counter_dicts(self.proposed_part_mismatched_tag_spans,
                                            o.proposed_part_mismatched_tag_spans),
                        merge_counter_dicts(self.proposed_wrong_label_spans, o.proposed_wrong_label_spans),
                        merge_counter_dicts(self.proposed_part_wrong_label_spans, o.proposed_part_wrong_label_spans))


def merge_counter_dicts(my_dict, other_dict) -> dict:
    result = my_dict.copy()
    for k, v in other_dict.items():
        if k in my_dict:
            result[k].update(v)
        else:
            result[k] = v
    return result


def core_label(s: str) -> str:
    if '-' in s:
        return s.split('-')[0]
    elif '=' in s:
        return s.split('=')[0]
    return s


# def core_label(s: str) -> str:
#     if '=' in s:
#         s = s.split('=')[0]
#     if '-' in s:
#         s = s.split('-')[0]
#     return s


def unmatched_tags(gold_pos, test_pos):
    part_mismatched_tag_spans = []
    mismatched_tag_spans = []
    proposed_part_mismatched_tag_spans = {}
    proposed_mismatched_tag_spans = {}
    for i, (gold, test) in enumerate(zip(gold_pos, test_pos)):
        if gold != test:
            if core_label(gold) == core_label(test):
                part_mismatched_tag_spans.append(((i, i), gold))
                counter = proposed_part_mismatched_tag_spans.setdefault(gold, Counter())
                counter.update({test: 1})
            else:
                mismatched_tag_spans.append(((i, i), gold))
                counter = proposed_mismatched_tag_spans.setdefault(gold, Counter())
                counter.update({test: 1})
    return mismatched_tag_spans, proposed_mismatched_tag_spans, part_mismatched_tag_spans, proposed_part_mismatched_tag_spans


def span_into_map(spans) -> dict:
    result = dict()
    for (start, end, label) in spans:
        span = (start, end)
        if span in result:
            result[span].append(label)
        else:
            result[span] = [label, ]
    return result


def analyze_parses(gold, test):
    gold_span_map = span_into_map(gold.spans())
    test_span_map = span_into_map(test.spans())
    proposed_wrong_label_spans = {}
    proposed_part_wrong_label_spans = {}

    failed_spans = []
    wrong_label_spans = []
    part_wrong_label_spans = []
    for item in gold_span_map.items():
        span, gold_labels = item
        if span not in test_span_map:  # this gold span doesn't exist
            for label in gold_labels:
                failed_spans.append((span, label))
        else:  # span exists, check labels
            test_labels = set(test_span_map[span])
            part_test_labels = set(core_label(x) for x in test_labels)
            for label in gold_labels:
                if label in test_labels:
                    continue  # a perfect match of the span and gold and test labels
                if core_label(label) in part_test_labels:
                    part_wrong_label_spans.append((span, label))
                    proposed_labels = set()
                    for proposed_label in test_labels:
                        if label.startswith(core_label(proposed_label)):
                            proposed_labels.add(proposed_label)
                    proposed_part_wrong_label_spans.setdefault(label, Counter()).update(proposed_labels)
                else:  # span is correct, but all test labels are wrong
                    wrong_label_spans.append((span, label))
                    proposed_wrong_label_spans.setdefault(label, Counter()).update(part_test_labels)
    return failed_spans, wrong_label_spans, proposed_wrong_label_spans, part_wrong_label_spans, proposed_part_wrong_label_spans


def layered_node_into_map(layered_nodes):
    result = {}
    for node, depth in layered_nodes.items():
        result[(node.start, node.end, depth)] = node.label
    return result


def analyze_layered_parses(gold, test):
    gold_span_map = layered_node_into_map(gold.layered_spans())
    test_span_map = layered_node_into_map(test.layered_spans())

    proposed_wrong_label_spans = {}
    proposed_part_wrong_label_spans = {}

    failed_spans = []
    wrong_label_spans = []
    part_wrong_label_spans = []
    for span, label in gold_span_map.items():
        if span not in test_span_map:  # this gold span doesn't exist
            failed_spans.append((span, label))
        else:  # span exists, check labels
            test_label = test_span_map[span]
            if label == test_label:
                continue  # a perfect match of the span and gold and test labels
            if core_label(label) == core_label(test_label):
                part_wrong_label_spans.append((span, label))
                proposed_part_wrong_label_spans.setdefault(label, Counter()).update({test_label: 1})
            else:  # span is correct, but all test labels are wrong
                wrong_label_spans.append((span, label))
                proposed_wrong_label_spans.setdefault(label, Counter()).update({test_label: 1})
    return failed_spans, wrong_label_spans, proposed_wrong_label_spans, part_wrong_label_spans, proposed_part_wrong_label_spans


def analyze(gold_file, eval_file, layered=False):
    num_sentences = 0
    num_error_sentences = 0
    num_skipped_sentences = 0

    total_eval = FailureAnalyzer.init_default()
    total_node_counter = Counter()
    # print(total_eval.header())

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
            print(f"{num_sentences}: Mismatch of number of words in\ngold:{gold}\ntest:{eval}")
            num_error_sentences += 1
            continue

        # # strip TOP_LABEL (VROOT) in both gold and eval treees
        # if gold.label == TOP_LABEL and len(gold.children) == 1:
        #     gold = gold.children[0]
        # if eval.label == TOP_LABEL and len(eval.children) == 1:
        #     eval = eval.children[0]

        eval_set = set(str(t) for t in eval.leaves())
        gold_set = set(str(t) for t in gold.leaves())
        if eval_set != gold_set:
            new_eval_words = eval_set - gold_set
            new_gold_words = gold_set - eval_set
            print(f"{num_sentences}: Words unmatch {new_gold_words} | {new_eval_words}")
            num_skipped_sentences += 1
            continue
        sentence_len = gold.end - gold.start + 1
        node_counter = Counter(nt.label for nt in gold.nonterminals())
        # node_counter = Counter(core_label(nt.label) for nt in gold.nonterminals())
        total_node_counter.update(node_counter)
        mismatched_tag_spans, proposed_mismatched_tag_spans, part_mismatched_tag_spans, proposed_part_mismatched_tag_spans = unmatched_tags(
            gold.pos_tags(),
            eval.pos_tags())

        [failed_spans, wrong_label_spans, proposed_wrong_label_spans, part_wrong_label_spans,
         proposed_part_wrong_label_spans] = analyze_layered_parses(gold, eval) if layered else analyze_parses(gold,
                                                                                                              eval)

        prop = Proposal(proposed_mismatched_tag_spans, proposed_part_mismatched_tag_spans, proposed_wrong_label_spans,
                        proposed_part_wrong_label_spans)
        row = FailureAnalyzer(mismatched_tag_spans, part_mismatched_tag_spans, failed_spans, wrong_label_spans,
                              part_wrong_label_spans, prop, node_counter, num_sentences, 1, sentence_len)

        print(row)
        total_eval += row

    return total_eval


if __name__ == "__main__":
    gold_file, eval_file = open_gold_eval_files()

    eval_result = analyze(
        gold_file,
        eval_file, layered=True)

    eval_result.print_most_common(50)

    # print("Number of analyzed sentences: {}".format(num_sentences))
    # print("Error sentences: {}".format(num_error_sentences))
    # print("Skipped sentences: {}".format(num_skipped_sentences))
    # print(total_eval.bottom_str())

    gold_file.close()
    eval_file.close()
