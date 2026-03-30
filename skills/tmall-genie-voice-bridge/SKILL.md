---
name: tmall-genie-voice-bridge
description: 让 OpenClaw 通过“天猫精灵语音桥”方式接入家庭语音场景。适用于：需要为天猫精灵/家庭音箱搭建第一版语音桥、本地 bridge server、TTS 播报后端、以及未来接入云技能或自动化平台时。该 skill 重点是搭好桥接骨架、配置结构、播放适配层和本地可运行 MVP，不承诺直接接管天猫精灵麦克风原始音频流。
---

# tmall-genie-voice-bridge

这是一个**第一版骨架 skill**。

目标不是一上来就“完全接管天猫精灵”，而是先把下面四件事搭对：

1. 文本入口
2. TTS 生成音频
3. 播放后端适配层
4. 本地 HTTP bridge server

## 适用场景

当用户要做这些事时使用本 skill：

- 想让 OpenClaw 以后能通过天猫精灵说话
- 想先做一个家庭语音桥 MVP
- 想把天猫精灵当作语音前端/播报出口
- 想为未来接入阿里技能、Home Assistant、巴法云、Webhook、中控服务预留接口

## 当前边界

当前版本：

- 支持本地 bridge server
- 支持文本 -> TTS 文件
- 支持可插拔播放后端
- 支持 mock 后端与通用 HTTP 播放后端
- 支持通过 HTTP `/speak` 接口触发播报

当前**不承诺**：

- 直接接管天猫精灵麦克风原始音频流
- 完整打通阿里官方技能
- 纯天猫精灵本地局域网双工对话

## 目录

- `config.example.json`：示例配置
- `scripts/bridge_server.py`：本地 HTTP bridge server
- `scripts/speak.py`：文本转语音并调用后端
- `scripts/listen_once.py`：Windows 一次性语音输入 / wav 转写入口
- `scripts/providers/tts_edge.py`：Edge TTS provider
- `scripts/backends/base.py`：后端基类
- `scripts/backends/mock_tmall_genie.py`：模拟后端
- `scripts/backends/local_http_player.py`：通用 HTTP 播放后端
- `.gitignore`：忽略本地配置、缓存和测试音频

## 快速上手

### 1) 复制配置

把：

- `config.example.json`

复制成：

- `config.json`

按实际环境填写。

### 2) 安装依赖

建议 Python 3.10+。

需要的第三方依赖：

- `flask`
- `requests`
- `edge-tts`

安装命令：

```bash
pip install flask requests edge-tts
```

### 3) 先直接测 speak.py

```bash
python skills/tmall-genie-voice-bridge/scripts/speak.py "你好，我是沈万三。" --config skills/tmall-genie-voice-bridge/config.json
```

如果当前后端还是 `mock_tmall_genie`，预期结果是：

- 生成一个 mp3 文件
- 返回 JSON 结果
- `backend_result.note` 明确说明这是模拟播放，不是真正下发到天猫精灵

### 4) Windows 本地播报入口（新增）

在 Windows 上可直接调用根目录入口：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/tmall-genie-voice-bridge/speak-local.ps1 -Text "你好，我是本地播报"
```

或：

```bat
skills\tmall-genie-voice-bridge\speak-local.bat "你好，我是本地播报"
```

说明：

- 不传 `-Config` 时优先读取 `config.local-speaker.json`，否则回落到 `config.json`
- 也可通过环境变量 `TMALL_GENIE_VOICE_BRIDGE_CONFIG` 指定配置路径
- 脚本已显式设置 UTF-8 控制台/Python 编码，减少中文参数和 JSON 输出乱码

### 4.4) 最小 demo：text in -> spoken reply out

本地直连模式（不依赖 HTTP）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/tmall-genie-voice-bridge/demo-text-roundtrip.ps1 -Text "收到，大老板" -Mode local
```

桥接模式（要求 bridge server 已启动）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/tmall-genie-voice-bridge/demo-text-roundtrip.ps1 -Text "收到，大老板" -Mode bridge
```

这个 demo 脚本会：

- `local`：直接调用 `speak-local.ps1`
- `bridge`：向 `POST /speak` 发送 UTF-8 JSON，避开 PowerShell/curl 引号转义坑

### 4.5) 本机语音输入 MVP（新增）

优先走 Windows 内置 `System.Speech`，不额外依赖云识别服务。

直接听一次麦克风：

```bash
python skills/tmall-genie-voice-bridge/scripts/listen_once.py --timeout-seconds 6
```

转写已有 wav 文件：

```bash
python skills/tmall-genie-voice-bridge/scripts/listen_once.py --wav skills/tmall-genie-voice-bridge/tmp_audio/smoke.wav
```

识别成功后直接回灌现有 speak 流：

```bash
python skills/tmall-genie-voice-bridge/scripts/listen_once.py --timeout-seconds 6 --echo-speak --config skills/tmall-genie-voice-bridge/config.local-speaker.json
```

返回统一 JSON，核心字段：

- `ok`
- `text`
- `mode`
- `confidence`
- `culture`
- `speak_result`（仅 `--echo-speak` 时出现）

注意：

- 当前入口优先保证 **Windows 本机一次性输入 demo**，不是持续流式识别。
- 若麦克风权限、设备占用、默认录音设备缺失或现场噪音导致识别不稳，先用 `--wav` 跑文件转写，最快拿到演示结果。
- 如果 `SetInputToDefaultAudioDevice` 报错，下一条命令直接这样跑：

```bash
python skills/tmall-genie-voice-bridge/scripts/listen_once.py --wav skills/tmall-genie-voice-bridge/tmp_audio/listen-once-test.wav --echo-speak --config skills/tmall-genie-voice-bridge/config.local-speaker.json
```

### 5) 再跑 bridge server

```bash
python skills/tmall-genie-voice-bridge/scripts/bridge_server.py --config skills/tmall-genie-voice-bridge/config.json
```

### 6) 用 HTTP 触发播报

```bash
curl -X POST http://127.0.0.1:57881/speak \
  -H "Content-Type: application/json" \
  -d '{"text":"你好，我是沈万三。"}'
```

## 推荐工作流

### 1) 先跑 mock 模式

先确认：

- 配置能读
- TTS 能生成文件
- JSON 返回正常
- bridge server 能接收 `/speak`

### 2) 再切换真实后端

把 `backend.type` 从：

- `mock_tmall_genie`

改成：

- `local_http_player`

并填写：

- `player_url`
- `audio_base_url`
- 鉴权参数（如有）

## 配置说明

### tts

- `provider`: 当前默认 `edge`
- `voice`: 例如 `zh-CN-XiaoxiaoNeural`
- `rate`: 例如 `+0%`
- `output_dir`: 音频输出目录

### backend

#### `mock_tmall_genie`
只打印和记录，不真的播。
适合先验链路。

#### `local_http_player`
把文本对应的音频 URL 发给一个外部 HTTP 播放端。
适合未来对接：

- Home Assistant
- 自建播放网关
- 局域网中控服务
- 云技能回调服务

## 什么时候读其它文件

- 要看接口：读 `scripts/bridge_server.py`
- 要看 TTS：读 `scripts/providers/tts_edge.py`
- 要看后端：读 `scripts/backends/*.py`
- 要改配置：读 `config.example.json`

## 下一步怎么扩展

后续如果要真接天猫精灵，优先走下面路线之一：

1. 天猫精灵技能 / 云桥接入口 -> 调本地或云端 bridge server
2. Home Assistant / 巴法云 / 语音网关中转
3. 独立网页语音入口 + 天猫精灵作为播报端

不要先把希望押在“直接本地接管天猫精灵麦克风”上。
