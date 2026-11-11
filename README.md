# video-agent-kit

**从想法与参考图，到可恢复、可验证的视频交付。**  
Agent skills and local utilities for prompt planning, Kling production guidance, task recovery and verified MP4 delivery.

v0.1.0 · MIT · Python 3.9+ · FFmpeg required for media validation

## 能做什么

- 提示词导演 Skill：角色/场景约束、动作顺序、运镜、参考用途与验收点。
- 可灵 Skill：指导 Agent 上传、生成、跟进同一任务、下载与交付。
- 本地任务日志：记录提交前后状态；提交结果不确定时先核实，下载失败时继续已有任务。
- MP4 校验：容器完整性、FFmpeg 完整解码、时长容差、SHA256、禁止覆盖已有成片。

**这是 Agent 技能与本地工具包。** CLI 不直接调用可灵，不自带视频模型、账号或积分。需要支持技能及相应工具的 Agent；生成仍取决于平台能力、登录状态和用户授权。技术校验不等于人物/动作质量达标。

## 安装两个 Skill

克隆仓库后，将 `skills/ai-video-prompt-director` 和 `skills/kling-video-producer` 两个目录并列复制到 Codex 的用户 skills 目录（通常为 `~/.codex/skills/`）。若同名目录已存在，先备份并比较，不覆盖本地修改。重新开启会话以刷新技能列表。

示例请求：
> 用我的参考图做一个 5 秒视频，让纸船从画面左侧漂到中央。生成一条，保存到我指定的目录，并在对话里展示。

只讨论或只写提示词不会进入生成。可灵优先使用环境中可用的官方集成，网站操作作为补充。见 [适配范围与官方指南](skills/kling-video-producer/references/providers.md)。官方 MCP/CLI 适配尚未实测。

## 本地快速体验（不消耗生成积分）

安装 Python 3.9+ 和 FFmpeg，把 ffmpeg 加入 PATH，然后在仓库根目录执行：

```sh
python3 scripts/task.py init runs/boat-task.json --brief examples/brief.json
python3 scripts/task.py resume runs/boat-task.json
python3 scripts/make_demo.py --output runs/demo.mp4
python3 skills/kling-video-producer/scripts/finish_video.py --input runs/demo.mp4 --output runs/verified.mp4 --expected-duration 1
python3 -m unittest discover -s tests -v
```

示例 MP4 由本机 FFmpeg 生成纯色画面，仅用于验证文件流程，不是 AI 生成效果。`examples/brief.json` 的参考路径是待替换字段；它不附带图片，不授权真实提交。

输出：新 MP4 与同名 `.verification.json`。重复输出会拒绝；换版本文件名即可。可通过 `--ffmpeg /path/to/ffmpeg` 指定程序。完整解码最多等待 300 秒；默认时长容差 0.25 秒。工具只接受以 ftyp 开头、含 moov/mdat 的普通 MP4；不是所有媒体容器的通用验证器。

## 恢复和交付

[任务协议](docs/task-protocol.md) 说明状态迁移、并发锁和人工核实边界。日志不会自行提交视频，也不能保证远端只执行一次。下载错误只恢复下载；不要重新花积分生成。

支持本地媒体的宿主可用 `![video](/absolute/path/video.mp4)` 显示成片；其他宿主提供文件链接。保存原始水印与来源信息。用户素材、任务链接、临时签名地址留在本地，仓库只包含工具和通用示例。

## 已验证与未验证

- 私有案例跑通过官网上传 → 生成 → 下载 → 本地解码；案例素材和账号数据不发布。
- 公开版自动测试使用本地合成素材，覆盖错误网页、截断容器、时长不符、输出保护和任务恢复。
- 未实测官方 MCP/CLI 生成、多账号兼容和所有宿主内嵌播放。不会保证逐帧复刻。
- 小红书下载器、MV 分镜工具和其他视频平台暂不包含在 v0.1。

## Contributing

欢迎提交有复现步骤的 bug、脱敏日志、平台适配或提示词实验。注明平台/模型/日期，区分实际生成测试与文字推演；不要提交账号、签名 URL 或无权分发的素材。改动后运行测试。新增平台应分离提交、查询、下载步骤，并测试“提交超时但远端已成功”的恢复路径。

English: install both skill directories side by side in your agent's skill directory. The Python utilities are local-only and dependency-free except FFmpeg for video validation. Provider integrations are operated by the host agent and require the user's own account and authorization. See the task protocol for recovery semantics.
