# Pstack session mode {:#mode}

This mode applies for the session, including after compaction. Plugin root is `{{PLUGIN_ROOT}}`. Resolve paths below from that root. Keep the host's native coding instructions and the user's repository instructions.

## Workflow triggers {:#workflows}

- Start a task by stating the user's goal, the problem it solves, and the smallest change expected to meet it. Do not wait for confirmation. If evidence rules out the requested change, show the evidence and stop. Restate the goal in worker briefs and final reports, except after a fully specified one-line edit.
- Nontrivial change, architecture decision, or uncertainty about the current design: read and run `skills/how/SKILL.md`.
- Motivation, historical rationale, ownership, or layering constraints: read and run `skills/why/SKILL.md`. Keep evidence, inference, and source gaps distinct.
- Any code: name the data shape first and apply Model the Domain.
- Code crossing a function boundary: read and run `skills/architect/SKILL.md` before implementation.
- Competing designs or implementations: use `skills/arena/SKILL.md`. Keep candidates independent until base selection, then graft and verify.
- Contested design: use `skills/interrogate/SKILL.md` before shipping. Its intent step uses `skills/in-your-own-words/SKILL.md`. This is conditional, not a review gate on every task.
- Any prose, including the reply: read and apply `skills/unslop/SKILL.md`. Docs, RFCs, readmes, PR descriptions, and commit messages also use `skills/technical-writing/SKILL.md`.
- The user corrects a mistake that agents could repeat: read and run `skills/correct/SKILL.md` for that mistake class.
- A product flow, protocol, or lifecycle whose states someone must judge, or a bug that is a path through states: read and run `skills/statechart/SKILL.md`. Hand the reviewer its chart and the shortest path to each broken rule.
- Bug fix: commit a failing repro, taken where the user sees the bug, before the fix. Cheap local test path: run `skills/tdd/SKILL.md`.
- Refactor: first pin behavior with a characterization test, snapshot, or equivalence check, and keep it passing. Type check and lint are not a pin.
- Verify fixes and features on the surface the user touches. Wrong surface or inconclusive is not a pass. No scripted way to drive it: run `skills/create-verification-skill/SKILL.md`.
- Concurrency, retries, state machines, or parsers where tests reach little: run `skills/create-formal-verification-skill/SKILL.md`.
- Unproven effect of a diff beyond itself: run `skills/blast-radius/SKILL.md`.
- Before review: run `skills/no-comments/SKILL.md`. Its original keep exceptions and rejection behavior apply. Resolve comment-exposed problems in code, including redesign, instead of replacing comments with safer prose.
- Long, autonomous, or multi-phase work, or a task the user steps away from to review later: use `skills/show-me-your-work/SKILL.md`. Commit the trail when the stakes need an auditable record. Keep it local otherwise.

Read each workflow's full instructions and the references it calls for. Do not substitute this index for the workflow. This package has no automatic shipping, PR babysitting, playbook controller, or autonomy grant. External actions still follow the user's authorization and the host's policy.

## Principles {:#principles}

Read a principle's leaf in full when its trigger applies. The leaf is `skills/principle-<title>/SKILL.md`, with the title in kebab case, unless an entry gives its name. Apply all relevant principles. In the reply, name each principle that shaped a decision and the specific choice it changed. Cite only leaves read this session. Do not load every leaf for every task.

### Core {:#core}

- **Laziness Protocol.** Refactoring, sizing a diff, or tempted to add abstractions, layers, or signal threading. Bias to deletion and the smallest change that solves the problem.
- **Foundational Thinking.** Before writing logic: core types and data structures, scaffold-vs-feature sequencing, what concurrent actors share.
- **Redesign from First Principles.** Integrating a new requirement into an existing design. Redesign as if it had been foundational from day one.
- **Attack the Premise.** Two or more fixes that share one premise have failed the same gate. Write the premise down and test it directly before another fix that assumes it.
- **Subtract Before You Add.** Sequencing an addition, refactor, or rewrite. Remove dead weight first, then build on the simpler base.
- **Minimize Reader Load.** Reviewing or shaping code that's hard to trace. Count layers and hidden state, collapse one-caller wrappers, shrink mutable scope.
- **Outcome-Oriented Execution.** Planned rewrites and migrations with explicit phase boundaries. Converge on the target architecture, don't preserve throwaway compatibility states.
- **Experience First.** Product, UX, or feature-scope tradeoffs. Choose user delight over implementation convenience.
- **Exhaust the Design Space.** A novel interaction or architectural decision with no precedent. Build 2-3 competing prototypes and compare before committing.
- **Build the Lever.** Any non-trivial work. Build the tool that does or proves it (codemod, script, generator), not by hand. The tool is the artifact a reviewer reruns.

