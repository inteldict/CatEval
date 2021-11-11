## About The Project
# CatEval

CatEval is a tool for evaluation of constituency parsers.

Cateval identifies
error-prone non-terminals or pre-terminals, respectively, to equip linguists with key
information to identify/revise the most fatal rules in the grammar. 

In our metric we classify all parsing failures in the following mutually exclusive
categories where we distinguish pre-terminal and non-terminal in the usual manner,
i.e., a pre-terminal is a leave in a derivation tree, whereas non-terminals refer to inner
nodes (including the root node).

CatEval distinguish following error categories:
 - TAG_MISMATCH — evaluation of pre-terminals: POS tag mismatch with the one
in the gold standard.
 - PART_TAG_MISMATCH — evaluation of pre-terminals with more fine-grained
features defined in the grammar: if the node has a correct POS tag, but at least one
of other terminal features (e.g., morphological categories) do not match the gold
standard specification.
 - WRONG_SPAN — evaluation of non-terminals: the range of yielded terminals
mismatches the gold standard.
 - WRONG_LABEL_SPAN — evaluation of non-terminals: despite a correct span is
yielded, the category symbol does not match the gold standard.
 - PART_WRONG_LABEL_SPAN — evaluation of non-terminals with more fine-
grained features defined in the grammar: despite a correct span is yielded, addi-
tional features of the category symbol do not match the gold standard specification.

### Built With
matplotlib # pip install matplotlib

squarify  # pip install squarify

<!-- GETTING STARTED -->
## Getting Started

This is an example of how you may run evaluation on the provided example.
```
python3 cateval.py --gold data/sample2.gld --eval data/sample2.eval --tags=SX,VAFIN,NX
```
