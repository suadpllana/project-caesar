import sys, pathlib
R = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R/"tasks/aside-fit-sweep/tests")); sys.path.insert(0, str(R/"tasks/aside-fit-sweep/tests/seal"))
sys.path.insert(0, str(R/"tasks/aside-fit-sweep/solution")); 
import cases, model
only = sys.argv[1:] or cases.ORDER
for name in only:
    print("==", name)
    for line in model.expect(cases.ops(name)):
        print("   ", line)
