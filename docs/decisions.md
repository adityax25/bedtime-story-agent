# Architecture Decision Records

## ADR 1: Multi-agent pipeline (classify, plan, write, judge, revise)

**Context.** A single prompt that turns a request directly into a story mixes several concerns: understanding the request, structuring a narrative, writing prose, and checking safety.

**Decision.** Split the work into specialized agents: a classifier (category, characters, tone, safety flags), a planner (story arc outline using a category-specific strategy), a storyteller (prose from the outline), a judge, and a reviser. A user feedback loop re-enters the revise and judge stages.

**Consequences.** Each prompt stays focused and independently testable. The plan-then-write split gives the storyteller a structure to follow and gives the judge a reference for what the story was meant to achieve. Cost is a few extra calls per story, which is negligible on Haiku.

## ADR 2: Judge design

**Context.** Naive LLM judges inflate scores, prefer text written by their own model, give unjustified numbers, and can let a safety problem be averaged away by high scores elsewhere.

**Decision.**
- Rubric with anchored descriptions for every score level.
- Critique before score: the judge quotes evidence from the story before scoring each dimension.
- Hard safety gates as pass/fail checks, separate from the averaged quality scores.
- The judge sees only the rubric, the request, and the story, never the storyteller's prompt.
- Pairwise acceptance: a revision replaces the previous draft only if the judge prefers it.
- At most 2 revision rounds.

**Consequences.** Scores carry evidence and are harder to inflate. Revisions cannot silently regress quality. Safety failures always force a revision.

## ADR 3: Extras built after the core

**Context.** The core requirement (storyteller plus judge) must ship before the deadline; extras add creativity but carry schedule risk.

**Decision.** Build in order: core pipeline and judge, then a deterministic readability check (Flesch-Kincaid grade level) and an eval harness with before/after scores, then an animated storybook.

**Consequences.** A complete, submittable system exists before any extra work starts.

## ADR 4: Animated storybook as a self-contained HTML file

**Context.** A narrated, animated story is memorable, but generating images requires a model other than Haiku, which the assignment forbids, and rendered video needs heavy, platform-specific dependencies.

**Decision.** A Scene Director agent returns validated scene JSON; deterministic Python fills an HTML template that animates scenes with CSS and narrates with the browser's speech synthesis.

**Consequences.** No extra models, keys, or system dependencies. Plays in any modern browser.

## ADR 5: Emoji characters on mood-colored scenes

**Context.** Scene visuals can come from emoji and colour palettes, or from model-generated SVG.

**Decision.** Use emoji characters on mood-colored backgrounds. Model-generated SVG is a possible future extension.

**Consequences.** Visuals render reliably and suit a children's storybook; artistic range is limited.

## ADR 6: Small package layout

**Context.** The original skeleton is a single script. The pipeline adds several agents and prompts.

**Decision.** `main.py` stays the CLI entry point. A `storyteller/` package holds the API gateway, schemas, agents, and prompts, with prompts kept in their own files.

**Consequences.** Prompts can be reviewed without reading orchestration code, and every API call goes through one module.

## ADR 7: Structured outputs for machine-read responses

**Context.** The classifier, planner, and judge return data that code acts on. Haiku 5.5 rejects assistant prefill, so JSON cannot be forced by starting the reply with a brace.

**Decision.** Use `client.messages.parse()` with Pydantic models. The API constrains output to the schema and the SDK returns a validated object. The storyteller returns plain prose.

**Consequences.** No hand-written JSON parsing or retry-on-malformed-output logic. Schemas double as documentation of each agent's contract.

## ADR 8: Effort levels instead of temperature

**Context.** Haiku 5.5 returns a 400 for non-default sampling parameters, so temperature cannot differentiate creative and analytical agents.

**Decision.** Steer each agent with `output_config.effort`: classifier `low`, planner `medium`, storyteller `medium`, judge `high`. Creativity is driven by the prompt; consistency by schemas.

**Consequences.** The judge gets the most deliberate reasoning at negligible cost (Haiku 5.5 is $0.10 / $0.50 per million input / output tokens).
