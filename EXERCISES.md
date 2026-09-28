# Exercises — Kappa Language (Handout)

This document contains the problem statements for the five programming exercises used in the project.
Each exercise includes a short description, required deliverables, example input (if applicable), expected behavior, and a grading hint.

---

## Exercise 1 — Sum of a List
**Feature tested:** Lists, pattern matching, recursion  
**Difficulty:** Easy

**Task.** Implement a function `sum : [Int] -> Int` that computes the sum of elements in a list of integers.

**Deliverables.**
- `examples/ex1_sum.kappa` — exercise file (problem statement only)
- `examples/solutions/ex1_sum_alt.kappa` — solution file (do not include solutions in the exercise file)

**Example.**
```
sum [1,2,3]  => 6
sum []       => 0
```

**Notes.**
- Use pattern matching on lists (`[]` and `[h | t]`).
- Use recursion via `fix`. Because top-level recursive `let` bindings are unreliable in this interpreter, prefer an immediately-applied `fix` for testing, or use a `let ... in ...` form if supported by your version.

**Grading tip.**
- Correctness on several test lists (including empty list).
- Proper static typing (`[Int] -> Int`) and rejection of invalid calls (e.g., `sum true` should be a type error).

---

## Exercise 2 — Sum of Squares
**Feature tested:** Lists, recursion, arithmetic  
**Difficulty:** Easy–Medium

**Task.** Implement `sumSquares : [Int] -> Int` that computes the sum of squares of elements in a list.

**Deliverables.**
- `examples/ex2_sumSquares.kappa` — exercise file
- `examples/solutions/ex2_sumSquares.kappa` — solution file

**Example.**
```
sumSquares [1,2,3]  => 1*1 + 2*2 + 3*3 = 14
sumSquares []       => 0
```

**Notes.**
- Use the same recursion / pattern-matching technique as Exercise 1.
- Keep the function body self-contained to avoid top-level `let` issues.

**Grading tip.**
- Correct results for multiple lists, including negative numbers; correct typing.

---

## Exercise 3 — Fibonacci
**Feature tested:** Recursion, conditionals, function application  
**Difficulty:** Medium

**Task.** Implement `fib : Int -> Int` using naive recursion (fixed-point combinator). `fib 0 = 0`, `fib 1 = 1`.

**Deliverables.**
- `examples/ex3_fib.kappa` — exercise file
- `examples/solutions/ex3_fib.kappa` — solution file

**Example.**
```
fib 6  => 8
fib 0  => 0
```

**Notes.**
- Use `if` / `then` / `else` constructs.
- Use `fix` for recursion.

**Grading tip.**
- Correct values for moderate n (e.g., n=0..8).
- Proper type signature `Int -> Int` and clean error messages on invalid inputs.

---

## Exercise 4 — Sum Types and Pattern Matching
**Feature tested:** Sum types (`inl` / `inr`), pattern matching, type checking  
**Difficulty:** Medium

**Task.** Create a small expression demonstrating sum types and pattern matching. Write a function `describe` (or equivalent) that accepts a sum value (either `inl Int` or `inr Bool`) and returns an `Int` result depending on the case.

**Deliverables.**
- `examples/ex4_sum.kappa` — exercise file
- `examples/solutions/ex4_sum.kappa` — solution file

**Example behavior.**
```
describe (inl 10)  => 11    # e.g., add 1 to Int contained in inl
describe (inr true) => 1    # e.g., map true->1, false->0
```

**Notes.**
- Ensure both branches return values of the same type (e.g., `Int`) so the match expression has a consistent type.
- Include a commented failing example that demonstrates type errors (e.g., matching an `Int` without `inl/inr`).

**Grading tip.**
- Correct matching behavior and typed branches.
- Clear demonstration that the type checker rejects mismatches.

---

## Exercise 5 — Imports and Modules
**Feature tested:** Declarations, modules, imports  
**Difficulty:** Easy

**Task.** Use the provided library file `examples/lib.kappa` (contains `let pi`, `let inc`, `let add`) and write a program that imports it and uses those definitions.

**Deliverables.**
- `examples/ex5_main.kappa` — exercise file (problem statement)
- `examples/lib.kappa` — small library (provided)
- `examples/solutions/ex5_main.kappa` — solution

**Example.**
```
import "examples/lib.kappa"
[inc 5, (add 2 3), pi]  => [6, 5, 3]
```

**Notes.**
- The grader will check that imports behave by bringing top-level bindings into the importing environment.
- Provide a brief comment in the solution explaining how import resolution is expected to work.

**Grading tip.**
- Correct usage of imported names, and demonstration that the imports are type-checked and evaluated before use.

---

## Submission instructions for exercises
- Put the exercise problem files in `examples/` (no solutions inside these files).
- Put the solutions in `examples/solutions/`.
- Ensure your README and TUTORIAL.md reference each exercise file and the expected behavior.
- Include at least one failing example (commented) per exercise to show the grader that incorrect programs are rejected.

---

## Hints & Common Pitfalls
- The interpreter performs static typing before evaluation; type errors are reported and prevent evaluation.
- For recursive functions, prefer immediately-applied `fix` expressions when you want the test to run reliably.
- Avoid top-level `let` recursion patterns that depend on the interpreter's particular handling of recursive names.
