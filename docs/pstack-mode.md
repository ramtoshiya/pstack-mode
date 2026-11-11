# Pstack session mode

The generated package is `plugins/pstack-mode/`. It starts the selected mode
through a SessionStart hook, including on resume, clear, and compaction. No mode
command or custom default agent is needed. Native host instructions stay in place.

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

## Install for one repository

From the ramtoshiya skills checkout, run its repository installer once:

```sh
node tools/pstack-session/install-project.mjs /path/to/project /path/to/pstack-mode/plugins/pstack-mode
```

Then start Claude Code or claudex normally in that project. No custom shell
command, plugin flags, or additional-directory flags are needed on each launch.
The registered command is `/pstack-mode:no-comments`.

The installer copies this generated package and the current shared `ramtoshiya`
plugin into the project's ignored `.claude/pstack/` directory. It registers a
private local marketplace through Claude's native CLI and saves enablement in
`.claude/settings.local.json`. It disables both humanizer plugins and selects
the shared snapshot for that repository only. Other plugins, settings, and global
and repository instructions remain. The shared policy is an installed copy of
the same source that lead uses, not a separate model table.

Run setup again to refresh the snapshots after source changes. There is no
published marketplace pin for this candidate and none is needed for the local
installation. The optional `pstack-session` launcher remains a process-only
alternative, not a prerequisite for normal repository launches.

Start a fresh session after setup. Existing sessions cannot unload instructions
they already received. Unslop and technical-writing replace only the two writing
plugins' behavior, not global or repository instructions.

## Codex

Codex does not read Claude's repository settings. For Codex workers, put these
overrides in the project's `.codex/config.toml`, preserving existing settings:

```toml
[plugins."humanize@ramtoshiya"]
enabled = false

[plugins."humanize-korean@ramtoshiya"]
enabled = false
```

Workers receive the mode and role paths in their briefs. Automatic mode activation
for a Codex main session additionally requires native installation and explicit
hook trust in `/hooks`. The Claude repository installer does not perform that
installation or grant trust. Do not bypass trust or restart a shared app-server.

## Workers

The selected workflows read the shared `ramtoshiya:worker-routing` policy for
model, effort, provider, quota, retry, and escalation. They do not activate lead's
shipping or review workflow. Arena retains independent candidates, base selection,
grafting, verification, and cross-family judgment where another family can run.

Native subagents inherit process plugin configuration. Separate Claude processes
can read the same repository settings. Codex workers need the separate overrides
above. A provider that already loads those settings needs no new instance or
launcher. Briefs provide the absolute mode and role paths, and workers perform
only their assigned roles.

Ignored settings and payloads do not necessarily reach a new isolated worktree.
Different host profiles may also load different configuration. Configure that
working directory before its session starts, or use an isolated provider with
both humanizers disabled. Optional `PSTACK_CLAUDE_INSTANCE`,
`PSTACK_CODEX_INSTANCE`, and `PSTACK_CLAUDEX_INSTANCE` bindings select those
providers without changing the routing policy. The host adapter in
`plugins/pstack-mode/HOSTS.md` describes selection and compaction behavior.

## Runtime checks

Check a fresh main and a native worker for loaded mode instructions, the two
humanizer skills' absence, and unrelated skills' presence. Inspect hook execution,
not only plugin configuration. After compaction, check that the mode returns and
route state is retained. Check separate T3 processes independently because the
parent's plugin settings do not transfer to them.

Run no-comments on real code and inspect the resulting diff and behavior. Static
prompt hashes protect source policy but do not show that the agent followed it.
