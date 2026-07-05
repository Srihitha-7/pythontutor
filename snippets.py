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
        "name": "Even or Odd",
        "description": "Check whether a number is even or odd",
        "target": [
            "n = 12",
            "if n % 2 == 0:",
            "  print(\"Even\")",
            "else:",
            "  print(\"Odd\")",
        ],
        "distractors": [
            "if n % 2 = 0:",
            "if n / 2 == 0:",
            "if n % 2 == 1:",
            "print(Even)",
            "elif n % 2 != 0:",
            "if n == 2:",
        ],
        "explanations": {
            "if n % 2 = 0:":     "Uses '=' (assignment) instead of '==' (comparison) — this is a syntax error.",
            "if n / 2 == 0:":    "Divides instead of checking the remainder — only true when n is 0, not for every even number.",
            "if n % 2 == 1:":    "Checks for a remainder of 1, which tests for odd — the wrong condition for this branch.",
            "print(Even)":       "Missing the quotation marks — Even would be read as an undefined variable name, causing a NameError.",
            "elif n % 2 != 0:":  "Using elif here is unnecessary — anything that fails 'remainder is 0' is already covered by else.",
            "if n == 2:":        "Only checks if n is exactly 2, not whether n is even in general.",
        },
        "correct_notes": {
            0: "Store the number to check in a variable.",
            1: "Use % to test whether dividing by 2 leaves no remainder.",
            2: "If the remainder is 0, the number is even.",
            3: "else covers every other case.",
            4: "Any number that isn't even must be odd.",
        },
    },
    {
        "name": "Positive, Negative, or Zero",
        "description": "Classify a number as positive, negative, or zero",
        "target": [
            "n = -5",
            "if n > 0:",
            "  print(\"Positive\")",
            "elif n < 0:",
            "  print(\"Negative\")",
            "else:",
            "  print(\"Zero\")",
        ],
        "distractors": [
            "if n => 0:",
            "if n =< 0:",
            "elif n > 0:",
            "else if n < 0:",
            "  print(\"negative\")",
            "if n != 0:",
        ],
        "explanations": {
            "if n => 0:":        "'=>' isn't valid Python — the operator for greater-than-or-equal is '>='.",
            "if n =< 0:":        "'=<' isn't valid Python — the operator for less-than-or-equal is '<='.",
            "elif n > 0:":       "This repeats the first branch's condition — it can never be reached since positive numbers are already handled above.",
            "else if n < 0:":    "Python doesn't use 'else if' — the correct keyword is 'elif'.",
            "  print(\"negative\")": "Wrong capitalization — inconsistent with the 'Positive' and 'Zero' outputs.",
            "if n != 0:":        "Only checks that n isn't zero — it doesn't separate positive numbers from negative ones.",
        },
        "correct_notes": {
            0: "Store the number to classify.",
            1: "First check if it's greater than 0.",
            2: "If true, it's positive.",
            3: "Otherwise, check if it's less than 0.",
            4: "If true, it's negative.",
            5: "else catches whatever's left over...",
            6: "...meaning n must be exactly 0.",
        },
    },
    {
        "name": "Print 1 to 10",
        "description": "Print the numbers from 1 to 10 using a loop",
        "target": [
            "for i in range(1, 11):",
            "  print(i)",
        ],
        "distractors": [
            "for i in range(1, 10):",
            "for i in range(0, 11):",
            "for i in range(10):",
            "  print(i + 1)",
            "for i in range(11, 1):",
            "print(I)",
        ],
        "explanations": {
            "for i in range(1, 10):": "range(1, 10) stops before 10, so it only prints 1 through 9.",
            "for i in range(0, 11):": "Starts at 0, so it prints an extra 0 before reaching 1.",
            "for i in range(10):":    "Starts at 0 and stops before 10, printing 0-9 instead of 1-10.",
            "  print(i + 1)":         "Adds 1 to i, shifting every printed number one higher than intended.",
            "for i in range(11, 1):": "The start is bigger than the stop with no negative step, so this loop never runs.",
            "print(I)":               "Variable names are case-sensitive — I is not the same as i, so this raises a NameError.",
        },
        "correct_notes": {
            0: "range(1, 11) produces 1 through 10 (the stop value is exclusive).",
            1: "Print each value of i as the loop runs.",
        },
    },
    {
        "name": "Sum 1 to 10",
        "description": "Add up the numbers from 1 to 10 using a loop",
        "target": [
            "total = 0",
            "for i in range(1, 11):",
            "  total = total + i",
            "print(total)",
        ],
        "distractors": [
            "total = 1",
            "for i in range(1, 10):",
            "  total = i",
            "  total = total + 1",
            "print(i)",
            "total = 0 + i",
        ],
        "explanations": {
            "total = 1":              "Starting the running total at 1 instead of 0 throws off the final sum.",
            "for i in range(1, 10):": "Stops before 10, so the number 10 is never added to the total.",
            "  total = i":            "Overwrites total with i each time instead of adding to it — only the last value survives.",
            "  total = total + 1":    "Adds a constant 1 each loop instead of adding the current number i.",
            "print(i)":               "Prints the last loop variable, not the accumulated sum.",
            "total = 0 + i":          "This uses i before the loop has even started — i isn't defined yet here.",
        },
        "correct_notes": {
            0: "Start with a running total of 0.",
            1: "Loop through every number from 1 to 10.",
            2: "Add the current number to the running total each time.",
            3: "Print the final total after the loop finishes.",
        },
    },
    {
        "name": "Largest of Two",
        "description": "Find the larger of two numbers",
        "target": [
            "a = 8",
            "b = 15",
            "if a > b:",
            "  print(a)",
            "else:",
            "  print(b)",
        ],
        "distractors": [
            "if a > b",
            "a > b:",
            "  print(\"a\")",
            "print(A)",
            "b = a",
            "if a < b:",
        ],
        "explanations": {
            "if a > b":       "Missing the colon ':' at the end — every if statement needs one.",
            "a > b:":         "Missing the 'if' keyword — this line alone isn't a valid statement.",
            "  print(\"a\")": "Prints the literal text 'a' instead of the value stored in the variable a.",
            "print(A)":       "Variable names are case-sensitive — A is not the same as a, so this raises a NameError.",
            "b = a":          "Overwrites b with a's value instead of comparing the two numbers.",
            "if a < b:":      "This is the opposite comparison — it would treat the smaller number as the one to print.",
        },
        "correct_notes": {
            0: "Store the first number.",
            1: "Store the second number.",
            2: "Compare the two numbers.",
            3: "If a is bigger, print a.",
            4: "Otherwise (a is not bigger than b)...",
            5: "...print b, since it must be the larger one.",
        },
    },
    {
        "name": "Multiplication Table",
        "description": "Print the multiplication table of a number",
        "target": [
            "n = 5",
            "for i in range(1, 11):",
            "  print(n * i)",
        ],
        "distractors": [
            "for i in range(1, 10):",
            "  print(n + i)",
            "  print(i * i)",
            "for i in range(0, 11):",
            "print(n, i)",
            "for i in range(10):",
        ],
        "explanations": {
            "for i in range(1, 10):": "Stops before 10, so the table only goes up to n*9 instead of n*10.",
            "  print(n + i)":         "Adds instead of multiplying — this isn't a multiplication table.",
            "  print(i * i)":        "Multiplies i by itself instead of by n — ignores the chosen number.",
            "for i in range(0, 11):": "Starts at 0, so the first line printed would be n*0 = 0.",
            "print(n, i)":           "Prints n and i as two separate values instead of their product.",
            "for i in range(10):":   "Starts at 0 and stops before 10, producing n*0 through n*9 instead.",
        },
        "correct_notes": {
            0: "Pick the number to build a table for.",
            1: "Loop i from 1 to 10 (inclusive).",
            2: "Print n multiplied by the current i.",
        },
    },
    {
        "name": "Countdown 10 to 1",
        "description": "Count down from 10 to 1 using a while loop",
        "target": [
            "n = 10",
            "while n >= 1:",
            "  print(n)",
            "  n = n - 1",
        ],
        "distractors": [
            "while n > 1:",
            "while n >= 0:",
            "  n = n + 1",
            "  print(n - 1)",
            "n -= 2",
            "while n <= 1:",
        ],
        "explanations": {
            "while n > 1:":       "Stops as soon as n reaches 1, so 1 itself never gets printed.",
            "while n >= 0:":      "Keeps going one extra time to print 0, which isn't part of the countdown.",
            "  n = n + 1":        "Increases n instead of decreasing it — the loop would never end.",
            "  print(n - 1)":     "Prints one less than the current n, so the countdown is off by one throughout.",
            "n -= 2":             "Decreases n by 2 instead of 1, skipping every other number in the countdown.",
            "while n <= 1:":      "This only keeps looping while n is 1 or less — the opposite of a countdown from 10.",
        },
        "correct_notes": {
            0: "Start the countdown at 10.",
            1: "Keep looping as long as n hasn't gone below 1.",
            2: "Print the current value.",
            3: "Decrease n by 1 each time so the loop eventually ends.",
        },
    },
    {
        "name": "FizzBuzz",
        "description": "Print Fizz, Buzz, FizzBuzz, or the number for 1 to 15",
        "target": [
            "for i in range(1, 16):",
            "  if i % 3 == 0 and i % 5 == 0:",
            "    print(\"FizzBuzz\")",
            "  elif i % 3 == 0:",
            "    print(\"Fizz\")",
            "  elif i % 5 == 0:",
            "    print(\"Buzz\")",
            "  else:",
            "    print(i)",
        ],
        "distractors": [
            "for i in range(1, 15):",
            "  if i % 3 == 0 or i % 5 == 0:",
            "  elif i % 15 == 0:",
            "    print(\"fizzbuzz\")",
            "    print(i + 1)",
            "  if i % 3 == 0:",
        ],
        "explanations": {
            "for i in range(1, 15):":            "Stops one number short — 15 itself is never checked.",
            "  if i % 3 == 0 or i % 5 == 0:":     "Using 'or' here matches numbers divisible by only one of 3 or 5 too early — the combined FizzBuzz case needs 'and'.",
            "  elif i % 15 == 0:":                "Checking divisibility by 15 only makes sense before the separate 3 and 5 checks, not as a later elif — it would never be reached first.",
            "    print(\"fizzbuzz\")":             "Wrong capitalization — inconsistent with 'Fizz' and 'Buzz' elsewhere.",
            "    print(i + 1)":                    "Adds 1 to i, so the plain numbers printed would all be off by one.",
            "  if i % 3 == 0:":                    "Checks for multiples of 3 without first checking for both 3 and 5 — 15 would incorrectly print just 'Fizz'.",
        },
        "correct_notes": {
            0: "Loop through every number from 1 to 15.",
            1: "First check the special case — divisible by both 3 and 5.",
            2: "Print FizzBuzz for that case.",
            3: "Otherwise, check divisible by 3 alone.",
            4: "Print Fizz for that case.",
            5: "Otherwise, check divisible by 5 alone.",
            6: "Print Buzz for that case.",
            7: "If none of the above matched...",
            8: "...just print the number itself.",
        },
    },
    {
        "name": "Sum of Digits",
        "description": "Add up the digits of a number using a while loop",
        "target": [
            "n = 253",
            "total = 0",
            "while n > 0:",
            "  digit = n % 10",
            "  total = total + digit",
            "  n = n // 10",
            "print(total)",
        ],
        "distractors": [
            "while n >= 0:",
            "  digit = n % 100",
            "  total = digit",
            "  n = n / 10",
            "  n = n - 10",
            "print(n)",
        ],
        "explanations": {
            "while n >= 0:":     "Includes n == 0, causing one extra, unnecessary loop iteration at the end.",
            "  digit = n % 100": "Takes the last two digits instead of just the last one.",
            "  total = digit":   "Overwrites the running total each time instead of adding to it.",
            "  n = n / 10":      "Regular division keeps a decimal, so n never reaches exactly 0 — this loop would run forever.",
            "  n = n - 10":      "Subtracts 10 instead of removing the last digit — doesn't shrink toward the next digit correctly.",
            "print(n)":          "Prints n itself (now 0 after the loop) instead of the accumulated total.",
        },
        "correct_notes": {
            0: "Start with the number whose digits we want to sum.",
            1: "Start a running total at 0.",
            2: "Keep looping as long as there are digits left.",
            3: "Get the last digit using % 10.",
            4: "Add that digit to the running total.",
            5: "Remove the last digit using integer division // 10.",
            6: "Print the final sum once all digits are processed.",
        },
    },
    {
        "name": "Factorial (Loop)",
        "description": "Compute a factorial using a loop instead of recursion",
        "target": [
            "n = 5",
            "fact = 1",
            "for i in range(1, n + 1):",
            "  fact = fact * i",
            "print(fact)",
        ],
        "distractors": [
            "fact = 0",
            "for i in range(1, n):",
            "  fact = fact + i",
            "  fact = i",
            "for i in range(0, n + 1):",
            "print(i)",
        ],
        "explanations": {
            "fact = 0":               "Starting the running product at 0 makes every multiplication result in 0.",
            "for i in range(1, n):":  "Stops one short of n, so the loop never multiplies by n itself.",
            "  fact = fact + i":      "Adds instead of multiplying — this computes a sum, not a factorial.",
            "  fact = i":             "Overwrites fact with i each time instead of multiplying — only the last i survives.",
            "for i in range(0, n + 1):": "Starts at 0, and multiplying by 0 at any point would zero out the whole product.",
            "print(i)":               "Prints the last loop variable instead of the accumulated factorial.",
        },
        "correct_notes": {
            0: "Pick the number to compute the factorial of.",
            1: "Start the running product at 1 (the multiplicative identity).",
            2: "Loop i from 1 to n (inclusive).",
            3: "Multiply the running product by the current i.",
            4: "Print the final factorial once the loop finishes.",
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