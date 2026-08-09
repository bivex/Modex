#!/usr/bin/env python3
"""
Modex Pipeline Bottleneck Profiler
Measures time of each pipeline phase: preprocessing, extraction, spin compile, pan run.
"""
import subprocess, time, sys, os, shutil

MODEX = os.path.abspath("Src/modex")
SCRIPTS = os.path.abspath("Scripts/verify")
TEST_FILES = [
    ("Manual/abp.c",          "Alternating Bit Protocol"),
    ("Manual/mutex.c",        "Mutex (race condition)"),
    ("Examples/real_queue.c", "Ring Buffer Queue"),
    ("Examples/5_incdec.c",   "CAS inc/dec"),
]

def run(cmd, cwd="."):
    t0 = time.perf_counter()
    r = subprocess.run(cmd, shell=True, capture_output=True, cwd=cwd)
    elapsed = time.perf_counter() - t0
    return elapsed, r.returncode, r.stdout.decode(errors="replace"), r.stderr.decode(errors="replace")

def profile_file(src, label):
    src_abs = os.path.abspath(src)
    src_dir  = os.path.dirname(src_abs)
    src_name = os.path.basename(src_abs)

    print(f"\n{'='*60}")
    print(f"  Target : {label}  [{src}]")
    print(f"{'='*60}")

    # Phase 1 — Modex extraction
    env = f'PATH={os.path.abspath("Src")}:$PATH'
    t, rc, out, err = run(f"{env} modex {src_name}", cwd=src_dir)
    print(f"  [1] modex extraction        : {t*1000:7.1f} ms  (rc={rc})")
    if rc != 0:
        print(f"      FAILED: {err[:200]}")
        return

    # Phase 2 — spin -a (model → pan.c)
    t, rc, out, err = run("sh _modex_.run prep 2>/dev/null || spin -a model", cwd=src_dir)
    print(f"  [2] spin -a (gen pan.c)     : {t*1000:7.1f} ms  (rc={rc})")

    # Phase 3 — gcc compile pan.c
    pan_c = os.path.join(src_dir, "pan.c")
    if os.path.exists(pan_c):
        t, rc, out, err = run("gcc -O2 -o pan pan.c 2>/dev/null", cwd=src_dir)
        print(f"  [3] gcc -O2 pan.c → pan     : {t*1000:7.1f} ms  (rc={rc})")

        # Phase 4 — ./pan verification
        pan_bin = os.path.join(src_dir, "pan")
        if os.path.exists(pan_bin):
            t, rc, out, err = run("./pan -E 2>&1 | tail -5", cwd=src_dir)
            print(f"  [4] ./pan verification      : {t*1000:7.1f} ms  (rc={rc})")
            # Print state stats
            for line in out.splitlines():
                if any(k in line for k in ["states", "transitions", "depth", "errors", "elapsed"]):
                    print(f"      {line.strip()}")
    else:
        print("      spin did not produce pan.c — model extraction incomplete")

    # Cleanup
    for f in ["pan", "pan.c", "pan.h", "pan.m", "pan.b", "pan.t", "pan.p",
              "model", "_modex_.run", "model.trail", "_spin_nvr.tmp"]:
        fp = os.path.join(src_dir, f)
        if os.path.exists(fp):
            os.remove(fp)
    for f in ["model.M", src_name.replace(".c", ".M"),
              src_name.replace(".c", ".nlut")]:
        fp = os.path.join(src_dir, f)
        if os.path.exists(fp):
            os.remove(fp)

def main():
    print("\nModex Pipeline Bottleneck Profiler")
    print("=" * 60)
    print(f"  Modex binary: {MODEX}")
    print(f"  Platform    : {subprocess.check_output('uname -sm', shell=True).decode().strip()}")
    print(f"  Spin version: {subprocess.check_output('spin -V 2>&1 | head -1', shell=True).decode().strip()}")

    for src, label in TEST_FILES:
        if os.path.exists(src):
            profile_file(src, label)
        else:
            print(f"\n  SKIP (not found): {src}")

    print("\n" + "="*60)
    print("  Profiling complete.")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
