# Modex Verification Guide

> Complete step-by-step documentation for mechanically extracting Promela models from C code and running formal verification with the Spin Model Checker.

---

## 📚 Table of Contents
1. [Overview](#1-overview)
2. [Prerequisites & Build](#2-prerequisites--build)
3. [Step 1: Preparing C Source Code](#step-1-preparing-c-source-code)
4. [Step 2: Generating Test Harness (.prx)](#step-2-generating-test-harness-prx)
5. [Step 3: Executing Verification](#step-3-executing-verification)
6. [Step 4: Interpreting Results & Error Trails](#step-4-interpreting-results--error-trails)
7. [Step 5: Advanced LTL Safety & Liveness Properties](#step-5-advanced-ltl-safety--liveness-properties)
8. [Real-World Examples](#real-world-examples)

---

## 1. Overview

Modex extracts **Promela models** from implementation-level **C code**. Spin then explores 100% of the state space across all possible concurrent thread interleavings to mathematically prove freedom from:
- **Deadlocks**
- **Race conditions**
- **Assertion violations** (`assert(...)`)
- **Invalid end states**

---

## 2. Prerequisites & Build

### Requirements
- **C Compiler**: `gcc` or `clang`
- **Parser & Lexer**: `bison` (Bison 3.x+ supported), `flex`
- **Model Checker**: [Spin](http://spinroot.com)

### Building Modex Engine
```bash
git clone https://github.com/bivex/Modex.git
cd Modex
make
```
The executable binary will be generated at [`Src/modex`](file:///Volumes/External/Code/Modex/Src/modex).

---

## Step 1: Preparing C Source Code

Ensure your C target module has clearly identifiable state variables and concurrent entry points.

Example (`my_module.c`):
```c
int counter = 0;

void increment(void) {
    counter++;
}

void decrement(void) {
    counter--;
}
```

---

## Step 2: Generating Test Harness (.prx)

A `.prx` harness guides Modex on which variables to track and how to execute concurrent processes.

### Option A: Automatic Generation using `modex-gen` (Recommended)
Run the built-in C99 AST generator:
```bash
Scripts/modex-gen my_module.c -o my_module.prx --threads 2
```

### Option B: Manual Harness Creation
Create `my_module.prx`:
```harness
%F my_module.c
%%
VAR {
    counter
}

%P
/* Model 2 concurrent threads calling C functions */
active [2] proctype harness() {
    if
    :: increment();
    :: decrement();
    fi
}
%
```

### Directives Reference:
| Directive | Purpose |
| :--- | :--- |
| `%F filename.c` | Target C file name |
| `VAR { x, y }` | State variables to track in state space |
| `HIDE { x }` | Omit non-essential variables to prevent state explosion |
| `MAP { int -> byte }` | Map C types to Promela types |
| `%P` | Promela processes definition block |

---

## Step 3: Executing Verification

Run the automated verification script:
```bash
PATH=$PWD/Src:$PATH Scripts/verify my_module.c
```

### Under the Hood Execution Pipeline:
1. **Extraction**: Modex processes `my_module.c` using `my_module.prx` to generate `my_module.M` and `_modex_.run`.
2. **Spin Compilation**: `sh _modex_.run` executes `spin -a` to produce `pan.c`.
3. **Verifier Build**: Compiles `pan.c` using `gcc -o pan pan.c`.
4. **State Space Exploration**: Runs `./pan` to verify all thread interleavings.

---

## Step 4: Interpreting Results & Error Trails

### Success Case (`No Errors Found`):
```text
State-vector 128 byte, depth reached 15, errors: 0
58 states, stored
No Errors Found
```
This confirms **100% formal proof** that no race conditions or deadlocks exist.

### Error Case (`Assertion Violation / Deadlock`):
If Spin encounters a fault, it halts and writes a `model.trail` file:
```text
pan:1: assertion violated (now.counter==1)
pan: wrote model.trail
```

### Replaying Error Trails:
To inspect the exact sequence of C statement executions that led to the fault:
```bash
./pan -C
```

### Cleaning Artifacts:
To clean generated verification files:
```bash
Scripts/verify clean
```

---

## Step 5: Advanced LTL Safety & Liveness Properties

You can specify **Linear Temporal Logic (LTL)** properties inside the `.prx` file:

```harness
%F my_module.c
%%
VAR {
    counter
}

%P
/* Safety claim: counter must never exceed 10 */
ltl max_bound { [] (counter <= 10) }

active [2] proctype harness() {
    increment();
}
%
```

Run verification with LTL acceptance check:
```bash
PATH=$PWD/Src:$PATH Scripts/verify -a my_module.c
```

---

## Real-World Examples

Try running the included verification benchmarks:
- **Mutual Exclusion Bug**: `PATH=$PWD/Src:$PATH Scripts/verify Manual/mutex.c`
- **Atomic CAS Operations**: `PATH=$PWD/Src:$PATH Scripts/verify Examples/5_incdec.c`
- **Lock-Free Queue**: `PATH=$PWD/Src:$PATH Scripts/verify Examples/real_queue.c`
