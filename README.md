# Kappa Language – Project README
**Author:** Adi Dasgupta  
**Project:** Small Functional Language Implementation — *Kappa*

---

## 1. Overview
This project implements a small **statically typed**, **expression-based**, **functional programming language** called **Kappa**.

Kappa includes:

- A lexer and parser  
- A static type checker  
- An evaluator  
- A REPL  
- Support for running `.kappa` files  
- Support for importing code from other files  
- Basic functional constructs (let-bindings, functions, recursion, lists, sums, pairs)

For a full explanation of language features and examples, see:
- **README.pdf**
- **TUTORIAL.pdf**
- **EXERCISES.md**

---

## Why this exists

Built as the final project for CS-C2170 Programming Languages at Aalto University. The goal was to implement a complete language from scratch — lexer, parser, type checker, evaluator, and REPL — with no parser generators or external language libraries. Everything is hand-written Python.

## 2. Project Structure

```
kappa_project/
│   EXERCISES.md          # Exercises + solutions description
│   kappa.py              # Main interpreter (lexer, parser, type checker, evaluator, REPL)
│   README.md             # This file
│   README.pdf            # Full project documentation
│   TUTORIAL.pdf          # Complete language tutorial
│
└───examples
    │   demo.kappa        # Basic language demo
    │   ex1_sum.kappa
    │   ex2_sumSquares.kappa
    │   ex3_fib.kappa
    │   ex4_sum.kappa
    │   ex5_main.kappa
    │   lib.kappa         # Importable library code
    │   main.kappa        # Simple entry point example
    │
    └───solutions
            ex1_sum_alt.kappa
            ex2_sumSquares.kappa
            ex3_fib.kappa
            ex4_sum.kappa
            ex5_main.kappa
```

---

## 3. Running Kappa

### **Run a file**
```bash
python kappa.py run examples/demo.kappa
```

### **Start the REPL**
```bash
python kappa.py repl
```

Paste any `.kappa` code directly into the REPL.

---

## 4. More Documentation
Additional detailed documentation can be found in:

- **README.pdf** — High-level description  
- **TUTORIAL.pdf** — Runnable examples and language tour  
- **EXERCISES.md** — Problems and tested solutions  

---

## 5. Author
**Adi Dasgupta**  

---
