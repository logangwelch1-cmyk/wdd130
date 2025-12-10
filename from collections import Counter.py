from collections import Counter
import sys

def collatz(n, stop_set=None):
    """Run the Collatz sequence starting from n and return the sequence.
    If stop_set is provided, stop the sequence early if a value in stop_set
    is encountered (append that value and return). This allows skipping
    work when we reach a number we've already seen in earlier runs.
    """
    if stop_set is None:
        stop_set = set()

    sequence = [n]
    # if starting number already in stop_set, return immediately
    if n in stop_set:
        return sequence

    while n != 1:
        if n % 2 == 0:   # even
            n //= 2
        else:            # odd
            n = 3 * n + 1

        sequence.append(n)

        # If we hit a previously seen value, stop early
        if n in stop_set:
            break

    return sequence


def main(times=None, start=None):
    # Interactive fallback if args not provided
    if times is None:
        times = int(input("How many times should the Collatz sequence run? "))
    if start is None:
        start = int(input("Enter the starting number: "))

    counts = Counter()
    seen = set()  # numbers seen across all runs

    for i in range(times):
        current_start = start + i   # increment each time (N+1)

        # If starting number already seen, skip to next
        if current_start in seen:
            print(f"Skipping {current_start} (already seen)")
            continue

        seq = collatz(current_start, stop_set=seen)
        counts.update(seq)  # add occurrences from this run
        seen.update(seq)

        print(f"\nRun {i+1}: Starting from {current_start}")
        print(seq)

    # Show numbers that appear in more than 2% of sequences
    print("\n--- Frequently Appearing Numbers (>2% of sequences) ---")
    frequent_numbers = []
    for number, freq in counts.items():
        percentage = (freq / times) * 100
        if percentage > 2:  # Only numbers appearing in more than 2% of sequences
            frequent_numbers.append((number, freq, percentage))
    
    # Sort by frequency (highest to lowest)
    frequent_numbers.sort(key=lambda x: x[1], reverse=True)
    
    for number, freq, percentage in frequent_numbers:
        print(f"Number {number:4d} → Found in {freq:3d} sequences ({percentage:5.1f}%)")


if __name__ == "__main__":
    # Allow non-interactive usage: python script.py <times> <start>
    if len(sys.argv) >= 3:
        try:
            times_arg = int(sys.argv[1])
            start_arg = int(sys.argv[2])
        except ValueError:
            print("Command-line arguments must be integers: <times> <start>")
            sys.exit(1)
        main(times=times_arg, start=start_arg)
    else:
        main()
