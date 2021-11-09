import argparse
import gzip


def ropen_file(path):
    if path.endswith('.gz'):
        return gzip.open(path, 'rt')
    else:
        return open(path, 'rt')


def open_gold_eval_files():
    parser = argparse.ArgumentParser(description='Take node ids from file and replace')
    parser.add_argument("gold", help="gold brackets file")
    parser.add_argument("proposed", help="generated brackets file")
    args = parser.parse_args()

    return ropen_file(args.gold), ropen_file(args.proposed)

def dumper(obj):
    try:
        return obj.toJSON()
    except:
        return obj.__dict__