---
name: ai-video-prompt-director
description: Turn video ideas and references into actionable prompts, shot plans, reference roles and acceptance criteria; revise prompts using observed results.
metadata:
  version: "0.1.0"
---
# Video prompt director

Use the user's language. Read [prompt methods](references/prompt-method.md) for creative work, [timing](references/model-and-timing.md) for transitions and music alignment, and [iteration](references/iteration.md) when incorporating results.

1. Inspect available references. Separate observed facts, user requirements and creative assumptions. Assign identity, scene, opening/ending frame or motion roles.
2. Identify what must remain stable and what changes. Write beginning → action → intermediate state → ending, with camera movement separately specified.
3. Preserve the user's priorities; resolve conflicting references. Ask only for missing information that materially changes the result.
4. Deliver the actual prompt, reference roles, proposed settings and observable acceptance criteria. Use the [shot card](assets/shot-card.md) as needed. Relative times belong to this clip; editing instructions belong outside the submitted prompt.
5. When the user requests generation, hand off to the adjacent `kling-video-producer` skill if Kling is appropriate and available. Prompt-only or discussion requests do not authorize uploads or generation. Other requested providers take precedence. Return to the calling producer without recursive skill invocation.

Do not promise exact identity, frame-level timing or a perfect copy. Record observed failures before changing guidance; distinguish text review from real generation tests.
