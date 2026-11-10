# Host adapters {:#hosts}

## Process configuration {:#process}

Mode instructions do not disable plugins. Start a fresh experimental process with `humanize@ramtoshiya` and `humanize-korean@ramtoshiya` disabled in its actual launch settings. Keep other plugins and repository instructions. Main sessions enable this plugin. Separate delegate processes disable it and receive the mode and workflow paths in their briefs. Native subagents inherit the parent's plugin set.

The `pstack-session` launcher from the ramtoshiya skills repository supplies these process overrides. It does not install plugins or change persistent settings. Claude Code can load a local development package with its `--plugin-dir` option. Codex requires native installation and hook trust in `/hooks`. Do not bypass hook trust or restart a shared app-server to force activation.

## Shared routing {:#routing}

Read the shared `ramtoshiya:worker-routing` skill once before spawning. Resolve it through the host's available skills. If the installed shared plugin lacks it, report that installation mismatch instead of inventing another table. Loading this policy does not activate lead mode. The caller keeps its roles, candidate counts, and family constraints.

Use the host's listed model IDs and effort options. Do not carry Cursor model slugs into another host. On Claude Code use `Agent` with `subagent_type: general-purpose`, or the registered `pstack-mode:comment-sicko` for that role. On Codex use `spawn_agent`. Preserve read-only role boundaries even when the API has no `readonly` parameter. Where there is no native agent API, perform the calling skill's roles sequentially as its fallback permits. Do not describe sequential passes as independent fresh workers.

For arena and architect, start with two independent candidate seats. Add seats when the design directions need them, as arena prescribes. Select each seat's row by the shared policy. Use different model families when available. A cross-judge must be outside the parent's model family. Claude and GPT are different families even when both run through Claude Code. A claudex `opus` alias is GPT, not Claude. When no other-family judge can run, keep arena's explicit skip-judge fallback and disclose it. Do not silently describe one family as a diverse panel.

## T3 isolated providers {:#t3}

T3 separate processes do not inherit the parent's command-line plugin settings. Experimental delegates therefore need dedicated provider instances whose launch configuration disables both humanizers, disables this plugin, and sets `AGENTMEMORY_SDK_CHILD=1`. Leave existing instances unchanged. Avoid "worker" in the new instance names so ordinary lead sessions do not select them through their name-based routing.

The experimental main's launch environment may bind these instance IDs:

- `PSTACK_CLAUDE_INSTANCE` selects the isolated Claude delegate instance.
- `PSTACK_CODEX_INSTANCE` selects the isolated Codex delegate instance.
- `PSTACK_CLAUDEX_INSTANCE` selects the isolated claudex delegate instance.

SessionStart adds the available bindings to context. Use the binding for the route selected by worker-routing, including quota switches and escalation. Set `providerInstanceId` explicitly on every `delegate_task` call. These bindings replace only instance lookup, not the shared policy's model table, route choice, quota rules, or effort.

Before using a binding, verify the instance and its model in the host's capability catalog. The instance must have been configured for this experiment. A name alone does not prove humanizer isolation. If a required binding or isolated instance is unavailable, report the missing configuration and do not send that delegate to an ordinary instance or inherit the main instance. Work that needs no separate process can continue. A provider unavailable for a cross-judge still follows arena's skip-judge fallback. This limitation is process isolation, not a weaker comment policy.

Keep bindings and route state in the compaction handoff. Worker briefs that delegate again carry the same bindings and absolute mode paths. A T3 child never loads lead mode merely because it runs on a top-tier model.
