"""The README's code blocks, as the live check runs them.

    python readme_blocks.py list           # JSON matrix for the block jobs (ONLY filters)
    python readme_blocks.py run N          # run block N with the real token, one retry
    python readme_blocks.py cli-syntax     # every README CLI line with a dummy key

One parser for all three, so the list and the runner can never disagree on
what block N is.
"""

import json
import os
import pathlib
import re
import subprocess
import sys
import time

README = pathlib.Path(__file__).resolve().parents[2] / "README.md"
SKIP = ("pip install", "export ", "npm i", "npm install",
        "npx -p @brightdata/cli bdata login", "bdata login")
CLI = os.environ.get("BDATA_CLI", "")  # the pinned CLI version; empty means whatever is installed


def blocks():
    readme = README.read_text(encoding="utf-8")
    # never execute anything inside the generated field table: its text comes from
    # the API, and a fence in a description must not become a command
    readme = re.sub(r"<!-- fields:start -->.*?<!-- fields:end -->", "", readme, flags=re.S)
    found, heading, seen = [], "README", {}
    for m in re.finditer(r"^#{2,3} ([^\n]+)$|```(python|bash)\n(.*?)```", readme, re.M | re.S):
        if m.group(1):
            heading = m.group(1).strip()  # a block is named after its section, not its first line
            continue
        lang, code = m.group(2), m.group(3)
        lines = [line for line in code.splitlines()
                 if line.strip() and not line.strip().startswith("#")]
        if lang == "bash":
            lines = [line for line in lines if not line.startswith(SKIP)]
            if not lines:
                continue
            code = "\n".join(lines)
        seen[heading] = seen.get(heading, 0) + 1
        title = heading if seen[heading] == 1 else f"{heading} ({seen[heading]})"
        found.append({"lang": lang, "title": title[:50], "code": code})
    return found


def cli_lines(code, key):
    """The CLI cannot open a browser here, so the key goes in by flag, and an
    unpinned npx is held to the version the job installed."""
    out = []
    for line in code.splitlines():
        if CLI:
            line = line.replace("npx -p @brightdata/cli ", f"npx -p @brightdata/cli@{CLI} ")
        if "bdata pipelines" in line:
            line += f" -k {key}"
        out.append(line)
    return "\n".join(out)


def list_blocks():
    wanted = {int(n) for n in os.environ.get("ONLY", "").split(",") if n.strip()}
    out = [{"n": i + 1, "lang": b["lang"], "title": b["title"]}
           for i, b in enumerate(blocks()) if not wanted or i + 1 in wanted]
    print("blocks=" + json.dumps(out))


def run_block(n):
    b = blocks()[n - 1]
    if b["lang"] == "bash":
        # only the shell ever sees the key's value
        argv = ["bash", "-e", "-c", cli_lines(b["code"], '"$BRIGHTDATA_API_TOKEN"')]
    else:
        argv = [sys.executable, "-c", b["code"]]
    secret = os.environ.get("BRIGHTDATA_API_TOKEN", "")
    for _attempt in (1, 2):
        started = time.time()
        try:
            run = subprocess.run(argv, capture_output=True, text=True, timeout=480)
        except subprocess.TimeoutExpired:
            run = subprocess.CompletedProcess(
                argv, 1, "", "block timeout: no result within 8 minutes")
        secs = round(time.time() - started)
        out, err = run.stdout.strip(), run.stderr.strip()
        if secret:  # summaries are not secret-masked the way logs are
            out, err = out.replace(secret, "***"), err.replace(secret, "***")
        ok = run.returncode == 0 and bool(out if b["lang"] == "python" else out or err)
        if ok or ((out or err) and "timeout" not in (out + err).lower()):
            break
        time.sleep(30)  # the API timed out or answered with nothing at all; one retry
    if ok:
        shown = (out.splitlines() or [""])[:1]
    else:
        # the last few lines: a CLI error often puts the cause above its hint
        shown = (err.splitlines() or out.splitlines() or ["no output"])[-6:]
    body = "\n".join("    " + line[:160] for line in shown)
    state = "ok" if ok else "FAILED"
    print(f"\n`{b['title']}`: {state} in {secs}s (exit {run.returncode})\n\n{body}")
    sys.exit(0 if ok else 1)


def cli_syntax():
    """Run every README CLI line with a key the API rejects. A line the CLI
    still understands reaches the API and gets a 401; a line it no longer
    understands fails before that. Free, and needs no secret."""
    failed = 0
    print("| block | CLI line | result |\n| --- | --- | --- |")
    for i, b in enumerate(blocks(), 1):
        if b["lang"] != "bash":
            continue
        for line in b["code"].splitlines():
            if "bdata pipelines" not in line:
                continue
            run = subprocess.run(["bash", "-c", cli_lines(line, "invalid-key-for-syntax-check")],
                                 capture_output=True, text=True, timeout=120)
            text = run.stdout + run.stderr
            ok = "401" in text or "Invalid credentials" in text
            last = (run.stderr.strip().splitlines() or run.stdout.strip().splitlines()
                    or ["no output"])
            why = "reached the API" if ok else " / ".join(x.strip() for x in last[-3:])[:200]
            print(f"| {i} | `{line[:90]}` | {'ok' if ok else 'FAILED'}: {why.replace('|', '/')} |")
            if not ok:
                failed = 1
                print(f"::error::README block {i}: the CLI rejects `{line}`", file=sys.stderr)
    sys.exit(failed)


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else ""
    if mode == "list":
        list_blocks()
    elif mode == "run":
        run_block(int(sys.argv[2]))
    elif mode == "cli-syntax":
        cli_syntax()
    else:
        sys.exit(__doc__)
