# Host adapters {:#hosts}

## Activation {:#process}

The plugin is installed for the user and stays inactive until activated. Run `/pstack-mode:mode` to start the mode in a session. After compaction the SessionStart hook loads the mode again when the transcript shows that command. A repository can opt in to automatic activation by setting `PSTACK_MODE=1` in its Claude settings `env`. The SessionStart hook then loads the mode on startup, resume, clear, and compaction. Existing sessions cannot unload instructions they already received.

Workers enter the mode through their brief, not through settings or launch environment. A native subagent shares the parent's plugin set but not its conversation. A separate T3 process loads its own configuration. Both receive the absolute `mode.md` and `HOSTS.md` paths in the brief, and the paths resolve on the same machine.

## Shared routing {:#routing}

Read the shared `ramtoshiya:worker-routing` skill once before spawning. Resolve it through the host's available skills. If the host cannot resolve it, report the installation mismatch instead of inventing another table. Loading this policy does not activate lead mode. The caller keeps its roles, candidate counts, and family constraints.

Use the host's listed model IDs and effort options. Do not carry Cursor model slugs into another host. On Claude Code use `Agent` with `subagent_type: general-purpose`, or the registered `pstack-mode:comment-sicko` for that role. On Codex use `spawn_agent`. Preserve read-only role boundaries even when the API has no `readonly` parameter. Where there is no native agent API, perform the calling skill's roles sequentially as its fallback permits. Do not describe sequential passes as independent fresh workers.

For arena and architect, start with two independent candidate seats. Add seats when the design directions need them, as arena prescribes. Select each seat's row by the shared policy. Use different model families when available. A cross-judge must be outside the parent's model family. Claude and GPT are different families even when both run through Claude Code. A claudex `opus` alias is GPT, not Claude. When no other-family judge can run, keep arena's explicit skip-judge fallback and disclose it. Do not silently describe one family as a diverse panel.

## T3 providers and working directories {:#t3}

Use the provider selected by worker-routing. Keep the existing worker profile's `AGENTMEMORY_SDK_CHILD=1`. A new isolated checkout or a different host profile need not load the parent's settings, so the brief is the only activation a worker can rely on. Worker briefs that delegate again carry the same absolute mode paths. Keep working-directory assumptions and route state in the compaction handoff. A T3 child never loads lead mode merely because it runs on a top-tier model.
