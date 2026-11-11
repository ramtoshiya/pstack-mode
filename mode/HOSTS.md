# Host adapters {:#hosts}

## Repository and process configuration {:#process}

Mode instructions do not disable plugins. Start a fresh experimental session with `humanize@ramtoshiya` and `humanize-korean@ramtoshiya` disabled in the host's actual configuration. Keep other plugins and repository instructions. Existing sessions cannot unload instructions they already received.

The repository installer from the ramtoshiya skills checkout puts this package and the shared plugin in `.claude/pstack/`, registers a private local marketplace, and saves overrides in that repository's `.claude/settings.local.json`. Normal Claude Code and claudex launches then load the mode without command-line plugin flags. Native subagents inherit the process plugin set. Separate Claude processes in the same repository can read the same saved overrides. Workers still do only their assigned role, not the coordinator's whole workflow.

Codex does not read `.claude/settings.local.json`. For Codex workers, disable both humanizers in the repository's `.codex/config.toml`. Their briefs supply the absolute mode and workflow paths. Starting a Codex main session with automatic mode activation additionally requires native plugin installation and explicit hook trust in `/hooks`. Do not bypass hook trust or restart a shared app-server to force activation.

The optional `pstack-session` launcher supplies process-only overrides. Its `--delegate` path disables this plugin as well and supplies mode instructions through the worker brief. Command-line overrides do not transfer to a separate process.

## Shared routing {:#routing}

Read the shared `ramtoshiya:worker-routing` skill once before spawning. Resolve it through the host's available skills. In the repository-local installation, that same policy is also at `../ramtoshiya/skills/worker-routing/SKILL.md` relative to this plugin root. Read the file when the host has no Skill tool or cannot resolve the namespace. If neither is available, report the installation mismatch instead of inventing another table. Loading this policy does not activate lead mode. The caller keeps its roles, candidate counts, and family constraints.

Use the host's listed model IDs and effort options. Do not carry Cursor model slugs into another host. On Claude Code use `Agent` with `subagent_type: general-purpose`, or the registered `pstack-mode:comment-sicko` for that role. On Codex use `spawn_agent`. Preserve read-only role boundaries even when the API has no `readonly` parameter. Where there is no native agent API, perform the calling skill's roles sequentially as its fallback permits. Do not describe sequential passes as independent fresh workers.

For arena and architect, start with two independent candidate seats. Add seats when the design directions need them, as arena prescribes. Select each seat's row by the shared policy. Use different model families when available. A cross-judge must be outside the parent's model family. Claude and GPT are different families even when both run through Claude Code. A claudex `opus` alias is GPT, not Claude. When no other-family judge can run, keep arena's explicit skip-judge fallback and disclose it. Do not silently describe one family as a diverse panel.

## T3 providers and working directories {:#t3}

Repository-scoped settings can apply to separate T3 processes. Use the provider selected by worker-routing when its working directory and configuration load the opted-in repository's humanizer overrides. Claude hosts use `.claude/settings.local.json`. Codex hosts use `.codex/config.toml`. Keep the existing worker profile's `AGENTMEMORY_SDK_CHILD=1`. A provider name alone does not prove which configuration it loads.

A new isolated checkout does not necessarily contain ignored plugin payloads or local settings. A different host profile can also load different settings. Do not assume the parent's plugin configuration transfers to either. Configure the intended working directory before its session starts, or use an isolated provider already configured to disable both humanizers. Do not send substantive work to a process whose required isolation is missing.

For process-only setups, the experimental main's launch environment may bind isolated instances:

- `PSTACK_CLAUDE_INSTANCE` selects the Claude delegate instance.
- `PSTACK_CODEX_INSTANCE` selects the Codex delegate instance.
- `PSTACK_CLAUDEX_INSTANCE` selects the claudex delegate instance.

SessionStart adds available bindings to context. When a binding is supplied, verify its instance and model in the host's capability catalog and set `providerInstanceId` explicitly on every `delegate_task` call for that route. Bindings replace only instance lookup, not model rows, route choice, quota rules, effort, retries, or escalation. They are not required for providers that already load the repository's overrides. Do not fall back from an unavailable binding to an unconfigured ordinary process. A provider unavailable for a cross-judge still follows arena's skip-judge fallback.

Keep bindings, working-directory assumptions, and route state in the compaction handoff. Worker briefs that delegate again carry the same configuration requirements and absolute mode paths. A T3 child never loads lead mode merely because it runs on a top-tier model.
