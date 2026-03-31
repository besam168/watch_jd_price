import { Type } from "@sinclair/typebox";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const preprocessSchema = Type.Union([
  Type.Literal("raw"),
  Type.Literal("gray"),
  Type.Literal("binary"),
  Type.Literal("upscale2x"),
  Type.Literal("gray_upscale2x"),
  Type.Literal("high_contrast"),
]);
const queryModeSchema = Type.Union([Type.Literal("contains"), Type.Literal("exact")]);
const groupBySchema = Type.Union([
  Type.Literal("auto"),
  Type.Literal("word"),
  Type.Literal("line"),
  Type.Literal("phrase"),
]);

async function runPy(scriptPath: string, args: string[]) {
  const result = await execFileAsync("python", [scriptPath, ...args], {
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    maxBuffer: 1024 * 1024 * 16,
  });
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
  groupBy?: string;
  topN?: number;
  debugOverlay?: string;
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
    ...maybeArg("--group-by", params.groupBy || "auto"),
    ...maybeArg("--top-n", params.topN ?? 1),
    ...maybeArg("--debug-overlay", params.debugOverlay),
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

function sortItemsByConfidence(items: any[]) {
  return [...items].sort((a, b) => {
    const confA = typeof a?.confidence === "number" ? a.confidence : -1;
    const confB = typeof b?.confidence === "number" ? b.confidence : -1;
    return confB - confA;
  });
}

function pickTopMatches(ocrResult: any, topN = 1) {
  const items = Array.isArray(ocrResult?.matches) && ocrResult.matches.length > 0
    ? ocrResult.matches
    : (Array.isArray(ocrResult?.items) ? ocrResult.items : []);
  return sortItemsByConfidence(items).slice(0, Math.max(1, topN));
}

function pickBestMatch(ocrResult: any) {
  return pickTopMatches(ocrResult, 1)[0] || null;
}

function baseFindTextParams() {
  return {
    query: Type.String(),
    queryMode: Type.Optional(Type.Union([Type.Literal("contains"), Type.Literal("exact")], { default: "contains" })),
    lang: Type.Optional(Type.String()),
    preprocess: Type.Optional(preprocessSchema),
    groupBy: Type.Optional(groupBySchema),
    topN: Type.Optional(Type.Number()),
    debugOverlayPath: Type.Optional(Type.String()),
    virtualScreen: Type.Optional(Type.Boolean()),
    x: Type.Optional(Type.Number()),
    y: Type.Optional(Type.Number()),
    width: Type.Optional(Type.Number()),
    height: Type.Optional(Type.Number()),
    path: Type.Optional(Type.String()),
  };
}

async function captureScreen(captureScriptPath: string, params: {
  path?: string;
  virtualScreen?: boolean;
  x?: number;
  y?: number;
  width?: number;
  height?: number;
}) {
  const result = await execFileAsync("powershell", [
    "-ExecutionPolicy",
    "Bypass",
    "-File",
    captureScriptPath,
    ...buildCaptureArgs(params),
  ]);
  return (result.stdout || "").trim() || (result.stderr || "").trim();
}

export default function (api) {
  const scriptPath = path.join(__dirname, "scripts", "desktop-input.py");
  const captureScriptPath = path.join(__dirname, "scripts", "screen-capture-compat.ps1");
  const ocrScriptPath = path.join(__dirname, "scripts", "screen-ocr.py");

  api.registerTool({
    name: "desktop_mouse_move",
    description: "Move the Windows mouse pointer to an absolute screen position.",
    parameters: Type.Object({ x: Type.Number(), y: Type.Number() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["mouse-move", String(params.x), String(params.y)]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_mouse_move_relative",
    description: "Move the Windows mouse pointer relative to its current position.",
    parameters: Type.Object({ dx: Type.Number(), dy: Type.Number() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["mouse-move-relative", String(params.dx), String(params.dy)]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_mouse_click",
    description: "Click the Windows mouse. Supports left, right, and double click.",
    parameters: Type.Object({
      button: Type.Optional(Type.Union([Type.Literal("left"), Type.Literal("right"), Type.Literal("middle"), Type.Literal("double")], { default: "left" })),
    }),
    async execute(_id, params) {
      const button = params.button || "left";
      const text = await runPy(scriptPath, ["mouse-click", button]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_mouse_drag",
    description: "Drag the mouse from one absolute screen position to another.",
    parameters: Type.Object({ fromX: Type.Number(), fromY: Type.Number(), toX: Type.Number(), toY: Type.Number() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["mouse-drag", String(params.fromX), String(params.fromY), String(params.toX), String(params.toY)]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_mouse_scroll",
    description: "Scroll the mouse wheel. Positive values usually scroll up; negative values scroll down.",
    parameters: Type.Object({ delta: Type.Number() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["mouse-scroll", String(params.delta)]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_type_text",
    description: "Type text into the active Windows input focus using SendKeys.",
    parameters: Type.Object({ text: Type.String() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["type-text", params.text]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_press_hotkey",
    description: "Press a Windows hotkey combination such as ctrl+s, alt+tab, win+r, or enter.",
    parameters: Type.Object({ keys: Type.String() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["press-hotkey", params.keys]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_open_app",
    description: "Open a Windows app, executable, or shell target.",
    parameters: Type.Object({ target: Type.String() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["open-app", params.target]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_open_url",
    description: "Open a URL in the default browser.",
    parameters: Type.Object({ url: Type.String() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["open-url", params.url]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_run_command",
    description: "Run a Windows shell command via cmd.exe /c.",
    parameters: Type.Object({ command: Type.String() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["run-command", params.command]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_focus_window",
    description: "Bring a window to the foreground by title match using AppActivate.",
    parameters: Type.Object({ title: Type.String() }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["focus-window", params.title]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_get_foreground_window",
    description: "Get the current foreground window title.",
    parameters: Type.Object({}),
    async execute() {
      const text = await runPy(scriptPath, ["get-foreground-window"]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_get_recent_actions",
    description: "Read recent desktop action logs for observability and debugging.",
    parameters: Type.Object({ limit: Type.Optional(Type.Number()) }),
    async execute(_id, params) {
      const text = await runPy(scriptPath, ["get-recent-actions", String(params.limit ?? 20)]);
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
      const text = await captureScreen(captureScriptPath, params) || "OK";
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_screen_ocr",
    description: "Run OCR on a screen image and return recognized text with bounding boxes as JSON.",
    parameters: Type.Object({
      imagePath: Type.String(),
      lang: Type.Optional(Type.String()),
      preprocess: Type.Optional(preprocessSchema),
      x: Type.Optional(Type.Number()),
      y: Type.Optional(Type.Number()),
      width: Type.Optional(Type.Number()),
      height: Type.Optional(Type.Number()),
      query: Type.Optional(Type.String()),
      queryMode: Type.Optional(queryModeSchema),
      groupBy: Type.Optional(groupBySchema),
      topN: Type.Optional(Type.Number()),
      debugOverlayPath: Type.Optional(Type.String()),
    }),
    async execute(_id, params) {
      const ocr = await runOcr(ocrScriptPath, {
        ...params,
        debugOverlay: params.debugOverlayPath,
      });
      return { content: [{ type: "text", text: JSON.stringify(ocr) }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_find_text_on_screen",
    description: "Capture the screen, run OCR, and return the best match plus optional top-N matches and engine info.",
    parameters: Type.Object(baseFindTextParams()),
    async execute(_id, params) {
      const imagePath = await captureScreen(captureScriptPath, params);
      const ocr = await runOcr(ocrScriptPath, {
        imagePath,
        lang: params.lang,
        preprocess: params.preprocess,
        query: params.query,
        queryMode: params.queryMode,
        groupBy: params.groupBy,
        topN: params.topN,
        debugOverlay: params.debugOverlayPath,
      });
      const matches = pickTopMatches(ocr, params.topN ?? 1);
      const match = matches[0] || null;
      const result = {
        ok: Boolean(match),
        query: params.query,
        queryMode: params.queryMode || "contains",
        imagePath,
        match,
        matches,
        topN: params.topN ?? 1,
        count: ocr?.count || 0,
        items: ocr?.items || [],
        debugOverlay: ocr?.debugOverlay || null,
        engine: ocr?.engine || null,
        ocr,
      };
      return { content: [{ type: "text", text: JSON.stringify(result) }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_click_text_on_screen",
    description: "Find matching text on screen using OCR and click its center point. Supports dry-run mode and optional post-click verification.",
    parameters: Type.Object({
      ...baseFindTextParams(),
      button: Type.Optional(Type.Union([Type.Literal("left"), Type.Literal("right"), Type.Literal("middle"), Type.Literal("double")], { default: "left" })),
      dryRun: Type.Optional(Type.Boolean()),
      verifyQuery: Type.Optional(Type.String()),
      verifyAbsentQuery: Type.Optional(Type.String()),
      verifyDelayMs: Type.Optional(Type.Number()),
    }),
    async execute(_id, params) {
      const imagePath = await captureScreen(captureScriptPath, params);
      const ocr = await runOcr(ocrScriptPath, {
        imagePath,
        lang: params.lang,
        preprocess: params.preprocess,
        query: params.query,
        queryMode: params.queryMode,
        groupBy: params.groupBy,
        topN: params.topN,
        debugOverlay: params.debugOverlayPath,
      });
      const matches = pickTopMatches(ocr, params.topN ?? 1);
      const match = matches[0] || null;
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
              topN: params.topN ?? 1,
              count: ocr?.count || 0,
              items: ocr?.items || [],
              matches,
              debugOverlay: ocr?.debugOverlay || null,
              engine: ocr?.engine || null,
              ocr,
            }),
          }],
        };
      }

      const clickX = Math.round(match.centerX);
      const clickY = Math.round(match.centerY);
      const button = params.button || "left";
      const dryRun = Boolean(params.dryRun);
      let clickText = "DRY_RUN";
      let verify: any = null;
      if (!dryRun) {
        await runPy(scriptPath, ["mouse-move", String(clickX), String(clickY)]);
        clickText = await runPy(scriptPath, ["mouse-click", button]);

        const shouldVerify = Boolean(params.verifyQuery || params.verifyAbsentQuery);
        if (shouldVerify) {
          const delayMs = Math.max(0, Math.round(params.verifyDelayMs ?? 700));
          if (delayMs > 0) {
            await new Promise((resolve) => setTimeout(resolve, delayMs));
          }
          const verifyImagePath = await captureScreen(captureScriptPath, params);
          const verifyOcr = await runOcr(ocrScriptPath, {
            imagePath: verifyImagePath,
            lang: params.lang,
            preprocess: params.preprocess,
            groupBy: params.groupBy,
            topN: Math.max(params.topN ?? 1, 3),
          });
          const verifyItems = Array.isArray(verifyOcr?.items) ? verifyOcr.items : [];
          const normalizedTexts = verifyItems.map((item: any) => String(item?.normalizedText || ""));
          const verifyQuery = String(params.verifyQuery || "").trim().toLowerCase();
          const verifyAbsentQuery = String(params.verifyAbsentQuery || "").trim().toLowerCase();
          const present = verifyQuery ? normalizedTexts.some((t: string) => t.includes(verifyQuery)) : null;
          const absent = verifyAbsentQuery ? !normalizedTexts.some((t: string) => t.includes(verifyAbsentQuery)) : null;
          verify = {
            imagePath: verifyImagePath,
            verifyQuery: params.verifyQuery || null,
            verifyAbsentQuery: params.verifyAbsentQuery || null,
            verifyDelayMs: delayMs,
            present,
            absent,
            success: [present, absent].filter((v) => v !== null).every(Boolean),
            engine: verifyOcr?.engine || null,
            count: verifyOcr?.count || 0,
          };
        }
      }

      return {
        content: [{
          type: "text",
          text: JSON.stringify({
            ok: true,
            dryRun,
            query: params.query,
            queryMode: params.queryMode || "contains",
            imagePath,
            click: {
              x: clickX,
              y: clickY,
              button,
              executed: !dryRun,
              result: clickText,
            },
            verify,
            match,
            matches,
            topN: params.topN ?? 1,
            count: ocr?.count || 0,
            items: ocr?.items || [],
            debugOverlay: ocr?.debugOverlay || null,
            engine: ocr?.engine || null,
            ocr,
          }),
        }],
      };
    },
  }, { optional: true });
}
