import { Type } from "@sinclair/typebox";
import { execFile } from "node:child_process";
import { promisify } from "node:util";
import path from "node:path";

const execFileAsync = promisify(execFile);

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

  api.registerTool(
    {
      name: "desktop_mouse_move",
      description: "Move the Windows mouse pointer to an absolute screen position.",
      parameters: Type.Object({
        x: Type.Number(),
        y: Type.Number(),
      }),
      async execute(_id, params) {
        const text = await runPs(scriptPath, ["mouse-move", String(params.x), String(params.y)]);
        return { content: [{ type: "text", text }] };
      },
    },
    { optional: true },
  );

  api.registerTool(
    {
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
    },
    { optional: true },
  );

  api.registerTool(
    {
      name: "desktop_type_text",
      description: "Type text into the active Windows input focus using SendKeys.",
      parameters: Type.Object({
        text: Type.String(),
      }),
      async execute(_id, params) {
        const text = await runPs(scriptPath, ["type-text", params.text]);
        return { content: [{ type: "text", text }] };
      },
    },
    { optional: true },
  );

  api.registerTool(
    {
      name: "desktop_press_hotkey",
      description: "Press a Windows hotkey combination such as ctrl+s, alt+tab, win+r, or enter.",
      parameters: Type.Object({
        keys: Type.String(),
      }),
      async execute(_id, params) {
        const text = await runPs(scriptPath, ["press-hotkey", params.keys]);
        return { content: [{ type: "text", text }] };
      },
    },
    { optional: true },
  );
}
