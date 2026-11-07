# Architecture Decision Records

The five decisions that shape the system most. Smaller choices are described in the README.

## ADR 1: A pipeline of specialized agents

**Context.** A single prompt that turns a request directly into a story mixes several jobs: understanding the request, deciding what is safe, structuring a narrative, writing prose, and checking quality. The baseline single-call approach failed at least one safety gate on 6 of 8 eval requests.

**Decision.** Split the work into focused agents, each with its own prompt file: a classifier (category, age band, safety verdict), a planner (story arc built from a category-specific strategy, injected only for the matching category), a storyteller, a judge, a reviser, a pairwise judge, and a feedback interpreter for follow-up turns.

**Consequences.** Each prompt stays short and testable, and the plan gives the judge a structure to check against. A story costs several calls instead of one, which is negligible on Haiku 5.5 and averages under a minute.

## ADR 2: Judge design and calibration

**Context.** LLM judges inflate scores, give unjustified numbers, and can let a safety problem be averaged away. An early version of this judge had the opposite problem: it was so strict that it contradicted itself between rounds and almost never let a story pass.

**Decision.**
- Three pass/fail safety gates, separate from five quality dimensions scored 1 to 5.
- Every score level is anchored, including 4 ("good enough to read to a child tonight"). The missing 4 anchor was the main cause of stories never passing.
- A story passes only when every gate passes and the minimum score, not the average, is at least 4.
- Evidence fields precede verdict fields in the schema, so the model reasons before it decides.
- Gates judge frightening content, not characters' feelings, under a reasonable-parent standard.
- The judge sees the request, audience, and story, never the writer's prompts.

**Consequences.** Seven of eight eval stories pass the full rubric, with 0.9 revision rounds on average. Some leniency remains, documented in the README.

## ADR 3: Safety is guaranteed in code and owned by one judge

**Context.** Prompt rules reduce unsafe output but do not eliminate it: the storyteller produced body horror despite being told not to. Two further gaps appeared during testing: a story could be shown after the revision limit even while failing a gate, and the pairwise judge, applying its own looser sense of safety, rejected a revision that fixed a gate failure.

**Decision.**
- A story that fails any safety gate is never shown. The fallback order is the last draft that passed every gate, then one fresh draft from the plan, then a gentle message with no story. A follow-up change that ends unsafe keeps the previous story.
- The gate judge is the single source of truth for safety. When a draft fails a gate, a revision is accepted on the gate judge's re-check, never on the pairwise judge's opinion.
- Follow-up messages pass through their own intake check, the feedback interpreter, so raw listener text never reaches the reviser. Unclear feedback produces a question rather than a forced rewrite.

**Consequences.** Quality may degrade gracefully at the round limit; safety may not. All 8 eval stories passed every gate, against 2 of 8 for the baseline.

## ADR 4: Revisions must beat the current draft, with facts decided in code

**Context.** Iterative revision fixes one problem and often introduces another. LLM comparisons are biased toward whichever version appears first and toward longer text, and a prompt instruction alone did not stop the length bias.

**Decision.**
- When the current draft is safe, a revision is accepted only if a pairwise judge prefers it on net across both orderings, run in parallel, so position bias cancels out.
- The pairwise judge sees the revision notes (without being told which version is the revision) and exact word counts computed in code.
- Length is a fact, so code decides it: a revision that crosses the length limit is rejected without asking a model.

**Consequences.** Revisions cannot silently regress quality or grow the story without bound. The general principle, that code supplies facts and models supply judgment, also drives the word count and reading grade checks.

## ADR 5: Structured outputs and effort levels on Claude Haiku 5.5

**Context.** The assignment fixes the model, and Haiku 5.5 rejects both assistant prefill and non-default sampling parameters such as temperature. The classifier, planner, judges, and interpreter return data that code acts on.

**Decision.** Machine-read outputs use `client.messages.parse()` with Pydantic schemas, so the API constrains the output and the SDK returns validated objects. Behavior is steered with `output_config.effort` per agent instead of temperature: low for classification and interpretation, medium for planning, writing, revising, and pairwise comparison, high for the judge.

**Consequences.** No hand-written JSON parsing or retry-on-malformed-output logic, and the schemas document each agent's contract. Creativity comes from prompts rather than sampling.

## Planned extension: animated storybook

**Context.** A narrated, animated story would be memorable at bedtime, but generating images requires a model other than Haiku, which the assignment rules out, and rendering video needs heavy, platform-specific dependencies.

**Design.** A Scene Director agent returns validated scene JSON (narration text, setting, mood colors, characters as emoji, a simple motion cue). Deterministic Python fills a self-contained HTML template that animates each scene with CSS and narrates it with the browser's speech synthesis, highlighting each sentence as it is read. The pipeline's progress events can drive the same page.

**Why this shape.** No extra models, keys, or system dependencies; the page plays in any modern browser; and the model's output is treated as untrusted input to a renderer, validated by a schema before use.
