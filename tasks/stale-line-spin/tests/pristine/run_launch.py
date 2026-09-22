import sys

from sim import clock, load, say


def run(text):
    launch = load.parse(text)
    return say.lines(launch, *clock.run(launch))


def main():
    with open(sys.argv[1]) as f:
        print("\n".join(run(f.read())))


if __name__ == "__main__":
    main()
