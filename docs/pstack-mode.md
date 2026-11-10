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

## Local Claude Code session

Install the `pstack-session` command from the ramtoshiya skills repository's
`tools/pstack-session/README.md`. The shared `ramtoshiya` plugin must provide
`worker-routing`. From this checkout, start a fresh session:

```sh
pstack-session --plugin-dir "$PWD/plugins/pstack-mode" claude
```

Use `claudex` in place of `claude` for that launch path. The launcher disables
humanize and humanize-korean in process settings, including their hooks, without
changing persistent settings. It preserves other enabled plugins and settings.
Global and repository writing instructions remain. Unslop and technical-writing
replace only the two plugins' behavior in this experiment.

Existing sessions cannot unload already-injected instructions. A fresh process
is required. The plugin alone cannot disable another plugin.

## Installed sessions and Codex

An installed package can be launched with `pstack-session claude` or
`pstack-session codex`. This checkout does not supply a published marketplace pin.
Do not register an invented remote commit. Until there is a published package,
use the local Claude Code path above.

Codex has no equivalent local `--plugin-dir` launch flag. Native installation and
explicit hook trust in `/hooks` are required. The launcher does not install the
package, grant trust, or restart a shared app-server. Disabling the humanizers
uses unquoted Codex override paths, for example
`-c plugins.humanize@ramtoshiya.enabled=false`.

## Workers

The selected workflows read the shared `ramtoshiya:worker-routing` policy for
model, effort, provider, quota, retry, and escalation. They do not activate lead's
shipping or review workflow. Arena retains independent candidates, base selection,
grafting, verification, and cross-family judgment where another family can run.

Native subagents inherit process plugin configuration. Separate T3 delegates
need isolated provider instances with the humanizers disabled. Use
`pstack-session --delegate claude`, `claudex`, or `codex` as their launch path.
The delegate mode also disables pstack-mode and sets `AGENTMEMORY_SDK_CHILD=1`.
Briefs provide the absolute mode and role paths.

Bind the instance IDs with `PSTACK_CLAUDE_INSTANCE`, `PSTACK_CODEX_INSTANCE`, and
`PSTACK_CLAUDEX_INSTANCE` in the experimental main's environment. The host adapter
in `plugins/pstack-mode/HOSTS.md` describes selection and compaction behavior.
Do not rename or alter normal providers. If isolated instances are not configured,
the mode reports the missing binding rather than sending work to normal providers.

## Runtime checks

Check a fresh main and a native worker for loaded mode instructions, the two
humanizer skills' absence, and unrelated skills' presence. Inspect hook execution,
not only plugin configuration. After compaction, check that the mode returns and
route state is retained. Check separate T3 processes independently because the
parent's plugin settings do not transfer to them.

Run no-comments on real code and inspect the resulting diff and behavior. Static
prompt hashes protect source policy but do not show that the agent followed it.
