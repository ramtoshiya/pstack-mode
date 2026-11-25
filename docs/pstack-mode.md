# Pstack session mode

The generated package is `plugins/pstack-mode/`. Install it once for your user,
then start the mode in a session with `/pstack-mode:mode`. Until then the
package only adds its commands. Native host instructions stay in place.

## Contents

The package selects `no-comments`, `how`, `why`, `architect`, `arena`,
`interrogate`, `in-your-own-words`, `show-me-your-work`, `unslop`,
`technical-writing`, `correct`, and `statechart`, plus all 24 `principle-*`
skills. `statechart` runs TypeScript with Node 22.18 or later, Bun, or Deno, and
its first run installs TLC and Java with mise. The mode loads the complete
principle applicability index and reads individual bodies when relevant.
References, helpers, Comment Sicko, and the MIT license are included.

The mode has no trigger line for these skills, so run each one yourself, for
example `/pstack-mode:teach` in Claude Code or `$pstack-mode:teach` in Codex:

| Skill | What it does |
| --- | --- |
| `teach` | Explains a change or subsystem plainly, using `how` and `why` |
| `bro` | Restates the last message in plain words |
| `ketchup` | Catches you up on what changed in the chat and lists what waits on you |
| `sharpen` | Rewrites a prompt to make the task deeper, not bigger |
| `reframe` | Teaches the expert words for what you are building and rewrites your description with them |
| `recall` | Rebuilds your recent working context from chat transcripts and the shared record |
| `reflect` | Proposes skill edits from what the current transcript taught, and waits for approval |
| `figure-it-out` | Designs and runs an auditable workflow for a large task that no narrower skill fits |
| `swarm` | Fans out parallel workers and returns one report |
| `benchmark-checklist` | Vets a performance measurement before you report or act on it. `principle-explain-the-number` links to it |

The verification layer turns checks into project artifacts instead of prose:

| Skill | What it leaves behind |
| --- | --- |
| `create-verification-skill` | A project-local `verify-<app>` skill that launches, drives, and captures evidence from the app's real surface, with a feature map |
| `maintain-verification-skill` | Corrections to that skill and its map after the app changes |
| `create-formal-verification-skill` | A project-local check, shown to fail on a broken variant, with a coverage record and sync commit |
| `maintain-formal-verification-skill` | That check brought back in line with changed code, each failure judged as drift or a bug |
| `tdd` | A regression test that fails before a bug fix and passes after it |
| `blast-radius` | Proof, by running code, of what a change cannot break elsewhere |
| `typescript-best-practices` | TypeScript rules that `principle-type-system-discipline` links to |

The mode carries the discipline of pstack's bug-fix, refactoring, and feature
playbooks as trigger lines instead of the playbooks themselves. A bug fix
commits a failing repro before the fix. A refactor pins behavior first, and
type check and lint do not count as a pin. A fix or feature is verified on the
surface its user touches. The playbooks are not copied because they depend on
the poteto-mode controller, its subagent section, model IDs, and its PR flow.

It does not include the poteto-mode controller, poteto-agent wrapper,
setup-pstack model configuration, playbooks, automatic shipping, PR
babysitting, or overnight autonomy machinery. Upstream text that points at
those parts is rewritten for this package. `recall`, `figure-it-out`, and
`swarm` take worker models from `ramtoshiya:worker-routing` instead of the
poteto-mode subagent table or the setup-pstack settings file. `figure-it-out`
reads the principles from `mode.md`, and `reflect` finds transcripts through
`recall`'s list of locations. `swarm` uses the host's delegation tools instead
of Cursor cloud agents. `benchmark-checklist` drops its notes on the Perf issue
and Hillclimb playbooks.

## Source and policy

The skills come from `upstream/`, an unchanged copy of the `backnotprop/pstack` mirror.
The no-comments coordinator and both Comment Sicko prompt copies come from Cursor's
original files instead. The generator reads them with git from the mirror commit
named in `CURSOR_ORIGINALS`, which copies `cursor/plugins/pstack` exactly. The
mirror's outside-constraint review exception is not included. Ambiguous keeps are
deleted, a second rejected report fails no-comments, and MUST KILL retains its
original meaning. The workflow can redesign code to remove the need for comments.

This package adds a pre-check that pstack does not have. Before no-comments starts
Comment Sicko, `scripts/no-comments-precheck.py` scans the whole content of every
file in the review scope. It looks for comments, docstrings, lint or type
suppressions, and disabled code such as `#if 0`. When it finds none, the workflow
reports the script's output and does not start the reviewer. It knows the comment
syntax of common languages and skips past strings, so `"https://…"` is not a
comment. A file type it does not know, text it cannot lex with confidence, or a
scope it cannot resolve starts the reviewer as before.

[Build instructions](build-mode.md) explain regeneration and syncing. Edit `mode/`
for the controller, hook, and pre-check, and the generator for portable workflow substitutions.
Do not edit generated files directly.

## Install

