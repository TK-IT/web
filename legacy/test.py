import time
import argparse
from legacy.export import read_regnskab_revisions_gitpython
from legacy.export import read_regnskab_revisions


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('gitdir')
    args = parser.parse_args()

    t1 = time.time()
    r2 = list(read_regnskab_revisions(args.gitdir))
    t2 = time.time()
    r1 = list(read_regnskab_revisions_gitpython(args.gitdir))
    t3 = time.time()
    print(r1 == r2, t2 - t1, t3 - t2)
    assert r1 == r2


if __name__ == "__main__":
    main()
