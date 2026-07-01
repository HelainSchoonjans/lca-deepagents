# python/m5/sales_assistant/test_sandbox_matplotlib.py
"""Standalone sandbox diagnostic — no LLM.

Spins up a LangSmith sandbox, runs pip install matplotlib, then executes a
minimal plot script.  Prints exit codes, stdout/stderr, and wall-clock time
at each step so we can see exactly where (and whether) the install fails.

Usage:
    uv run python test_sandbox_matplotlib.py
"""

from __future__ import annotations

import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "../../.env")

_PLOT_SCRIPT = """\
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
fig, ax = plt.subplots()
ax.bar(["A", "B", "C"], [1, 2, 3])
ax.set_title("sandbox-test")
plt.savefig("/test_chart.png", dpi=72)
print("saved /test_chart.png")
"""


def _step(sandbox, label: str, cmd: str, timeout: int = 60) -> bool:
    """Run cmd, print timing + output, return True if exit_code == 0."""
    print(f"\n[{label}]")
    print(f"  $ {cmd}")
    t0 = time.monotonic()
    result = sandbox.run(cmd, timeout=timeout)
    elapsed = time.monotonic() - t0
    print(f"  exit_code : {result.exit_code}  ({elapsed:.1f}s)")
    if result.stdout:
        for line in result.stdout.strip().splitlines():
            print(f"  stdout    : {line}")
    if result.stderr:
        for line in result.stderr.strip().splitlines():
            print(f"  stderr    : {line}")
    return result.exit_code == 0


def main() -> None:
    try:
        from langsmith.sandbox import SandboxClient
    except ImportError as exc:
        print(f"SKIP  langsmith.sandbox not importable: {exc}")
        return

    import uuid
    name = f"lca-matplotlib-diag-{uuid.uuid4().hex[:8]}"
    print(f"\nCreating sandbox: {name}")
    client = SandboxClient()
    sandbox = client.create_sandbox(name=name)
    print("Sandbox ready.\n")

    try:
        # 1. Check Python version
        _step(sandbox, "python version", "python3 --version")

        # 2. Check if matplotlib is already installed
        already = _step(sandbox, "import check (expect fail)", "python3 -c 'import matplotlib; print(matplotlib.__version__)'")
        if already:
            print("  => matplotlib already installed — skipping pip install")
        else:
            # 3. pip install
            ok = _step(sandbox, "pip install matplotlib", "pip3 install matplotlib --break-system-packages", timeout=180)
            if not ok:
                print("\nFAIL  pip install did not exit 0 — chart rendering will fail for students")
                return

        # 4. Run the plot script
        sandbox.write("/plot.py", _PLOT_SCRIPT.encode())
        ok = _step(sandbox, "render plot", "python3 /plot.py")
        if ok:
            png = sandbox.read("/test_chart.png")
            print(f"\nPASS  chart rendered — {len(png):,} bytes")
        else:
            print("\nFAIL  plot script exited non-zero")

    finally:
        print(f"\nDeleting sandbox: {name}")
        try:
            client.delete_sandbox(sandbox.name)
        except Exception:
            pass
        print("Done.")


if __name__ == "__main__":
    main()
