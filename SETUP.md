# Setup Instructions — paste this whole file to your AI assistant

> **You (the contributor) do not need to run these commands yourself.** Paste this file as your
> first message to your AI coding assistant. Everything below is addressed to the assistant.

---

## Assistant: your task

Install and verify the tooling needed to author Frontier Bench tasks on this machine. Work
autonomously. Ask the contributor only when you need a password, an admin approval, or a decision
you genuinely cannot make. Assume the contributor is **not a software engineer**: never hand them a
command to run themselves, never explain a stack trace to them, and never end your turn with
"you may want to try…". Diagnose and fix it yourself, then report in plain language.

Work through the steps in order. Do not skip verification.

---

## Step 0 — Detect the platform

Determine the operating system and shell you are working in, and use the matching commands below.
On Windows, prefer the **native Windows** path: the `harbor` CLI runs fine on Windows as long as
Docker is running, so WSL is **not** required. Do not install WSL, and do not migrate the
contributor's files into a Linux filesystem, unless a later step fails in a way that specifically
requires it.

---

## Step 1 — Verify Docker (prerequisite, must already exist)

Docker is the one thing the contributor is responsible for. Confirm it is genuinely working — not
merely installed — by checking that the daemon responds and can pull and run an image:

```
docker --version
docker info
docker run --rm hello-world
```

All three must succeed.

**If `docker info` fails**, the daemon is not running. Try to start it (start Docker Desktop on
Windows/macOS, or `sudo systemctl start docker` on Linux), wait for it to become ready, and retry.

**If `docker run hello-world` fails but `docker info` succeeds**, the problem is image pulling —
usually a network, proxy, or registry-authentication issue. Diagnose it now. Do not continue:
every later step depends on pulling images, and failures there will look like `harbor` bugs.

**If Docker cannot be made to work at all**, stop and tell the contributor clearly that Docker must
be fixed before anything else can proceed, with the specific reason you found. Do not attempt to
install Docker yourself unless the contributor explicitly asks — on Windows and macOS that involves
GUI installers, licence acceptance, and possibly a reboot, which is their decision to make.

---

## Step 2 — Install `uv`

`uv` is the Python package manager used to install the `harbor` CLI. It installs into the user's
home directory and needs no administrator rights.

First check whether it already exists (`uv --version`). If it does, skip to Step 3.

**Windows (PowerShell):**
```
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

**macOS / Linux:**
```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

If the machine has a package manager the contributor already uses (Homebrew, winget), that is an
acceptable alternative: `brew install uv` or `winget install --id=astral-sh.uv -e`.

---

## Step 3 — Install the `harbor` CLI

```
uv tool install harbor
```

This installs three executables: `harbor`, `hb`, and `hr`. `harbor` is the one this project uses.

---

## Step 4 — Fix the PATH (do not skip this)

`uv` installs tools into a user-local directory (`~/.local/bin`, or `C:\Users\<name>\.local\bin` on
Windows) and **warns rather than fixing the PATH itself**. If you skip this, `harbor` will appear to
be missing in every future shell and the contributor will think the install failed.

Run:

```
uv tool update-shell
```

Then **start a fresh shell** and confirm the binary resolves there. Verifying in your current shell
is not sufficient — the current process may have a PATH you modified in-session, which will not
persist. The check is:

```
harbor --version
```

It should print a version number (`0.20.0` or later). If it does not resolve in a fresh shell, add
the directory to the user's persistent PATH yourself, then verify again in another fresh shell.

---

## Step 5 — Smoke test

Confirm the whole toolchain works end to end by scaffolding a throwaway task in a temporary
directory (**not** in the contributor's project folder) and inspecting the result:

```
harbor init afterquery/smoke-test-task -t --include-standard-metadata -o <temp-dir>
```

This should create `instruction.md`, `task.toml`, `environment/Dockerfile`, `solution/solve.sh`,
`tests/test.sh`, and `tests/test_outputs.py`. Confirm the files exist, then delete the temporary
directory.

Also confirm the two commands the workflow depends on are available:

```
harbor run --help
harbor check --help
```

---

## Step 6 — Wire up the operating manual

`AGENTS.md` in this workspace is the system prompt for the project. Make sure it will be loaded
automatically in future sessions, so the contributor never has to paste it. Do this yourself:

| Assistant | What to create |
|---|---|
| Claude Code | `CLAUDE.md` containing the single line `@AGENTS.md` |
| Cursor / Windsurf / Codex / Gemini CLI | Nothing — `AGENTS.md` is picked up automatically |
| GitHub Copilot | `.github/copilot-instructions.md` containing the contents of `AGENTS.md` |
| Anything else | Whatever that tool's project-instructions file is; if it has none, tell the contributor they must paste `AGENTS.md` at the start of each session |

Do not duplicate the text of `AGENTS.md` when a reference will do — two copies drift apart.

Then read `AGENTS.md` yourself before continuing.

---

## Step 7 — Report back

Tell the contributor, in plain language and without jargon:

- Which tools were already present and which you installed.
- The `harbor` version now available.
- Confirmation that Docker can pull and run images.
- Anything you changed on their system (PATH edits in particular).
- Any problem you could not resolve, what it blocks, and what you need from them.

Then tell them what happens next: the tooling is ready, you have read the operating manual, and the
work begins whenever they are ready to talk through their task idea.

**End this report by showing them the domain category table.** Reproduce the category table from
Stage 1 of `AGENTS.md` **verbatim — full table, all seven rows, descriptions and labels, no
paraphrasing or shortening**. It is the guideline's own taxonomy: every task is filed under exactly
one of these categories with 1–6 of these labels, and the contributor should see the full menu
before they settle on an idea, not after. Invite them to tell you where their expertise sits.

---

## Troubleshooting notes

**`harbor: command not found` in a new terminal.** The PATH step did not take effect. Re-run
`uv tool update-shell`, or write the tools directory into the user's shell profile or persistent
environment yourself. Always verify in a *newly started* shell.

**Corporate proxy or TLS interception.** `uv` and Docker both need outbound HTTPS. If installs fail
with certificate errors, the machine is likely behind an intercepting proxy; configure the proxy
environment variables rather than disabling certificate verification.

**Windows line endings.** If the contributor's Git or editor is configured to convert to CRLF, shell
scripts inside task bundles will fail inside Linux containers with confusing errors such as
`cannot execute: required file not found`. Ensure `.sh` files are written with LF endings. The
project template includes a `.gitattributes` that enforces this; keep it.

**Do not run `harbor` under `sudo`.** It is installed per-user; elevating changes the PATH and the
tool will appear to be missing.
