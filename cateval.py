import argparse
import pickle
import sys
from collections import Counter
from operator import itemgetter

import matplotlib
import matplotlib.pyplot as plt
import squarify  # pip install squarify (algorithm for treemap)

# Create a dataset:
from parse_analyzer import analyze
from utils import ropen_file

plt.rcParams.update({'font.size': 9})  # change font size


def plot_heatmap(labels, values):
    mini = min(values)
    maxi = max(values)
    norm = matplotlib.colors.Normalize(vmin=mini, vmax=maxi)
    color_map = matplotlib.cm.Reds
    colors = [color_map(norm(value)) for value in values]

    # Change color
    squarify.plot(sizes=values, label=labels, alpha=.8, color=colors)
    plt.axis('off')

    fig = plt.gcf()
    # fig.set_size_inches(18.5, 10.5)
    # plt.title("Mismatched brackets")
    fig.savefig("out/error_labels.pdf", transparent=True)
    plt.show()


def evaluate():
    parser = argparse.ArgumentParser()
    group = parser.add_argument_group()
    group.add_argument('--gold', '-g', help="File with parses in bracketed format as gold standard")
    group.add_argument('--eval', '-e', help="File with parses in bracketed format to evaluate")
    group.add_argument('--save', '-s', help="Save precomputed parse analysis to a file")
    group.add_argument('--load', '-l', help="Load precomputed parse analysis from a file")
    args, unknown_args = parser.parse_known_args()

    if args.load:
        with open(args.load, 'rb') as f:
            total_eval = pickle.load(f)
    elif args.gold and args.eval:
        gold_file, eval_file = ropen_file(args.gold), ropen_file(args.eval)
        total_eval = analyze(
            gold_file,
            eval_file, layered=False)
        gold_file.close()
        eval_file.close()
        if args.save:
            with open(args.save, 'wb') as f:
                pickle.dump(total_eval, f, pickle.HIGHEST_PROTOCOL)
    else:
        sys.exit('Please specify gold file (--gold) and eval file (--eval)')
    return total_eval


def analyze_errors(total_eval):
    total_eval.print_most_common(100)
    # tags_to_analyse = ('SIMPX', 'FKOORD', 'KONJ')
    tags_to_analyse = ('PP',)
    print()
    print(f"Analysis: {tags_to_analyse}")

    total_eval.print_by_tags(tags_to_analyse, 50)
    total_error_labels = Counter(t[1] for t in total_eval.all_errors())
    # wrong_spans = total_eval.wrong_label_spans + total_eval.failed_spans
    # total_error_labels = Counter(l for (_, _, l) in wrong_spans)

    total_labels = total_eval.node_counter

    filtered_total_error_labels = dict((k, v) for k, v in total_error_labels.items() if v > 5)
    print("Total errors:")
    print(sorted(filtered_total_error_labels.items(), key=lambda item: item[1], reverse=True))
    most_common_error_labels = total_error_labels.most_common(30)
    labels_values = []

    relative_frequencies = []
    for label, freq in total_error_labels.items():
        rel_freq = freq / total_labels[label]
        relative_frequencies.append((label, freq, rel_freq))

    relative_frequencies.sort(key=itemgetter(2, 1), reverse=True)
    rel_freq_str = []
    for label, freq, rel_freq in relative_frequencies:
        rel_freq_str.append('{}:{:.2f}%({})'.format(label, rel_freq * 100, freq))
    print("Total error frequencies: ")
    print(', '.join(rel_freq_str))

    for label, freq in most_common_error_labels:
        total_freq = total_labels[label]
        rel_freq = freq / total_freq
        labels_values.append(('{}\n{:.2f}%'.format(label, rel_freq * 100), rel_freq))

    labels_values.sort(key=lambda x: x[1], reverse=True)
    return zip(*labels_values)


if __name__ == "__main__":
    total_eval = evaluate()
    labels, values = analyze_errors(total_eval)
    plot_heatmap(labels, values)
