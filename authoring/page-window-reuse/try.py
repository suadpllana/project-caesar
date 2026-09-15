"""Does this program separate the reference from a named wrong reading?

    python try.py <reading-name> <<'EOF'
    ...program...
    EOF
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import readings  # noqa: E402


def main():
    name = sys.argv[1]
    text = sys.stdin.read().strip()
    alt = pathlib.Path("/tmp/pwr-try-%s" % name)
    alt.mkdir(exist_ok=True)
    for part, src in readings.READINGS[name].items():
        (alt / part).write_text(src, encoding="utf-8")
    ref = readings.run(readings.REFERENCE, text)
    bad = readings.run(str(alt), text)
    print("reference".ljust(34), "|", name)
    for i in range(max(len(ref), len(bad))):
        a = ref[i] if i < len(ref) else "-"
        b = bad[i] if i < len(bad) else "-"
        print("%-34s | %-34s %s" % (a, b, "" if a == b else "<<<"))
    print("SEPARATED" if ref != bad else "SAME")


if __name__ == "__main__":
    main()
