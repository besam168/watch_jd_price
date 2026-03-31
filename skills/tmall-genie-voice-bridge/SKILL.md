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
- 支持通过 `/callback/text` / `/webhook/text` 接收上游 webhook / 技能文本回调并转成播报

当前**不承诺**：

- 直接接管天猫精灵麦克风原始音频流
- 完整打通阿里官方技能
- 纯天猫精灵本地局域网双工对话

## 目录

- `config.example.json`：示例配置
- `scripts/bridge_server.py`：本地 HTTP bridge server
- `scripts/speak.py`：文本转语音并调用后端
- `scripts/listen_once.py`：Windows 一次性语音输入 / wav 转写入口
- `demo-wav-roundtrip.ps1`：无麦克风时最快的 wav -> 转写 -> 回灌播报演示入口
- `scripts/check-microphone.ps1`：Windows 录音设备 / 默认输入 / 识别器预检脚本
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

### 4.4) 最快 text -> speak demo

本地直连模式（最快，不依赖 HTTP）：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/tmall-genie-voice-bridge/demo-text-roundtrip.ps1 -Text "收到，大老板" -Mode local
```

桥接模式（要求 bridge server 已启动）：

```powershell
python skills/tmall-genie-voice-bridge/scripts/bridge_server.py --config skills/tmall-genie-voice-bridge/config.local-speaker.json
powershell -NoProfile -ExecutionPolicy Bypass -File skills/tmall-genie-voice-bridge/demo-text-roundtrip.ps1 -Text "收到，大老板" -Mode bridge
```

这个 demo 脚本会：

- `local`：直接调用 `speak-local.ps1`
- `bridge`：向 `POST /speak` 发送 UTF-8 JSON，避开 PowerShell/curl 引号转义坑

### 4.5) 最快 wav -> transcribe -> echo-speak demo

无物理麦克风时，优先直接跑 wav 回路：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/tmall-genie-voice-bridge/demo-wav-roundtrip.ps1
```

指定自己的 wav：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/tmall-genie-voice-bridge/demo-wav-roundtrip.ps1 -Wav skills/tmall-genie-voice-bridge/tmp_audio/listen-once-test.wav
```

这个脚本本质上等价于：

```bash
python skills/tmall-genie-voice-bridge/scripts/listen_once.py --wav skills/tmall-genie-voice-bridge/tmp_audio/listen-once-test.wav --echo-speak --config skills/tmall-genie-voice-bridge/config.local-speaker.json
```

注意：

- 当前无麦克风时，这条是最稳的闭环演示路径。
- `listen-once-test.wav` 在本机可跑通完整链路，但识别文本可能受样本质量影响，不保证每次都识别成预期中文。
- 若只想验证转写，不回灌播报，去掉 `--echo-speak` 即可。

### 4.6) 本机语音输入 MVP（新增）

优先走 Windows 内置 `System.Speech`，不额外依赖云识别服务。

#### 最短 bring-up 路线（以后插上麦再跑）

先做只读预检：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/tmall-genie-voice-bridge/scripts/check-microphone.ps1
```

看三个点：

- `recognizer.available` 是否为 `true`
- `microphone.default_input_accessible` 是否为 `true`
- `devices` 里是否能看到像样的录音端点 / 声卡设备

再做最小麦克风识别：

```bash
python skills/tmall-genie-voice-bridge/scripts/listen_once.py --timeout-seconds 6
```

最后做“听到就说”联调：

```bash
python skills/tmall-genie-voice-bridge/scripts/listen_once.py --timeout-seconds 6 --echo-speak --config skills/tmall-genie-voice-bridge/config.local-speaker.json
```

#### 无麦克风时的替代验证

先用 wav 文件验证识别链路：

```bash
python skills/tmall-genie-voice-bridge/scripts/listen_once.py --wav skills/tmall-genie-voice-bridge/tmp_audio/smoke.wav
```

再用 wav 文件验证“识别后回灌 speak”链路：

```bash
python skills/tmall-genie-voice-bridge/scripts/listen_once.py --wav skills/tmall-genie-voice-bridge/tmp_audio/listen-once-test.wav --echo-speak --config skills/tmall-genie-voice-bridge/config.local-speaker.json
```

返回统一 JSON，核心字段：

- `ok`
- `text`
- `mode`
- `confidence`
- `culture`
- `speak_result`（仅 `--echo-speak` 时出现）

#### 麦克风 bring-up 排障顺序

按这个顺序查，最快：

1. **先跑 `check-microphone.ps1`**
   - 如果 `recognizer.available=false`：本机没有对应语言识别器，先换 `--culture en-US` 试，或安装匹配的 Windows 语音识别语言包。
   - 如果 `default_input_accessible=false`：默认录音设备不存在、被系统禁用、被别的软件占用，或当前机器没插麦。
