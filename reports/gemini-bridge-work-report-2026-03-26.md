# gemini-bridge 工作报告 - 2026-03-26

## 1. 工作目标
本次目标是为当前 OpenClaw 工作区补一个本地可调用的 Gemini 桥接能力，不再卡死在 VS Code / Cline 图形界面里，而是先把 `OpenClaw -> Gemini API` 这条链路真实打通。

## 2. 本次完成内容
已新建技能目录：
- `C:\Users\besam\.openclaw\workspace\skills\gemini-bridge\`

已完成文件：
- `C:\Users\besam\.openclaw\workspace\skills\gemini-bridge\SKILL.md`
- `C:\Users\besam\.openclaw\workspace\skills\gemini-bridge\scripts\run-gemini.ps1`

`run-gemini.ps1` 已支持：
- `Prompt`
- `ApiKey`
- `Model`
- `BaseUrl`
- `OutputFile`
- `Json`
- `OpenAICompat`

## 3. 实测过程与结果
### 3.1 原始目标模型测试
测试模型：`gemini-3.1-pro-preview`

结果：
- 原生接口：`429 Too Many Requests`
- OpenAI 兼容接口：`429 Too Many Requests`

判断：
- 请求已成功打到 Google Gemini
- Key / Base URL / 请求结构基本没问题
- 问题更像是该预览模型的限流 / 配额 / 当前调用限制

### 3.2 降级模型排查
测试模型：`gemini-1.5-flash`

结果：
- 返回 `404 Not Found`

后续通过真实 `models.list` 查询确认：
- 当前账号可见模型列表中没有 `models/gemini-1.5-flash`

所以这个 404 不是桥接挂了，而是模型名不在当前账号的可见列表里。

### 3.3 真实模型列表核验
通过：
- `GET https://generativelanguage.googleapis.com/v1beta/models`

实测确认当前账号可见的关键模型包括：
- `models/gemini-2.5-flash`
- `models/gemini-2.5-pro`
- `models/gemini-3.1-pro-preview`
- `models/gemini-3.1-flash-lite-preview`

### 3.4 成功打通测试
实测命令：
```powershell
powershell -ExecutionPolicy Bypass -File "C:\Users\besam\.openclaw\workspace\skills\gemini-bridge\scripts\run-gemini.ps1" -Prompt "Reply with exactly GEMINI_25_FLASH_OK" -Model "gemini-2.5-flash" -Json
```

实测返回：
```json
{
  "ok": true,
  "model": "gemini-2.5-flash",
  "baseUrl": "https://generativelanguage.googleapis.com/v1beta",
  "openAICompat": false,
  "outputFile": "",
  "text": "GEMINI_25_FLASH_OK"
}
```

## 4. 当前结论
### 已确认打通
- `gemini-bridge` 已做成
- 原生 Gemini API 已真实可用
- 当前稳定可用模型：`gemini-2.5-flash`

### 未完全打通的部分
- `gemini-3.1-pro-preview` 当前仍返回 `429`
- 这更像预览模型限流 / 配额问题，不是桥接脚本故障

## 5. 已做的收尾调整
已将桥接脚本默认模型改为：
- `gemini-2.5-flash`

这样后续默认调用时，会优先走已经实测成功的稳定模型。

## 6. 当前交付状态
当前 `gemini-bridge` 已达到：
- 可调用
- 可复用
- 已实测
- 可继续作为 Claude 指挥 Gemini 的下层基础

## 7. 后续建议
后续优先级建议：
1. 给 `run-gemini.ps1` 增加更清楚的 HTTP 错误分类（429 / 401 / 403 / 404）
2. 补一个更高层的任务脚本，例如：
   - 代码分析
   - 文件草拟
   - 项目总结
3. 如果后面还要接 VS Code / Cline，再决定是否把这条桥接能力接回 GUI 工具链

## 8. 一句话总结
这次不是把所有 Gemini 模型都打通了，而是已经把 **本地 Gemini 桥接能力真实做出来并跑通了 `gemini-2.5-flash`**。