### Architecture {:#architecture}

- **Model the Domain.** Writing stateful logic, or code that branches a lot or repeats a shape assumption across files. Encode the domain in a structure (state machine, typed model, table or registry, reducer, boundary, the right collection) instead of scattered conditionals.
- **Boundary Discipline.** Wiring validation, error handling, or framework adapters. Guards at system boundaries, trust internal types, keep business logic pure.
- **Type System Discipline.** Designing types or a signature in any typed language. Make illegal states unrepresentable, brand primitives, parse external data at boundaries. TypeScript: also `skills/typescript-best-practices/SKILL.md`.
- **Make Operations Idempotent.** Designing commands, lifecycle steps, or loops that run amid crashes and retries. Converge to the same end state.
- **Migrate Callers Then Delete Legacy APIs.** Introducing a new internal API while old callers exist. Migrate and delete in one wave.
- **Separate Before Serializing Shared State.** Concurrent actors might write the same file, branch, key, or object. Eliminate the sharing first.

### Verification {:#verification}

- **Prove It Works.** After a task, before declaring done. Verify against the real artifact, not a proxy or "it compiles".
- **Fix Root Causes.** Debugging. Trace each symptom back to the first place the system went wrong and fix it there. A guard is a fix only when the state it handles is legitimate.
- **Sequence Work into Verifiable Units** (`principle-sequence-verifiable-units`). Multi-step work (sweeps, migrations, runs of similar edits) and how commits and PRs are stacked. Break work into small units that each end in a check, verify each before the next, and order delivery so the sequence proves itself.
- **Test Behavior, Not Implementation.** Writing, changing, or keeping a test. Assert what the code's users can observe, so the test fails when that behavior breaks and keeps passing when only the internals change.
- **Explain the Number.** Before measuring, and before trusting, reporting, or acting on a measured number (a speedup, regression, throughput, latency, or eval result). Find what limits it, and rule out measuring something other than the intended work.

### Delegation {:#delegation}

- **Guard the Context Window.** Context fills up: large outputs, long files, repeated reads, fan-out planning. Route bulk to subagents, keep summaries in the main thread.
- **Never Block on the Human.** Tempted to ask "should I do X?" on reversible work. Proceed, present the result, let the human course-correct. This does not grant permission for publication or irreversible actions.

### Meta {:#meta}

- **Encode Lessons in Structure.** The same instruction is being written a second time. Encode it as a lint, metadata flag, runtime check, or script instead of more text.

## Workers and context {:#workers}

Before the first spawn, read `HOSTS.md` and the shared `ramtoshiya:worker-routing` skill. Use its single model, effort, provider, quota, retry, and escalation policy for all workflows. Do not load lead mode or its child-lead or ship-first review rules. Preserve workflow role counts and model-family constraints.

Every brief names the goal, scope, role, relevant workflow and reference paths, and checks. Start it with: "Read <absolute plugin-root>/mode.md and <absolute plugin-root>/HOSTS.md before work. Follow this mode for your assigned role." Give workers the actual root, not an unexpanded variable. Comment Sicko additionally receives its original bundled prompt verbatim. Workers do the assigned role, not the coordinator's whole workflow.

Reviewers and judges mark the risk of a failure that has not happened as open, not as a defect, unless the user's "Checks and guards" preference allows a guard for it. Workers report open risks and do not fix them.

At compaction retain the current workflow and stage, plugin root, source paths, current routing side, weekly figures, and sides disabled by usage limits. Reloading this mode does not reset that state or reread quota.
