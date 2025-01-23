from args import parse_args
from mode1 import mode1
from mode2 import mode2

def main():
    args = parse_args()
    mode = args.mode

    if mode == 1:
        print("Baseline selected")
        mode1()
    elif mode == 2:
        print("Comparison selected")
        mode2()

if __name__ == "__main__":
    main()
