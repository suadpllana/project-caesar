import pathlib
import shutil

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / HERE.name
SRC = TASK / "environment" / "app_src"
DST = TASK / "tests" / "pristine"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = len(list(DST.rglob("*.py")))
    print("pristine refreshed:", n, "python files")


if __name__ == "__main__":
    main()
