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

### 4) 再跑 bridge server

```bash
python skills/tmall-genie-voice-bridge/scripts/bridge_server.py --config skills/tmall-genie-voice-bridge/config.json
```

### 5) 用 HTTP 触发播报

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
