# Pstack session mode

The generated package is `plugins/pstack-mode/`. Install it once for your user,
then start the mode in a session with `/pstack-mode:mode`. Until then the
package only adds its commands. Native host instructions stay in place.

## Contents

The package selects `no-comments`, `how`, `why`, `architect`, `arena`,
`interrogate`, `in-your-own-words`, `show-me-your-work`, `unslop`, and
`technical-writing`, plus all 24 `principle-*` skills. The mode loads the complete
principle applicability index and reads individual bodies when relevant.
References, helpers, Comment Sicko, and the MIT license are included. The
benchmark checklist is a supporting reference, not another registered skill.

It does not include the poteto-mode controller, poteto-agent wrapper,
setup-pstack model configuration, swarm, playbooks, automatic shipping,
PR babysitting, or overnight autonomy machinery.

## Source and policy

The source mirror is `backnotprop/pstack` at
`08547969e1dffaa6457ea65141cc62c1d9a2eef1`. The no-comments coordinator and both
Comment Sicko prompt copies use the Cursor originals at
`de8ee15dd1194627d21eb5fcd41cb1873208dabb`. The mirror's outside-constraint review
exception is not included. Ambiguous keeps are deleted, a second rejected report
fails no-comments, and MUST KILL retains its original meaning. The workflow can
redesign code to remove the need for comments.

`source-selection.json` in the generated package records source and output hashes.
[Build instructions](build-mode.md) explain regeneration. Edit `mode/` for the
controller and hook, and the generator for portable workflow substitutions.
Do not edit generated files directly.

## Install

Register this checkout as a local marketplace and install the plugin for your
user. Nothing is published.

```sh
claude plugin marketplace add /path/to/pstack-mode
claude plugin install pstack-mode@pstack-local --scope user
```

After rebuilding, run `claude plugin marketplace update pstack-local` and
`claude plugin update pstack-mode@pstack-local --scope user`, then start a new
session. The shared `ramtoshiya:worker-routing` skill comes from the
`ramtoshiya` plugin, which must also be installed.

## Activate

Run `/pstack-mode:mode` at the start of a session. The command loads `mode.md`
with the installed plugin root filled in, and the mode applies for the rest of
the session. The model cannot start the mode by itself.

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

The selected workflows read the shared `ramtoshiya:worker-routing` policy for
model, effort, provider, quota, retry, and escalation. They do not activate lead's
shipping or review workflow. Arena retains independent candidates, base selection,
grafting, verification, and cross-family judgment where another family can run.
The host adapter in `plugins/pstack-mode/HOSTS.md` describes tool names and
compaction behavior.

## Runtime checks

Check a fresh session after `/pstack-mode:mode`, and a native worker and a T3
worker started from it, for the mode's workflow index in their context. Check
that a session without the command or `PSTACK_MODE=1` does not load the mode.
After compaction, check that the mode returns and route state is retained.

Run no-comments on real code and inspect the resulting diff and behavior. Static
prompt hashes protect source policy but do not show that the agent followed it.
