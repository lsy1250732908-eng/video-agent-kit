---
name: kling-video-producer
description: Help produce and deliver a Kling video from an idea and reference images, including task recovery, local MP4 validation and inline playback where supported.
metadata:
  version: "0.1.0"
---
# Kling video producer

Activate for an actual video-production request. Installation grants no standing spending or upload authorization. Honor user-selected providers, output folders, budgets and prompt-only requests.

1. Check existing task records before creating work. Use the adjacent prompt-director skill to prepare the prompt, reference roles, parameters and acceptance criteria. Save them before submission.
2. Prefer an available official integration. See [provider routes](references/providers.md); this package does not implement an API client. Use browser guidance only when that is the available route.
3. For local task tracking, follow the repository [task protocol](../../docs/task-protocol.md). If installed standalone, maintain equivalent JSON records. Mark submitting BEFORE the external call. A timeout is an unknown outcome, not permission to submit again. Reconcile with the provider's history before retrying.
4. Confirm uploads actually appear, read actual settings and current credit cost, then submit within the user's authorization. No automatic purchases or unbounded paid regeneration. Login/verification handoffs stay in the provider UI.
5. Follow the same task until complete or blocked. Save its task ID and result location locally. A download failure must not start another generation.
6. Obtain the user's accessible official result using the documented connector/browser download. Do not guess signed URLs or extract credentials. An observed official download URL may be used by an allowed download tool; respect access restrictions.
7. Run `scripts/finish_video.py --input <download> --output <new.mp4> --expected-duration <seconds>`. Requires FFmpeg. Preserve watermarks/metadata. The report proves technical validation, not visual fidelity. Inspect identity and the central action separately.
8. Save video, prompt, task record and verification report in the user's project folder. In hosts supporting local media, render `![video](/absolute/path/video.mp4)` and a download link. Otherwise provide a usable file link; do not claim playback occurred.

When extending this skill, document provider/UI version, observed behavior and tests. No background self-learning. Do not publish task records, signed URLs or user assets with the skill.
