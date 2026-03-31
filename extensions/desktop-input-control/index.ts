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

function maybeArg(flag: string, value: unknown): string[] {
  if (value === undefined || value === null || value === "") {
    return [];
  }
  return [flag, String(value)];
}

async function runOcr(ocrScriptPath: string, params: {
  imagePath: string;
  lang?: string;
  preprocess?: string;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
  query?: string;
  queryMode?: string;
}) {
  const args = [
    ocrScriptPath,
    params.imagePath,
    params.lang || "chi_sim+eng",
    ...maybeArg("--preprocess", params.preprocess || "gray_upscale2x"),
    ...maybeArg("--x", params.x),
    ...maybeArg("--y", params.y),
    ...maybeArg("--width", params.width),
    ...maybeArg("--height", params.height),
    ...maybeArg("--query", params.query),
    ...maybeArg("--query-mode", params.queryMode || "contains"),
  ];
  const result = await execFileAsync("python", args, {
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    maxBuffer: 1024 * 1024 * 16,
  });
  const text = (result.stdout || "").trim() || (result.stderr || "").trim() || "{}";
  return JSON.parse(text);
}

function buildCaptureArgs(params: {
  path?: string;
  virtualScreen?: boolean;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
}) {
  const args: string[] = [params.path || ""];
  if (params.virtualScreen) {
    args.push("-VirtualScreen");
  }
  args.push(...maybeArg("-X", params.x));
  args.push(...maybeArg("-Y", params.y));
  args.push(...maybeArg("-Width", params.width));
  args.push(...maybeArg("-Height", params.height));
  return args;
}

function pickBestMatch(ocrResult: any) {
  const items = Array.isArray(ocrResult?.items) ? ocrResult.items : [];
  if (items.length === 0) {
    return null;
  }
  return [...items].sort((a, b) => {
    const confA = typeof a?.confidence === "number" ? a.confidence : -1;
    const confB = typeof b?.confidence === "number" ? b.confidence : -1;
    return confB - confA;
  })[0];
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
    description: "Capture the current screen to a PNG file, with optional virtual-screen and region support.",
    parameters: Type.Object({
      path: Type.Optional(Type.String()),
      virtualScreen: Type.Optional(Type.Boolean()),
      x: Type.Optional(Type.Number()),
      y: Type.Optional(Type.Number()),
      width: Type.Optional(Type.Number()),
      height: Type.Optional(Type.Number()),
    }),
    async execute(_id, params) {
      const result = await execFileAsync("powershell", [
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        captureScriptPath,
        ...buildCaptureArgs(params),
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
      preprocess: Type.Optional(Type.Union([
        Type.Literal("raw"),
        Type.Literal("gray"),
        Type.Literal("binary"),
        Type.Literal("upscale2x"),
        Type.Literal("gray_upscale2x"),
        Type.Literal("high_contrast"),
      ])),
      x: Type.Optional(Type.Number()),
      y: Type.Optional(Type.Number()),
      width: Type.Optional(Type.Number()),
      height: Type.Optional(Type.Number()),
      query: Type.Optional(Type.String()),
      queryMode: Type.Optional(Type.Union([Type.Literal("contains"), Type.Literal("exact")]))
    }),
    async execute(_id, params) {
      const ocr = await runOcr(ocrScriptPath, params);
      return { content: [{ type: "text", text: JSON.stringify(ocr) }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_find_text_on_screen",
    description: "Capture the screen, run OCR, and return the best matching text item with click coordinates.",
    parameters: Type.Object({
      query: Type.String(),
      queryMode: Type.Optional(Type.Union([Type.Literal("contains"), Type.Literal("exact")], { default: "contains" })),
      lang: Type.Optional(Type.String()),
      preprocess: Type.Optional(Type.Union([
        Type.Literal("raw"),
        Type.Literal("gray"),
        Type.Literal("binary"),
        Type.Literal("upscale2x"),
        Type.Literal("gray_upscale2x"),
        Type.Literal("high_contrast"),
      ])),
      virtualScreen: Type.Optional(Type.Boolean()),
      x: Type.Optional(Type.Number()),
      y: Type.Optional(Type.Number()),
      width: Type.Optional(Type.Number()),
      height: Type.Optional(Type.Number()),
      path: Type.Optional(Type.String()),
    }),
    async execute(_id, params) {
      const captureResult = await execFileAsync("powershell", [
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        captureScriptPath,
        ...buildCaptureArgs(params),
      ]);
      const imagePath = (captureResult.stdout || "").trim() || (captureResult.stderr || "").trim();
      const ocr = await runOcr(ocrScriptPath, {
        imagePath,
        lang: params.lang,
        preprocess: params.preprocess,
        query: params.query,
        queryMode: params.queryMode,
      });
      const match = pickBestMatch(ocr);
      const result = {
        ok: Boolean(match),
        query: params.query,
        queryMode: params.queryMode || "contains",
        imagePath,
        match,
        count: ocr?.count || 0,
        items: ocr?.items || [],
        ocr,
      };
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_click_text_on_screen",
    description: "Find matching text on screen using OCR and click its center point.",
    parameters: Type.Object({
      query: Type.String(),
      queryMode: Type.Optional(Type.Union([Type.Literal("contains"), Type.Literal("exact")], { default: "contains" })),
      lang: Type.Optional(Type.String()),
      preprocess: Type.Optional(Type.Union([
        Type.Literal("raw"),
        Type.Literal("gray"),
        Type.Literal("binary"),
        Type.Literal("upscale2x"),
        Type.Literal("gray_upscale2x"),
        Type.Literal("high_contrast"),
      ])),
      virtualScreen: Type.Optional(Type.Boolean()),
      x: Type.Optional(Type.Number()),
      y: Type.Optional(Type.Number()),
      width: Type.Optional(Type.Number()),
      height: Type.Optional(Type.Number()),
      button: Type.Optional(Type.Union([Type.Literal("left"), Type.Literal("right"), Type.Literal("double")], { default: "left" })),
      path: Type.Optional(Type.String()),
    }),
    async execute(_id, params) {
      const captureResult = await execFileAsync("powershell", [
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        captureScriptPath,
        ...buildCaptureArgs(params),
      ]);
      const imagePath = (captureResult.stdout || "").trim() || (captureResult.stderr || "").trim();
      const ocr = await runOcr(ocrScriptPath, {
        imagePath,
        lang: params.lang,
        preprocess: params.preprocess,
        query: params.query,
        queryMode: params.queryMode,
      });
      const match = pickBestMatch(ocr);
      if (!match) {
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              ok: false,
              query: params.query,
              queryMode: params.queryMode || "contains",
              imagePath,
              error: "text not found",
              count: ocr?.count || 0,
              items: ocr?.items || [],
              ocr,
            }),
          }],
        };
      }

      const clickX = Math.round(match.centerX);
      const clickY = Math.round(match.centerY);
      await runPs(scriptPath, ["mouse-move", String(clickX), String(clickY)]);
      const clickText = await runPs(scriptPath, ["mouse-click", params.button || "left"]);
      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            ok: true,
            query: params.query,
            queryMode: params.queryMode || "contains",
            imagePath,
            click: {
              x: clickX,
              y: clickY,
              button: params.button || "left",
              result: clickText,
            },
            match,
            count: ocr?.count || 0,
            items: ocr?.items || [],
            ocr,
          }),
        }],
      };
    },
  }, { optional: true });
}
