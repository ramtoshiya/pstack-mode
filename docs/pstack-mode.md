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

Install the plugin for your user from this checkout. Nothing is published. The
shared `ramtoshiya:worker-routing` skill comes from the `ramtoshiya` plugin,
which must also be installed on the same host.

Claude Code:

```sh
claude plugin marketplace add /path/to/pstack-mode
claude plugin install pstack-mode@pstack-local --scope user
```

After rebuilding, run `claude plugin marketplace update pstack-local` and
`claude plugin update pstack-mode@pstack-local --scope user`, then start a new
session.

Codex reads the same marketplace and copies the plugin into its cache:

```sh
codex plugin marketplace add /path/to/pstack-mode
codex plugin add pstack-mode@pstack-local
```

After rebuilding, run `codex plugin add pstack-mode@pstack-local` again to
refresh the copy, then start a new session.

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
start a Codex prompt with `$pstack-mode:mode`. The command loads `mode.md`
with the installed plugin root filled in, and the mode applies for the rest of
the session. Compaction would otherwise reduce the command's text to a summary,
so the SessionStart hook loads `mode.md` again when the session's transcript
shows that you ran the command. The model cannot start the mode by itself.

Only Claude Code expands `${CLAUDE_PLUGIN_ROOT}` in the command. The command
tells other hosts that the plugin root is the directory that contains
`skills/mode/`, and Codex and Hermes show the model that path. Codex keeps the
model from starting the mode through `skills/mode/agents/openai.yaml`. Hermes
has no such setting and lists the mode with its other skills, so its model can
load the mode without the command. Hermes does not run the SessionStart hook,
so there the mode does not reload after compaction and `PSTACK_MODE=1` does not
start it. Codex runs a plugin hook only after you trust it in `/hooks`, and the
hook has not been tested there.

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
