1#!/usr/bin/env python3
"""Collatz sequence calculator with persistent seen-number cache.

Behavior:
- Applies Collatz rules until 1.
- Saves every number encountered into a persistent JSON file (default: .collatz_seen.json in the script directory).
- Skips any starting value that's already in the seen cache (so you don't recompute sequences you've already covered).

Usage examples:
  python collatz.py 27            # runs 27 and 28 by default (if repeats omitted)
  python collatz.py 27 -r 3       # runs 27,28,29
  python collatz.py 27 --after 2  # runs 27,28,29 (after = additional starts)
  python collatz.py 27 -a         # repeats indefinitely starting at 27
  python collatz.py 27 --no-skip  # do not skip starts even if seen before
  python collatz.py 27 --persist-file seen.json  # use custom cache file
"""
import argparse
import json
import os
import sys
from typing import Set, List


def collatz_sequence(n: int) -> List[int]:
    seq = [n]
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = n * 3 + 1
        seq.append(n)
    return seq


def load_seen(path: str) -> Set[int]:
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return set(int(x) for x in data)
    except Exception as e:
        print(f"Warning: couldn't read seen file {path}: {e}")
    return set()


def save_seen(path: str, seen: Set[int]) -> None:
    # write atomically
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            # store as sorted list for readability
            json.dump(sorted(list(seen)), f)
        os.replace(tmp, path)
    except Exception as e:
        print(f"Warning: couldn't save seen file {path}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Collatz calculator with persistent seen-number cache')
    parser.add_argument('start', nargs='?', type=int, help='starting positive integer')
    parser.add_argument('-r', '--repeats', type=int, default=None, help='number of consecutive starts to run (N..N+repeats-1). If omitted, defaults to 2 when start is provided (runs N and N+1).')
    parser.add_argument('-x', '--after', type=int, default=None, help='number of additional starts to run after the initial start (so --after 2 runs N, N+1, N+2)')
    parser.add_argument('-t', '--to', type=int, default=None, help='run for all starting values from N to TO (inclusive). Accepts TO < N to run downward.')
    parser.add_argument('--down', action='store_true', help='run for start and all numbers less than it down to 1 (inclusive)')
    parser.add_argument('-a', '--auto', action='store_true', help='repeat indefinitely starting at N (Ctrl-C to stop)')
    parser.add_argument('--persist-file', type=str, default=None, help='path to JSON file to store seen numbers (default: .collatz_seen.json next to script)')
    parser.add_argument('--no-skip', action='store_true', help='do not skip starts that are already in the seen cache')
    args = parser.parse_args()

    # determine script directory and default persist path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_seen = os.path.join(script_dir, '.collatz_seen.json')
    seen_path = args.persist_file if args.persist_file else default_seen

    if args.start is None:
        try:
            n = int(input('Enter a positive integer: ').strip())
        except Exception:
            print('Invalid input')
            return 1
    else:
        n = args.start

    if n <= 0:
        print('Please enter a positive integer greater than 0')
        return 1

    # load seen cache
    seen = load_seen(seen_path)

    if args.auto:
        try:
            current = n
            while True:
                if (not args.no_skip) and (current in seen):
                    print(f"Skipping Start={current}: already in seen cache")
                else:
                    seq = collatz_sequence(current)
                    print(f"Start={current}: " + ' -> '.join(str(x) for x in seq))
                    # add all encountered numbers
                    seen.update(seq)
                    save_seen(seen_path, seen)
                current += 1
        except KeyboardInterrupt:
            print('\nInterrupted by user. Exiting.')
            return 0

    # If --down is provided, iterate from n down to 1 (inclusive)
    if args.down:
        if n < 1:
            print('Invalid start value; must be >= 1')
            return 1
        current = n
        while current >= 1:
            if (not args.no_skip) and (current in seen):
                print(f"Skipping Start={current}: already in seen cache")
            else:
                seq = collatz_sequence(current)
                print(f"Start={current}: " + ' -> '.join(str(x) for x in seq))
                seen.update(seq)
                save_seen(seen_path, seen)
            current -= 1
        print('Done.')
        return 0

    # If --to is provided, run for the inclusive range from n to to_value and exit
    if args.to is not None:
        to_value = args.to
        if to_value <= 0:
            print('Invalid --to value; must be >= 1')
            return 1
        # determine step for range (allow descending)
        step = 1 if to_value >= n else -1
        # iterate inclusive of to_value
        current = n
        while True:
            if (not args.no_skip) and (current in seen):
                print(f"Skipping Start={current}: already in seen cache")
            else:
                seq = collatz_sequence(current)
                print(f"Start={current}: " + ' -> '.join(str(x) for x in seq))
                seen.update(seq)
                save_seen(seen_path, seen)
            if current == to_value:
                break
            current += step
        print('Done.')
        return 0

    # compute repeats
    if args.after is not None:
        if args.after < 0:
            print('Invalid --after value; must be >= 0')
            return 1
        repeats = args.after + 1
    else:
        repeats = args.repeats
        if repeats is None and args.start is not None:
            repeats = 2
        if repeats is None:
            repeats = 1

    try:
        repeats = int(repeats)
    except Exception:
        print('Invalid repeats argument; must be an integer')
        return 1
    if repeats <= 0:
        print('Repeats must be >= 1 (use --auto to repeat indefinitely)')
        return 1

    # run for the requested starts
    for i in range(repeats):
        start = n + i
        if (not args.no_skip) and (start in seen):
            print(f"Skipping Start={start}: already in seen cache")
            continue
        seq = collatz_sequence(start)
        print(f"Start={start}: " + ' -> '.join(str(x) for x in seq))
        seen.update(seq)
        save_seen(seen_path, seen)

    print('Done.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
