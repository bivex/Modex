# Modex

> **A Model Extractor for the Spin Model Checker**

[![C standard](https://img.shields.io/badge/C-C99%20%2F%20ANSI-blue.svg)](https://en.wikipedia.org/wiki/C_(programming_language))
[![Toolchain](https://img.shields.io/badge/Build-GCC%20%7C%20Bison%20%7C%20Flex-orange.svg)](Src/makefile)
[![Spin Compatible](https://img.shields.io/badge/Model%20Checker-Spin-green.svg)](http://spinroot.com/modex)
[![License](https://img.shields.io/badge/License-Educational%20%2F%20Non--Commercial-lightgrey.svg)](Src/modex.c)

**Modex** is an automated model extractor that mechanically transforms implementation-level **C source code** into **Promela** verification models for the [Spin Model Checker](http://spinroot.com). First developed at Bell Labs starting in 1998 by Gerard J. Holzmann and released as open-source in 2002, Modex enables formal verification of real-world software by bridging the gap between C source code and state-space model checking.

---

## 📋 Table of Contents
- [Why Modex? (Main Problems Solved)](#-why-modex-main-problems-solved)
- [Key Features](#-key-features)
- [How It Works & Workflow](#-how-it-works--workflow)
- [Practical Code Extraction Example](#-practical-code-extraction-example)
- [Prerequisites](#-prerequisites)
- [Building & Installation](#-building--installation)
- [Quick Start Example](#-quick-start-example)
- [Test Harness (.prx) Overview](#-test-harness-prx-overview)
- [Repository Structure](#-repository-structure)
- [Documentation](#-documentation)
- [License & Authors](#-license--authors)

---

## ❓ Why Modex? (Main Problems Solved)

### 1. Bridge Between Specification and Real Code
Writing Promela models by hand is great for algorithms on paper, but production applications are written in **C**. Manual translation from C to Promela introduces human errors, misses edge cases, and creates a discrepancy between the verified model and actual code. 
- **Modex Solution**: Mechanically parses raw `.c` source files and generates `.pml` Promela models automatically.

### 2. Direct Software Model Checking of Production C Code
Modex translates real-world C constructs into formal semantics:
- Variables, pointers, and custom data structures (`struct`).
- Control flow statements (`for`, `while`, `if-else`, function calls).
- Concurrency primitives (`pthreads`, mutexes, condition variables, semaphores).

### 3. Native C Embedding in Spin (`c_code` / `c_expr`)
Spin supports executing pure C snippets inside its generated verifier (`pan.c`). Modex leverages Spin's `c_code { ... }`, `c_expr { ... }`, and `c_state` constructs to avoid simulating complex C calculations in Promela, instead executing them directly during state space exploration.

---

## ✨ Key Features

- **Automated Promela Extraction**: Extracts formal Promela models directly from ANSI C functions.
- **Harness-Driven Abstraction**: Uses a user-defined test harness (`.prx` file) to control data abstraction, variable mapping, environment behavior, and function stubs.
- **Data Flow & Control Analysis**: Performs static data flow analysis to construct accurate control flow graphs and variable dependencies.
- **Integrated Verification Workflow**: Generates models ready for verification with `spin`, `gcc`, and `pan`.

---

## 🔄 How It Works & Workflow

```
   [ Source C Code (app.c) ]
               │
               ▼  (Modex + Harness app.prx / Lookup Table)
   [ Generated Promela Model (app.pml) ]
               │
               ▼  (spin -a app.pml)
   [ C Verifier Source (pan.c) ]
               │
               ▼  (gcc -O3 -o pan pan.c && ./pan)
   [ 🎯 100% Proof of No Deadlocks / Race Conditions in C Code ]
```

1. **Input**: ANSI C source files + `.prx` test-harness configuration script.
2. **Extraction**: Modex parses C code into an AST, applies harness-defined abstractions, and emits a Promela model file (`_model.pml` / `model.nlut`).
3. **Verification**: Spin compiles the model into `pan.c`, which is compiled with `gcc` and executed to verify state space, checking for deadlocks, race conditions, memory bounds, or LTL claims.

---

## 📊 Practical Code Extraction Example

Consider a thread-safe message queue implemented in C:

```c
/* Real C code: queue.c */
void push_msg(Queue *q, Message *msg) {
    pthread_mutex_lock(&q->lock);
    while (q->count == MAX_QUEUE) {
        pthread_cond_wait(&q->not_full, &q->lock);
    }
    q->buffer[q->tail] = msg;
    q->tail = (q->tail + 1) % MAX_QUEUE;
    q->count++;
    pthread_cond_signal(&q->not_empty);
    pthread_mutex_unlock(&q->lock);
}
```

### What Modex does:
1. Parses `queue.c`.
2. Maps `pthread_mutex_lock` and `pthread_cond_wait` into semantic Promela primitives (or wraps them in `c_code` blocks).
3. Generates the `.pml` file for Spin.
4. Spin tests **all possible concurrent interleavings** across dozens of threads to mathematically guarantee freedom from deadlocks and ring buffer overflows!

---

## 🛠 Prerequisites

To build and run Modex, you need:

- **C Compiler**: `gcc` or `clang`
- **Parser Generator**: `bison`
- **Lexical Analyzer**: `flex`
- **Build Automation**: `make`
- **Model Checker** *(for running extracted models)*: [Spin](http://spinroot.com)

---

## 🚀 Building & Installation

### 1. Build from Source
Clone the repository and compile using `make`:

```bash
git clone https://github.com/bivex/Modex.git
cd Modex
make
```

The executable `modex` will be compiled into the `Src/` directory (`Src/modex`).

### 2. Install System-Wide (Optional)
To install `modex` binary and default lookup table to `/usr/local/bin` and `/usr/local/modex`:

```bash
cd Src
sudo make install
```

---

## 💡 Quick Start Example

A minimal example extracting a model from a C program:

### 1. Prepare C Source Code (`hello.c`)
```c
int count = 0;

void increment(void) {
    count++;
}
```

### 2. Create Test Harness (`hello.prx`)
```harness
%   hello.prx
%%
VAR {
    count
}
%
```

### 3. Run Modex
```bash
# Extract Promela model
modex -F hello.prx hello.c

# Run Spin verification
spin -a _model.pml
gcc -o pan pan.c
./pan
```

Explore additional runnable examples in the [`Examples/`](Examples/) and [`Manual/`](Manual/) directories:
- [`Manual/abp.c`](Manual/abp.c) & [`Manual/abp.prx`](Manual/abp.prx) - Alternating Bit Protocol
- [`Examples/4_mutex.c`](Examples/4_mutex.c) - Mutual exclusion verification
- [`Examples/6_suspend.c`](Examples/6_suspend.c) - Thread suspension dynamics

---

## 📜 Test Harness (`.prx`) Overview

The test harness file (`.prx`) instructs Modex on how to abstract C code. Key sections include:

| Section | Description |
| :--- | :--- |
| `%` / `%%` | Separators defining code sections and extraction target settings |
| `VAR { ... }` | Specifies state variables to track in the extracted model |
| `HIDE { ... }` | Excludes unneeded variables to avoid state-space explosion |
| `MAP { ... }` | Maps complex C types/structures to Promela types |
| `STUB { ... }` | Defines stubs for external function calls or system routines |

For full syntax reference, view [`Manual/MANUAL.html`](Manual/MANUAL.html).

---

## 📁 Repository Structure

```
Modex/
├── README.md             # Project overview & documentation
├── makefile              # Top-level build file
├── Src/                  # Source code for Modex engine
│   ├── modex.c           # Main extractor entry point
│   ├── xtract.c          # Promela translation rules
│   ├── gram.y / lexer.l  # Bison parser & Flex scanner
│   ├── symtab.c          # Symbol table management
│   └── tree.c            # Abstract Syntax Tree (AST) handling
├── Manual/               # User manual (MANUAL.html) and harness tutorials
├── Examples/             # Practical C code extraction examples
└── Scripts/              # Automated verification helper scripts
```

---

## 📚 Documentation

- Detailed user documentation: [`Manual/MANUAL.html`](Manual/MANUAL.html)
- Theoretical background & Spin documentation: [http://spinroot.com/modex](http://spinroot.com/modex)

---

## 📄 License & Credits

- **Author**: Gerard J. Holzmann (Bell Labs / Caltech JPL)
- **Copyright**: 
  - Copyright © 2000-2003 Lucent Technologies - Bell Laboratories.
  - Extensions © 2004-2014 Caltech / JPL.
- **License**: Educational & Non-Commercial Use. See license header in [`Src/modex.c`](Src/modex.c).