The `ramtoshiya` marketplace in
[ramtoshiya/skills](https://github.com/ramtoshiya/skills) lists this package
pinned to a commit of this repository. The mode needs the shared
`ramtoshiya:worker-routing` skill from the `ramtoshiya` plugin in the same
marketplace, so install both on each host.

Claude Code:

```sh
claude plugin marketplace add ramtoshiya/skills
claude plugin install ramtoshiya@ramtoshiya --scope user
claude plugin install pstack-mode@ramtoshiya --scope user
```

Codex:

```sh
codex plugin marketplace add ramtoshiya/skills
codex plugin add ramtoshiya@ramtoshiya
codex plugin add pstack-mode@ramtoshiya
```

Start a new session after installing or updating. [Build
instructions](build-mode.md) describe how a change reaches the pin.

Hermes Agent loads the package through a link, so a rebuild takes effect in the
next session:

```sh
mkdir -p ~/.hermes/plugins
ln -s /path/to/pstack-mode/plugins/pstack-mode ~/.hermes/plugins/pstack-mode
hermes plugins doctor ~/.hermes/plugins/pstack-mode --ci
hermes plugins enable pstack-mode
```

`plugin.yaml` and `__init__.py` make it a native Hermes plugin, so its skills
use the `pstack-mode:` namespace. The package has no root `plugin.json`. Codex
0.171.0 reads a root `plugin.json` that declares the agent-plugins schema in
place of `.codex-plugin/plugin.json` and then loads no hooks, so the
SessionStart hook would never run there.

## Activate

Run `/pstack-mode:mode` at the start of a session in Claude Code or Hermes, or
start a Codex prompt with `$pstack-mode:mode`. The entry skill directs the agent
to read `mode.md` from the installed plugin root before working and apply it for
the session. The model cannot start the mode by itself on Codex or Claude Code.

The entry skill resolves the plugin root from its own `skills/mode/` path and
uses that root for the placeholder in `mode.md`. Codex keeps the
model from starting the mode through `skills/mode/agents/openai.yaml`. Hermes
has no such setting and lists the mode with its other skills, so its model can
load the mode without the command. Hermes does not run the SessionStart hook,
so there `PSTACK_MODE=1` does not start it. The entry skill asks the agent to
retain the root and reload the mode after compaction when the host has not
restored it. In Claude Code the activation hook (`hooks/activation.py`) keeps the mode on for
the rest of a session that activated it. A session counts as activated when its
transcript shows the command, when its first message is a worker brief that reads
`mode.md` from a pstack-mode plugin root, or when a user message is a bb relay
header (`[bb message from thread:<id>]` and a blank line) followed by
`/pstack-mode:mode`. Claude Code does not run a relayed command, so on that
turn the UserPromptSubmit hook injects `mode.md` itself. On every later user turn
it injects a short turn check that points at the principle index in `mode.md`.
The turn that carries a typed command gets no check, because the transcript does
not yet contain the command, and the command itself loads the mode. There is no
deactivation, and sessions that never activated get nothing. After compaction the
SessionStart hook restores `mode.md` for an activated session, and the turn
check on the next prompt adds no second copy. For a brief it injects that root's
`mode.md`, so a brief that names a development build or another installed version
gets the file it named. The root counts as pstack-mode when its
`.claude-plugin/plugin.json` has that name. Each prompt scans the transcript
for the command and stops at the first match. A 130 MB transcript with no match
takes about 0.2 to 0.5 seconds, plus about 0.2 seconds for `uv` to start.
Codex runs a plugin hook only
after you trust it in `/hooks`. Command detection and restoration have not been
verified there.

To start the mode automatically in one repository, add this to its
`.claude/settings.local.json`, or to `.claude/settings.json` to share it:

```json
{ "env": { "PSTACK_MODE": "1" } }
```

The SessionStart hook then loads the mode on startup, resume, clear, and
compaction, and every prompt gets the turn check. Without `PSTACK_MODE=1` the
hook stays silent until a session activates the mode.

## Workers

Every worker brief starts by telling the worker to read the absolute `mode.md`
and `HOSTS.md` paths. That is how a native subagent and a separate worker
process enter the mode. Neither inherits the parent's conversation, and a
separate process does not inherit its launch environment or settings. The paths
resolve because every worker runs on the same machine.

Hermes Agent runs no workers itself. It hands implementation and worker roles
to Claude Code, Codex, or claudex with the same brief, through whatever
orchestration its host provides, instead of `delegate_task`. That tool would
run the role on Hermes's own model.

The selected workflows read the shared `ramtoshiya:worker-routing` policy for
model, effort, provider, quota, urgency, retry, and escalation. Arena retains independent candidates, base selection,
grafting, verification, and cross-family judgment where another family can run.
The host adapter in `plugins/pstack-mode/HOSTS.md` describes tool names and
compaction behavior.

## Runtime checks

Check a fresh session after `/pstack-mode:mode`, and a native worker and a
separate worker started from it, for the mode's workflow index in their context. On
Codex and Hermes, also check that the session resolves the installed plugin
root. Check
that a session without the command or `PSTACK_MODE=1` does not load the mode.
After compaction, check that the mode returns and route state is retained.

Run no-comments on real code and inspect the resulting diff and behavior. The
generator tests show which policy text ships, not that the agent follows it.
