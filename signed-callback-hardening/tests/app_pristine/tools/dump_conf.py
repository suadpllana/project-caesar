import json
import sys

sys.path.insert(0, "/app")

from svc.core import cfg


def main():
    print(cfg.active_profile())
    print(json.dumps(cfg.load(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
