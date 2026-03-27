import { Type } from "@sinclair/typebox";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

async function runPs(scriptPath: string, args: string[]) {
  const result = await execFileAsync("powershell", [
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    scriptPath,
    ...args,
  ]);
  return (result.stdout || "").trim() || (result.stderr || "").trim() || "OK";
}

export default function (api) {
  const scriptPath = path.join(__dirname, "scripts", "desktop-input.ps1");
  const captureScriptPath = path.join(__dirname, "scripts", "screen-capture-compat.ps1");
  const ocrScriptPath = path.join(__dirname, "scripts", "screen-ocr.py");

  api.registerTool({
    name: "desktop_mouse_move",
    description: "Move the Windows mouse pointer to an absolute screen position.",
    parameters: Type.Object({ x: Type.Number(), y: Type.Number() }),
    async execute(_id, params) {
      const text = await runPs(scriptPath, ["mouse-move", String(params.x), String(params.y)]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_mouse_click",
    description: "Click the Windows mouse. Supports left, right, and double click.",
    parameters: Type.Object({
      button: Type.Optional(Type.Union([Type.Literal("left"), Type.Literal("right"), Type.Literal("double")], { default: "left" })),
    }),
    async execute(_id, params) {
      const button = params.button || "left";
      const text = await runPs(scriptPath, ["mouse-click", button]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_mouse_drag",
    description: "Drag the mouse from one absolute screen position to another.",
    parameters: Type.Object({ fromX: Type.Number(), fromY: Type.Number(), toX: Type.Number(), toY: Type.Number() }),
    async execute(_id, params) {
      const text = await runPs(scriptPath, ["mouse-drag", String(params.fromX), String(params.fromY), String(params.toX), String(params.toY)]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_mouse_scroll",
    description: "Scroll the mouse wheel. Positive values usually scroll up; negative values scroll down.",
    parameters: Type.Object({ delta: Type.Number() }),
    async execute(_id, params) {
      const text = await runPs(scriptPath, ["mouse-scroll", String(params.delta)]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_type_text",
    description: "Type text into the active Windows input focus using SendKeys.",
    parameters: Type.Object({ text: Type.String() }),
    async execute(_id, params) {
      const text = await runPs(scriptPath, ["type-text", params.text]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_press_hotkey",
    description: "Press a Windows hotkey combination such as ctrl+s, alt+tab, win+r, or enter.",
    parameters: Type.Object({ keys: Type.String() }),
    async execute(_id, params) {
      const text = await runPs(scriptPath, ["press-hotkey", params.keys]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_open_app",
    description: "Open a Windows app, executable, or shell target.",
    parameters: Type.Object({ target: Type.String() }),
    async execute(_id, params) {
      const text = await runPs(scriptPath, ["open-app", params.target]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_open_url",
    description: "Open a URL in the default browser.",
    parameters: Type.Object({ url: Type.String() }),
    async execute(_id, params) {
      const text = await runPs(scriptPath, ["open-url", params.url]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_run_command",
    description: "Run a Windows shell command via cmd.exe /c.",
    parameters: Type.Object({ command: Type.String() }),
    async execute(_id, params) {
      const text = await runPs(scriptPath, ["run-command", params.command]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_focus_window",
    description: "Bring a window to the foreground by title match using AppActivate.",
    parameters: Type.Object({ title: Type.String() }),
    async execute(_id, params) {
      const text = await runPs(scriptPath, ["focus-window", params.title]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_screen_capture",
    description: "Capture the current primary screen to a PNG file and return the saved image path.",
    parameters: Type.Object({
      path: Type.Optional(Type.String()),
    }),
    async execute(_id, params) {
      const outputPath = params.path || "";
      const result = await execFileAsync("powershell", [
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        captureScriptPath,
        outputPath,
      ]);
      const text = (result.stdout || "").trim() || (result.stderr || "").trim() || "OK";
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_screen_ocr",
    description: "Run OCR on a screen image and return recognized text with bounding boxes as JSON.",
    parameters: Type.Object({
      imagePath: Type.String(),
      lang: Type.Optional(Type.String()),
    }),
    async execute(_id, params) {
      const lang = params.lang || "eng";
      const result = await execFileAsync("python", [ocrScriptPath, params.imagePath, lang], {
        env: { ...process.env, PYTHONIOENCODING: "utf-8" },
      });
      const text = (result.stdout || "").trim() || (result.stderr || "").trim() || "OK";
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });
}
