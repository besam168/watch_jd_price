import { Type } from "@sinclair/typebox";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";
import { fileURLToPath } from "node:url";

const execFileAsync = promisify(execFile);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const agentPath = path.join(__dirname, "desktop_ocr_agent.py");

const matchModeSchema = Type.Union([
  Type.Literal("contains"),
  Type.Literal("exact"),
  Type.Literal("regex"),
]);

async function runAgent(args: string[]) {
  const result = await execFileAsync("python", [agentPath, ...args], {
    cwd: __dirname,
    env: { ...process.env, PYTHONIOENCODING: "utf-8" },
    maxBuffer: 1024 * 1024 * 32,
    windowsHide: true,
  });
  return `${result.stdout || ""}${result.stderr || ""}`.trim() || "OK";
}

function maybeArg(flag: string, value: unknown): string[] {
  if (value === undefined || value === null || value === "") {
    return [];
  }
  return [flag, String(value)];
}

export default function (api) {
  api.registerTool({
    name: "desktop_ocr_scan_primary",
    description: "Capture only the Windows primary screen, run PaddleOCR Chinese OCR, and save screenshot/debug/log artifacts. No clicking.",
    parameters: Type.Object({}),
    async execute() {
      const text = await runAgent(["--scan"]);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });

  api.registerTool({
    name: "desktop_ocr_click_text",
    description: "Find text on the Windows primary screen with PaddleOCR Chinese OCR and click the best matching text center. Defaults to dry-run unless click=true.",
    parameters: Type.Object({
      text: Type.String({ description: "Target text to find, for example 确定 or 登录." }),
      match: Type.Optional(matchModeSchema),
      click: Type.Optional(Type.Boolean({ description: "Set true to really click. False/omitted performs dry-run only." })),
      failIfMultiple: Type.Optional(Type.Boolean({ description: "When true, abort if multiple candidates match instead of choosing the highest-confidence one." })),
      listMatches: Type.Optional(Type.Boolean({ description: "When true, include all matching candidates in the output for manual confirmation." })),
    }),
    async execute(_id, params) {
      const args = [
        "--text", String(params.text),
        ...maybeArg("--match", params.match || "contains"),
      ];
      if (params.failIfMultiple === true) {
        args.push("--fail-if-multiple");
      }
      if (params.listMatches === true) {
        args.push("--list-matches");
      }
      if (params.click === true) {
        args.push("--click");
      } else {
        args.push("--dry-run");
      }
      const text = await runAgent(args);
      return { content: [{ type: "text", text }] };
    },
  }, { optional: true });
}
