import argparse

def parse_args():
    parser = argparse.ArgumentParser(description="Idk just use it")
    parser.add_argument(
        "mode",
        type=int,
        choices=[1, 2],
        help="Select mode 1 (generate baseline) or mode 2 (compare against baseline)"
    )
    return parser.parse_args()
