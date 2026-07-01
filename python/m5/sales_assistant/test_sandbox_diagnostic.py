# python/m5/sales_assistant/test_sandbox_diagnostic.py
"""Step-by-step sandbox diagnostic for chart rendering.

Runs each stage of render_chart manually, printing stdout/stderr and
listing sandbox files at each step so failures are visible.

    uv run python test_sandbox_diagnostic.py
"""

from __future__ import annotations

import json
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / "../../.env")

SCRIPT = """\
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

labels = ["Rock", "Latin", "Metal"]
values = [300.0, 137.0, 85.0]
title = "Diagnostic Chart"

fig, ax = plt.subplots(figsize=(8, 5))
ax.bar(labels, values, color="#006DDD")
ax.set_ylabel("Value")
ax.set_title(title)
plt.tight_layout()
plt.savefig("/chart.png", dpi=120)
print("saved /chart.png")
"""


def step(label: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {label}")
    print(f"{'─' * 50}")


def run_and_print(sandbox, command: str) -> None:
    print(f"  $ {command}")
    result = sandbox.run(
        command,
        on_stdout=lambda line: print(f"  stdout: {line}", end=""),
        on_stderr=lambda line: print(f"  stderr: {line}", end=""),
    )
    print(f"  exit code: {result.exit_code}")


def list_files(sandbox, path: str = "/") -> None:
    result = sandbox.run(f"find {path} -maxdepth 2 -type f 2>/dev/null | sort")
    files = result.stdout.strip() if result.stdout else "(none)"
    print(f"  files under {path}:")
    for f in files.splitlines():
        print(f"    {f}")


def main() -> None:
    from langsmith.sandbox import SandboxClient

    client = SandboxClient()

    # Clean up any leftover sandbox from a prior run.
    step("0. Cleanup any existing sandbox")
    try:
        client.delete_sandbox("lca-sandbox-diag")
        print("  deleted existing sandbox")
    except Exception:
        print("  no existing sandbox to delete")

    step("1. Create sandbox")
    sandbox = client.create_sandbox(name="lca-sandbox-diag")
    print(f"  sandbox id: {sandbox.id if hasattr(sandbox, 'id') else 'created'}")

    try:
        step("2. pip install matplotlib")
        run_and_print(sandbox, "pip3 install matplotlib --break-system-packages")

        step("3. Verify matplotlib importable")
        run_and_print(sandbox, "python3 -c \"import matplotlib; print('matplotlib', matplotlib.__version__)\"")

        step("4. Write render script")
        sandbox.write("/render_chart.py", SCRIPT.encode("utf-8"))
        run_and_print(sandbox, "cat /render_chart.py")

        step("5. Run render script")
        run_and_print(sandbox, "python3 /render_chart.py")

        step("6. List files in /")
        list_files(sandbox, "/")

        step("7. Read /chart.png")
        try:
            png = sandbox.read("/chart.png")
            print(f"  SUCCESS — read {len(png):,} bytes")
            out = Path(__file__).parent / "outputs" / "sandbox_diag_chart.png"
            out.parent.mkdir(exist_ok=True)
            out.write_bytes(png)
            print(f"  saved locally to {out}")
        except Exception as exc:
            print(f"  FAILED to read /chart.png: {exc}")
            # Try common alternative paths
            for alt in ["/tmp/chart.png", "./chart.png"]:
                try:
                    png = sandbox.read(alt)
                    print(f"  found at {alt} ({len(png):,} bytes) — savefig path is wrong")
                    break
                except Exception:
                    print(f"  not at {alt} either")

    finally:
        step("8. Cleanup")
        try:
            client.delete_sandbox(sandbox.name)
            print("  sandbox deleted")
        except Exception as exc:
            print(f"  cleanup failed: {exc}")


if __name__ == "__main__":
    main()
