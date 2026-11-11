# Task protocol / 任务恢复

`python3 scripts/task.py init runs/task.json --brief examples/brief.json`

The example is a template, not permission to generate. Replace its reference with an actual inspected file, record the user's scope and save the final prompt before submission.

`python3 scripts/task.py advance runs/task.json submitting --evidence "Settings and user scope checked"`

Write `submitting` BEFORE calling the external provider. Then record `submitted --task-id ID` after success, or `uncertain` after a timeout. A crash while submitting is also treated as uncertain by `resume`. A local exclusive lock prevents concurrent journal mutations. It does NOT lock a provider account or guarantee exactly-once generation.

`python3 scripts/task.py resume runs/task.json`

Main path: prepared → submitting → submitted → generating → generated → downloaded → verified → delivered. submitted can go directly to generated. submitted/generating can become failed. All transitions require nonempty `--evidence`. Evidence is operator-supplied; the journal does not certify its truth.

uncertain → submitted requires the found task ID. uncertain → prepared requires recorded evidence that the provider did not accept the request; it is never an automatic retry. Preserve the same task ID thereafter. A terminal failure requires a separate authorized attempt, not rewriting history.

Network failure while polling/downloading leaves the task at its last confirmed state. `verified` evidence should identify the validator report and separate visual review; `delivered` should identify the artifact and host rendering outcome. Local records can contain private URLs; `runs/` is ignored by Git.

Writes use an exclusive lock and atomic replacement. If a process is killed, a `.lock` may remain: confirm no writer is active before manually removing that lock. Local filesystem only; not a distributed queue.
