#!/usr/bin/env python3
"""Conjecture.py

Combines a Collatz sequence runner with:
- persistent "seen" cache to skip already-computed starts
- flexible CLI: start, repeats, after, to, down, auto
- optional frequency counting across runs (prints numbers seen often)

Usage examples:
  python Conjecture.py 27                # runs 27 and 28 by default (if repeats omitted)
  python Conjecture.py 27 -r 3           # runs 27,28,29
  python Conjecture.py 27 --after 2      # runs 27,28,29
  python Conjecture.py 27 --to 1         # runs 27 down to 1
  python Conjecture.py 27 --down         # runs 27 down to 1 (same as --to 1)
  python Conjecture.py 27 --no-skip      # don't skip starts even if seen before
  python Conjecture.py 27 --counts       # collect and print frequency counts across runs
  python Conjecture.py 27 --persist-file seen.json  # use custom cache file
"""

import argparse
import json
import os
import sys
from collections import Counter
from typing import List, Set


def collatz_sequence(n: int) -> List[int]:
    seq = [n]
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = n * 3 + 1
        seq.append(n)
    return seq


def run_collatz_with_seen_check(start: int, seen: Set[int]):
    """Run Collatz starting at `start` and stop early if a number is found in `seen`.
    Returns (seq, stopped_at) where stopped_at is the seen value encountered or None.
    """
    seq = [start]
    n = start
    if n in seen:
        return ([], n)
    while n != 1:
        if n % 2 == 0:
            n = n // 2
        else:
            n = n * 3 + 1
        if n in seen:
            # stop before adding the seen value into the sequence
            return (seq, n)
        seq.append(n)
    return (seq, None)


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
    tmp = path + '.tmp'
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            json.dump(sorted(list(seen)), f)
        os.replace(tmp, path)
    except Exception as e:
        print(f"Warning: couldn't save seen file {path}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Conjecture: Collatz runner with cache and counting')
    parser.add_argument('start', nargs='?', type=int, help='starting positive integer')
    parser.add_argument('-r', '--repeats', type=int, default=None, help='number of consecutive starts to run (N..N+repeats-1). If omitted, defaults to 2 when start is provided (runs N and N+1).')
    parser.add_argument('-x', '--after', type=int, default=None, help='number of additional starts to run after the initial start (so --after 2 runs N, N+1, N+2)')
    parser.add_argument('-t', '--to', type=int, default=None, help='run for all starting values from N to TO (inclusive). Accepts TO < N to run downward.')
    parser.add_argument('--down', action='store_true', help='run for start and all numbers less than it down to 1 (inclusive)')
    parser.add_argument('-a', '--auto', action='store_true', help='repeat indefinitely starting at N (Ctrl-C to stop)')
    parser.add_argument('--persist-file', type=str, default=None, help='path to JSON file to store seen numbers (default: .collatz_seen.json next to script)')
    parser.add_argument('--no-skip', action='store_true', help='do not skip starts that are already in the seen cache')
    parser.add_argument('--counts', action='store_true', help='collect frequency counts across runs and print them at the end')
    parser.add_argument('--min-count', type=int, default=None, help='minimum occurrence to show in frequency output (default: repeats//4 or 2)')
    args = parser.parse_args()

    # determine script directory and default persist path
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_seen = os.path.join(script_dir, '.collatz_seen.json')
    seen_path = args.persist_file if args.persist_file else default_seen

    if args.start is None:
        try:
            n = int(input('Enter the starting number: ').strip())
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

    # special: --down behaves like --to 1
    if args.down:
        args.to = 1

    # if auto, do continuous run (counts disabled)
    if args.auto:
        try:
            current = n
            while True:
                if (not args.no_skip) and (current in seen):
                    print(f"Skipping Start={current}: already in seen cache")
                else:
                    seq = collatz_sequence(current)
                    print(f"Start={current}: " + ' -> '.join(str(x) for x in seq))
                    seen.update(seq)
                    save_seen(seen_path, seen)
                current += 1
        except KeyboardInterrupt:
            print('\nInterrupted by user. Exiting.')
            return 0

    # If --to provided, build inclusive range from n to to
    starts = []
    if args.to is not None:
        to_value = args.to
        step = 1 if to_value >= n else -1
        current = n
        while True:
            starts.append(current)
            if current == to_value:
                break
            current += step
    else:
        # compute repeats: after takes precedence
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
            print('Repeats must be >= 1')
            return 1
        starts = [n + i for i in range(repeats)]

    # prepare counter if requested
    counts = Counter()

    # run for each start
    for start in starts:
        if (not args.no_skip) and (start in seen):
            print(f"Skipping Start={start}: already in seen cache")
            continue

        # Use the seen-aware runner that stops if a number is already seen
        seq, stopped_at = run_collatz_with_seen_check(start, seen)

        if seq:
            print(f"Start={start}: " + ' -> '.join(str(x) for x in seq))
            seen.update(seq)
            save_seen(seen_path, seen)
            if args.counts:
                counts.update(seq)
        else:
            # seq empty means start itself was in seen
            print(f"Skipping Start={start}: already in seen cache")

        # If we stopped early because we hit a seen number, report it
        if stopped_at is not None:
            print(f"Stopped early for Start={start} because {stopped_at} was already in the seen cache")
            # If running downward, continue with start-1 (behavior requested)
            if args.down:
                # find next start (start-1) and continue in that direction
                next_start = start - 1
                while next_start >= 1:
                    if (not args.no_skip) and (next_start in seen):
                        print(f"Skipping Start={next_start}: already in seen cache")
                        next_start -= 1
                        continue
                    seq2, stopped2 = run_collatz_with_seen_check(next_start, seen)
                    if seq2:
                        print(f"Start={next_start}: " + ' -> '.join(str(x) for x in seq2))
                        seen.update(seq2)
                        save_seen(seen_path, seen)
                        if args.counts:
                            counts.update(seq2)
                    else:
                        print(f"Skipping Start={next_start}: already in seen cache")
                    if stopped2 is not None:
                        print(f"Stopped early for Start={next_start} because {stopped2} was already in the seen cache")
                    next_start -= 1

    if args.counts:
        # default min_count
        if args.min_count is None:
            try:
                min_count = max(2, len(starts) // 4)
            except Exception:
                min_count = 2
        else:
            min_count = args.min_count
        print('\n--- Number Frequencies (>= {} occurrences) ---'.format(min_count))
        for number, freq in counts.most_common():
            if freq >= min_count:
                print(f"{number}: {freq}")

    print('Done.')
    return 0


if __name__ == '__main__':
    sys.exit(main())
