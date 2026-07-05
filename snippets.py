"""
snippets.py — problem bank for the adaptive code-builder game.

Each problem provides:
  target        — the correct lines, in order
  distractors   — wrong lines that LOOK plausible (strong distractors:
                   off-by-one, inverted conditions, swapped operators,
                   infinite-recursion traps, etc.) so picking correctly
                   actually requires understanding, not pattern-matching
  explanations  — why each distractor is wrong (shown as feedback)
  correct_notes — why each correct line belongs where it does (shown on
                   hints / after a correct pick)

Having several problems (not just one) lets the adaptive hint system
generalise across different learners and different code, rather than
overfitting its hint policy to a single exercise.
"""

PROBLEMS = [
    {
        "name": "Factorial (Recursive)",
        "description": "Build a recursive factorial function",
        "target": [
            "def factorial(n):",
            "  if n == 0:",
            "    return 1",
            "  return n * factorial(n-1)",
        ],
        "distractors": [
            "  return n + 1",
            "  return factorial(n-1)",
            "  if n == 1:",
            "  return n * factorial(n)",
            "  if n < 0:",
            "  return n * factorial(n-1) + 1",
            "    return 0",
        ],
        "explanations": {
            "  return n + 1":              "Adds 1 instead of multiplying. Doesn't compute factorial.",
            "  return factorial(n-1)":     "Missing 'n *'. Loses the multiplication — always returns 1.",
            "  if n == 1:":                "Wrong base case. factorial(0) must be 1, not factorial(1).",
            "  return n * factorial(n)":   "Calls factorial(n) not factorial(n-1) — infinite recursion!",
            "  if n < 0:":                 "Wrong condition. Base case should check n == 0, not negatives.",
            "  return n * factorial(n-1) + 1": "So close! The stray '+ 1' throws off every result above n=0.",
            "    return 0":                "Wrong base value. factorial(0) is 1, not 0 — this breaks every product.",
        },
        "correct_notes": {
            0: "Function signature — names the function and its parameter.",
            1: "Base case — when n is 0, stop recursing.",
            2: "Base return — factorial(0) = 1 by definition.",
            3: "Recursive case — n * factorial(n-1) builds the product.",
        },
    },
    {
        "name": "Fibonacci (Recursive)",
        "description": "Build a recursive Fibonacci function",
        "target": [
            "def fib(n):",
            "  if n <= 1:",
            "    return n",
            "  return fib(n-1) + fib(n-2)",
        ],
        "distractors": [
            "  if n == 0:",
            "  return fib(n-1) * fib(n-2)",
            "  return fib(n) + fib(n-1)",
            "  return n - 1",
            "  if n < 0:",
            "  return fib(n-1) + fib(n-1)",
            "    return 1",
        ],
        "explanations": {
            "  if n == 0:":               "Incomplete — misses the n==1 base case. fib(1) must return 1.",
            "  return fib(n-1) * fib(n-2)":"Multiplies instead of adds. Fibonacci adds the two previous terms.",
            "  return fib(n) + fib(n-1)": "fib(n) calls itself with the same n — infinite recursion!",
            "  return n - 1":             "Wrong return. Base case should return n itself (0 or 1).",
            "  if n < 0:":                "Wrong guard. Base cases are n==0 and n==1, not negatives.",
            "  return fib(n-1) + fib(n-1)":"Both calls use n-1 — should be n-1 AND n-2, the two preceding terms.",
            "    return 1":              "Wrong for n==0. The combined base case must return n itself, not always 1.",
        },
        "correct_notes": {
            0: "Function signature — defines fib taking one argument n.",
            1: "Combined base case — handles both fib(0)=0 and fib(1)=1.",
            2: "Returns n directly for the base cases (0 or 1).",
            3: "Recursive case — sum of the two preceding Fibonacci numbers.",
        },
    },
    {
        "name": "Palindrome Check",
        "description": "Check if a string reads the same forwards and backwards",
        "target": [
            "def is_palindrome(s):",
            "  s = s.lower()",
            "  return s == s[::-1]",
        ],
        "distractors": [
            "  return s == s[::1]",
            "  s = s.upper()",
            "  return s != s[::-1]",
            "  return s[0] == s[-1]",
            "  s = s.strip()",
            "  return s == s.reverse()",
            "  return sorted(s) == s",
        ],
        "explanations": {
            "  return s == s[::1]":   "s[::1] is just s itself — always True. Need s[::-1] to reverse.",
            "  s = s.upper()":        "upper() works but is redundant — lower() is the conventional choice.",
            "  return s != s[::-1]":  "Inverted logic — != means it returns True for non-palindromes.",
            "  return s[0] == s[-1]": "Only checks first and last characters. 'abba' passes but 'abca' would too.",
            "  s = s.strip()":        "Strips whitespace only — doesn't normalise case, so 'Aba' != 'aba'.",
            "  return s == s.reverse()": "Strings have no .reverse() method — this raises an AttributeError.",
            "  return sorted(s) == s": "Checks if letters are alphabetically sorted, not whether s reads the same backwards.",
        },
        "correct_notes": {
            0: "Function signature — takes the string s to check.",
            1: "Normalise to lowercase so 'Racecar' == 'racecar'.",
            2: "Compare s with its reverse ([::-1]). Equal means palindrome.",
        },
    },
    {
        "name": "Bubble Sort",
        "description": "Sort a list in-place using bubble sort",
        "target": [
            "def bubble_sort(arr):",
            "  n = len(arr)",
            "  for i in range(n):",
            "    for j in range(n-i-1):",
            "      if arr[j] > arr[j+1]:",
            "        arr[j], arr[j+1] = arr[j+1], arr[j]",
        ],
        "distractors": [
            "  for i in range(n-1):",
            "    if arr[j] < arr[j+1]:",
            "    for j in range(n-i):",
            "        arr[j] = arr[j+1]",
            "  n = len(arr) - 1",
            "    for j in range(n-i+1):",
            "      if arr[j] >= arr[j+1]:",
        ],
        "explanations": {
            "  for i in range(n-1):":     "Off-by-one in outer loop — misses the final pass needed.",
            "    if arr[j] < arr[j+1]:":  "Inverted comparison — sorts descending, not ascending.",
            "    for j in range(n-i):":   "Missing -1: j+1 would go out of bounds on the last element.",
            "        arr[j] = arr[j+1]":  "Only copies, doesn't swap. Original value at j is lost.",
            "  n = len(arr) - 1":         "Under-counts length — the last element is never compared.",
            "    for j in range(n-i+1):": "Goes one too far — j+1 can index past the end of the array.",
            "      if arr[j] >= arr[j+1]:":"Swaps even when equal — harmless but wasteful, and changes stability of the sort.",
        },
        "correct_notes": {
            0: "Function signature — arr is modified in-place.",
            1: "Get the array length once for use in loop bounds.",
            2: "Outer loop — each pass bubbles the next largest to its place.",
            3: "Inner loop — shrinks by i because last i elements are already sorted.",
            4: "Comparison — if left > right, a swap is needed.",
            5: "Swap — Python tuple unpacking swaps both values atomically.",
        },
    },
    {
        "name": "Binary Search",
        "description": "Find a target value in a sorted list",
        "target": [
            "def binary_search(arr, target):",
            "  lo, hi = 0, len(arr) - 1",
            "  while lo <= hi:",
            "    mid = (lo + hi) // 2",
            "    if arr[mid] == target:",
            "      return mid",
            "    elif arr[mid] < target:",
            "      lo = mid + 1",
            "    else:",
            "      hi = mid - 1",
            "  return -1",
        ],
        "distractors": [
            "  lo, hi = 0, len(arr)",
            "  while lo < hi:",
            "    mid = (lo + hi) / 2",
            "    elif arr[mid] > target:",
            "      lo = mid",
            "      hi = mid",
            "  return 0",
            "    mid = (lo - hi) // 2",
            "      lo = mid - 1",
        ],
        "explanations": {
            "  lo, hi = 0, len(arr)":     "hi should be len(arr)-1 (last index). len(arr) is out of bounds.",
            "  while lo < hi:":           "Misses the case lo==hi — that single element is never checked.",
            "    mid = (lo + hi) / 2":    "/ gives float; // is needed for an integer index.",
            "    elif arr[mid] > target:":"Inverted condition — searches the wrong half every time.",
            "      lo = mid":             "Doesn't advance past mid — loop can hang forever.",
            "      hi = mid":             "Doesn't shrink below mid — loop can hang forever.",
            "  return 0":                 "Should return -1 (not found). 0 is a valid index and causes false positives.",
            "    mid = (lo - hi) // 2":   "Subtracts instead of adds — produces a negative or wrong midpoint.",
            "      lo = mid - 1":         "Moves the wrong direction — should move past mid (mid+1), not below it.",
        },
        "correct_notes": {
            0:  "Signature — takes sorted array and the value to find.",
            1:  "Initialise pointers to array bounds (hi is last valid index).",
            2:  "Loop while search space is non-empty.",
            3:  "Find midpoint with integer division.",
            4:  "Exact match — found the target.",
            5:  "Return the index where the target lives.",
            6:  "Target is larger — discard left half.",
            7:  "Move lo past mid to search right half.",
            8:  "Target is smaller — discard right half.",
            9:  "Move hi below mid to search left half.",
            10: "Target not in array.",
        },
    },
]

# ── Active problem (default: first) — changed by the game ────────────────────
_active_idx = 0

def get_problem(idx=None):
    global _active_idx
    if idx is not None:
        _active_idx = idx % len(PROBLEMS)
    return PROBLEMS[_active_idx]

def problem_count():
    return len(PROBLEMS)

# ── Flat exports for any module that wants the *current* problem directly ────
def _rebuild_flat(p):
    global TARGET_CODE, ALL_SNIPPETS, DISTRACTOR_EXPLANATIONS
    TARGET_CODE             = p["target"]
    ALL_SNIPPETS            = p["target"] + p["distractors"]
    DISTRACTOR_EXPLANATIONS = p["explanations"]

_rebuild_flat(PROBLEMS[0])