2. **去 Windows 设置确认默认输入**
   - 系统 -> 声音 -> 输入
   - 把目标麦克风设为默认输入，确认输入电平有波动。
3. **确认麦克风权限**
   - 系统 -> 隐私和安全性 -> 麦克风
   - 打开桌面应用麦克风访问。
4. **只跑 `listen_once.py`，别一上来就 `--echo-speak`**
   - 先拿到 `ok=true` 和 `text`，再叠加播报。
5. **如果默认设备链路不稳，先退回 `--wav`**
   - 这能把问题切分成“识别问题”还是“录音设备问题”。
6. **如果识别成功但没出声**
   - 直接改测 `speak-local.ps1` 或 `scripts/speak.py`，确认是播放后端问题，不是麦克风问题。

常见错误含义：

- `No recognizer installed for culture ...`：系统没装该语言的识别器。
- `SetInputToDefaultAudioDevice` 相关报错：默认录音设备不可用。
- `No speech recognized before timeout.`：有设备，但这次没识别到有效语音，常见于静音、音量太低、离麦太远、环境噪音、说话太晚。

#### 验收口径：mic in -> text -> spoken reply

满足下面 4 条，才算“麦克风已打通”：

1. `check-microphone.ps1` 显示：
   - `recognizer.available=true`
   - `microphone.default_input_accessible=true`
2. `listen_once.py --timeout-seconds 6` 返回：
   - `ok=true`
   - `mode="microphone"`
   - `text` 非空，且和口播内容大致一致
3. `listen_once.py --echo-speak --config skills/tmall-genie-voice-bridge/config.local-speaker.json` 返回：
   - `ok=true`
   - `speak_result.ok=true`
4. 现场主观验收：
   - 人说一句
   - 控制台打印出可接受文本
   - 本机扬声器真实播出回复
   - 不是只生成文件，也不是假成功

### 5) 再跑 bridge server

```bash
python skills/tmall-genie-voice-bridge/scripts/bridge_server.py --config skills/tmall-genie-voice-bridge/config.json
```

### 6) 用 HTTP 触发播报

PowerShell 里优先这样调，少踩引号坑：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File skills/tmall-genie-voice-bridge/demo-text-roundtrip.ps1 -Text "你好，我是沈万三。" -Mode bridge
```

如果一定要直接发 HTTP：

```powershell
$body = @{ text = '你好，我是沈万三。' } | ConvertTo-Json -Compress
Invoke-RestMethod -Uri 'http://127.0.0.1:57881/speak' -Method Post -ContentType 'application/json; charset=utf-8' -Body $body | ConvertTo-Json -Depth 8
```

### 6.5) 用 webhook / 技能文本回调触发播报（新增）

如果上游不是直接传 `{ text }`，而是技能平台 / 自动化平台回调，可直接打：

- `POST /callback/text`
- `POST /webhook/text`

当前接受的常见文本字段：

- `text`
- `query`
- `utterance`
- `message`
- `payload.text`
- `payload.query`
- `intent.query`
- `request.text`
- `request.query`

最小示例：

```powershell
$body = @{ query = '打开客厅灯' ; source = 'tmall-skill-sim' ; session_id = 'demo-001' } | ConvertTo-Json -Compress
Invoke-RestMethod -Uri 'http://127.0.0.1:57881/callback/text' -Method Post -ContentType 'application/json; charset=utf-8' -Body $body | ConvertTo-Json -Depth 10
```

注意：

- 这条路线本质是**文本回调桥接**，不是原始麦克风 / PCM 音频桥接。
- 适合先做“天猫精灵技能 / 云函数 / Home Assistant 自动化 -> 文本 -> 本地播报”闭环。
- 返回里会保留 `callback` 元数据和 `recognized_text`，便于以后接真实上游。

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

关键注意：

- 如果目标是真实天猫精灵/局域网设备，`media_content_id` 里的音频 URL 不能是 `127.0.0.1`。那只对 bridge 所在机器自己可见，对外部设备不可见。
- 当前支持两种更稳的写法：
  - `audio_base_url: "auto"`：bridge 会按当前请求的 `scheme://host[:port]/audio` 自动生成音频 URL。
  - `public_base_url: "http://你的可达地址:57881"`：bridge 会固定生成 `http://你的可达地址:57881/audio/...`，这对 Home Assistant 反代/NAT/固定域名场景更稳。
- 真实设备要能播，前提不是“生成了音频文件”，而是“设备能主动访问到这个音频 URL”。

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
