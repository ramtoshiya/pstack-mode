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
References, helpers, Comment Sicko, and the MIT license are included. The
benchmark checklist is a supporting reference, not another registered skill.

It does not include the poteto-mode controller, poteto-agent wrapper,
setup-pstack model configuration, swarm, playbooks, automatic shipping,
PR babysitting, or overnight autonomy machinery.

## Source and policy

The skills come from `upstream/`, an unchanged copy of the `backnotprop/pstack` mirror.
The no-comments coordinator and both Comment Sicko prompt copies come from Cursor's
original files instead. The generator reads them with git from the mirror commit
named in `CURSOR_ORIGINALS`, which copies `cursor/plugins/pstack` exactly. The
mirror's outside-constraint review exception is not included. Ambiguous keeps are
deleted, a second rejected report fails no-comments, and MUST KILL retains its
original meaning. The workflow can redesign code to remove the need for comments.

[Build instructions](build-mode.md) explain regeneration and syncing. Edit `mode/`
for the controller and hook, and the generator for portable workflow substitutions.
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
use the `pstack-mode:` namespace. Without them Hermes would load `plugin.json`
as a portable package under a generated namespace.

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
restored it. The SessionStart hook recognizes the Claude Code command in its
transcript and restores the mode after compaction. Codex runs a plugin hook only
after you trust it in `/hooks`. Command detection and restoration have not been
verified there.

To start the mode automatically in one repository, add this to its
`.claude/settings.local.json`, or to `.claude/settings.json` to share it:

```json
{ "env": { "PSTACK_MODE": "1" } }
```

The SessionStart hook then loads the mode on startup, resume, clear, and
compaction. Without `PSTACK_MODE=1` the hook does nothing.

## Workers

Every worker brief starts by telling the worker to read the absolute `mode.md`
and `HOSTS.md` paths. That is how a native subagent and a separate T3 or Codex
process enter the mode. Neither inherits the parent's conversation, and a
separate process does not inherit its launch environment or settings. The paths
resolve because every worker runs on the same machine.

Hermes Agent runs no workers itself. It hands implementation and worker roles
to Claude Code, Codex, or claudex with the same brief, through whatever
orchestration its host provides, instead of `delegate_task`. That tool would
run the role on Hermes's own model.

The selected workflows read the shared `ramtoshiya:worker-routing` policy for
model, effort, provider, quota, retry, and escalation. They do not activate lead's
shipping or review workflow. Arena retains independent candidates, base selection,
grafting, verification, and cross-family judgment where another family can run.
The host adapter in `plugins/pstack-mode/HOSTS.md` describes tool names and
compaction behavior.

## Runtime checks

Check a fresh session after `/pstack-mode:mode`, and a native worker and a T3
worker started from it, for the mode's workflow index in their context. On
Codex and Hermes, also check that the session resolves the installed plugin
root. Check
that a session without the command or `PSTACK_MODE=1` does not load the mode.
After compaction, check that the mode returns and route state is retained.

Run no-comments on real code and inspect the resulting diff and behavior. The
generator tests show which policy text ships, not that the agent follows it.
