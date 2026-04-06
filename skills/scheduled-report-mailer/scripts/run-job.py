from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SKILL_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = SKILL_ROOT / "config" / "report-config.json"
STATE_DIR = SKILL_ROOT / "state"
LOG_DIR = SKILL_ROOT / "logs"
STATE_DIR.mkdir(parents=True, exist_ok=True)
LOG_DIR.mkdir(parents=True, exist_ok=True)


def load_config() -> dict:
    return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))


def run_step(python_exe: str, script_name: str) -> tuple[int, str, str]:
    script_path = ROOT / script_name if not str(script_name).startswith(str(SKILL_ROOT)) else Path(script_name)
    completed = subprocess.run(
        [python_exe, str(script_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout, completed.stderr


def save_state(job: str, data: dict) -> None:
    out = STATE_DIR / f"last-{job}.json"
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def append_log(job: str, text: str) -> None:
    path = LOG_DIR / f"{job}.log"
    with path.open("a", encoding="utf-8") as f:
        f.write(text.rstrip() + "\n")


def resolve_outputs(cfg: dict) -> dict[str, str | None]:
    out_cfg = cfg.get("paths", {})
    resolved: dict[str, str | None] = {}
    for key, rel in out_cfg.items():
        path = ROOT / rel
        resolved[key] = str(path) if path.exists() else None
    return resolved


def summarize_policy(cfg: dict) -> dict:
    policy = cfg.get("collection_policy", {})
    return {
        "timeWindowHours": policy.get("time_window_hours", {}),
        "mustCheck": policy.get("must_check", []),
        "strategyNames": [x.get("name") for x in policy.get("capture_strategies", [])],
        "whitelistCount": len(policy.get("whitelist_urls", [])),
        "sendOnPartial": cfg.get("delivery_policy", {}).get("send_on_partial", "send_with_warning"),
        "desktopFallbackEnabled": bool(cfg.get("desktop_fallback", {}).get("enabled", False)),
    }


def load_evaluation_summary() -> dict:
    eval_path = STATE_DIR / "report-evaluation.json"
    if not eval_path.exists():
        return {"status": "unknown", "missing": [], "okCount": 0, "total": 0, "summaryText": "无验收结果"}
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    checks = data.get("mustCheckResults", {})
    missing = [k for k, v in checks.items() if not v.get("ok")]
    ok_count = data.get("summary", {}).get("okCount", 0)
    total = data.get("summary", {}).get("total", 0)
    if not missing:
        status = "pass"
        summary_text = f"状态：通过 | 命中：{ok_count}/{total} | 缺口：无 | 建议：可直接发送"
    elif ok_count >= max(total - 1, 1):
        status = "partial"
        summary_text = f"状态：部分通过 | 命中：{ok_count}/{total} | 缺口：{', '.join(missing)} | 建议：优先补抓或先发后补"
    else:
        status = "fail"
        summary_text = f"状态：未通过 | 命中：{ok_count}/{total} | 缺口：{', '.join(missing)} | 建议：重跑并补抓"
    return {
        "status": status,
        "missing": missing,
        "okCount": ok_count,
        "total": total,
        "summaryText": summary_text,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job", required=True)
    parser.add_argument("--collect-only", action="store_true")
    args = parser.parse_args()

    cfg = load_config()
    jobs = cfg.get("jobs", {})
    job = jobs.get(args.job)
    if not job:
        print(f"Unknown job: {args.job}", file=sys.stderr)
        return 2

    python_exe = cfg["python"]
    started = datetime.now().isoformat()
    plan_script = SKILL_ROOT / "scripts" / "build-collect-plan.py"
    eval_script = SKILL_ROOT / "scripts" / "evaluate-report.py"
    desktop_fallback_script = SKILL_ROOT / "scripts" / "desktop-fallback.py"
    send_on_partial = cfg.get("delivery_policy", {}).get("send_on_partial", "send_with_warning")
    plan_rc, plan_stdout, plan_stderr = run_step(python_exe, str(plan_script))
    state: dict = {
        "job": args.job,
        "mode": "collect-only" if args.collect_only else "collect-and-send",
        "startedAt": started,
        "policy": summarize_policy(cfg),
        "plan": {"rc": plan_rc, "stdout": plan_stdout, "stderr": plan_stderr},
        "collect": None,
        "send": None,
        "evaluation": None,
        "summary": None,
        "desktopFallback": None,
        "status": "running",
        "failedStage": None,
        "outputs": {},
    }

    rc, stdout, stderr = run_step(python_exe, job["collect_script"])
    state["collect"] = {"rc": rc, "stdout": stdout, "stderr": stderr}
    append_log(args.job, f"===== PLAN {started} rc={plan_rc} =====")
    append_log(args.job, plan_stdout or "(no plan stdout)")
    if plan_stderr:
        append_log(args.job, "[plan stderr]")
        append_log(args.job, plan_stderr)
    append_log(args.job, f"===== COLLECT {started} rc={rc} =====")
    append_log(args.job, stdout or "(no stdout)")
    if stderr:
        append_log(args.job, "[stderr]")
        append_log(args.job, stderr)
    state["outputs"] = resolve_outputs(cfg)
    if rc != 0:
        state["status"] = "failed"
        state["failedStage"] = "collect"
        state["finishedAt"] = datetime.now().isoformat()
        save_state(args.job, state)
        print("JOB_FAILED_AT_COLLECT")
        return rc

    eval_rc, eval_stdout, eval_stderr = run_step(python_exe, str(eval_script))
    state["evaluation"] = {"rc": eval_rc, "stdout": eval_stdout, "stderr": eval_stderr}
    append_log(args.job, f"===== EVALUATE {datetime.now().isoformat()} rc={eval_rc} =====")
    append_log(args.job, eval_stdout or "(no eval stdout)")
    if eval_stderr:
        append_log(args.job, "[eval stderr]")
        append_log(args.job, eval_stderr)

    eval_summary = load_evaluation_summary()
    state["summary"] = eval_summary
    append_log(args.job, "===== SUMMARY =====")
    append_log(args.job, eval_summary["summaryText"])

    if eval_summary["status"] != "pass" and cfg.get("desktop_fallback", {}).get("enabled", False):
        fb_rc, fb_stdout, fb_stderr = run_step(python_exe, str(desktop_fallback_script))
        state["desktopFallback"] = {"rc": fb_rc, "stdout": fb_stdout, "stderr": fb_stderr}
        append_log(args.job, f"===== DESKTOP_FALLBACK {datetime.now().isoformat()} rc={fb_rc} =====")
        append_log(args.job, fb_stdout or "(no desktop fallback stdout)")
        if fb_stderr:
            append_log(args.job, "[desktop fallback stderr]")
            append_log(args.job, fb_stderr)

    if eval_summary["status"] == "pass":
        state["status"] = "pass"
    elif eval_summary["status"] == "partial":
        state["status"] = "partial"
    else:
        state["status"] = "fail"

    if not args.collect_only:
        if state["status"] == "partial" and send_on_partial == "block":
            state["failedStage"] = "quality-gate"
            state["finishedAt"] = datetime.now().isoformat()
            state["outputs"] = resolve_outputs(cfg)
            save_state(args.job, state)
            print("JOB_BLOCKED_AT_PARTIAL")
            print(eval_summary["summaryText"])
            return 3
        if state["status"] == "fail":
            state["failedStage"] = "quality-gate"
            state["finishedAt"] = datetime.now().isoformat()
            state["outputs"] = resolve_outputs(cfg)
            save_state(args.job, state)
            print("JOB_BLOCKED_AT_FAIL")
            print(eval_summary["summaryText"])
            return 4

        rc, stdout, stderr = run_step(python_exe, job["send_script"])
        state["send"] = {"rc": rc, "stdout": stdout, "stderr": stderr, "sendPolicy": send_on_partial}
        append_log(args.job, f"===== SEND {datetime.now().isoformat()} rc={rc} =====")
        append_log(args.job, stdout or "(no stdout)")
        if send_on_partial == "send_with_warning" and state["status"] == "partial":
            append_log(args.job, "[warning]")
            append_log(args.job, eval_summary["summaryText"])
        if stderr:
            append_log(args.job, "[stderr]")
            append_log(args.job, stderr)
        if rc != 0:
            state["status"] = "failed"
            state["failedStage"] = "send"
            state["finishedAt"] = datetime.now().isoformat()
            state["outputs"] = resolve_outputs(cfg)
            save_state(args.job, state)
            print("JOB_FAILED_AT_SEND")
            return rc

    state["finishedAt"] = datetime.now().isoformat()
    state["outputs"] = resolve_outputs(cfg)
    save_state(args.job, state)
    print("JOB_OK")
    if state["outputs"].get("latest_subject"):
        try:
            subject = Path(state["outputs"]["latest_subject"]).read_text(encoding="utf-8").strip()
            print(subject)
        except Exception:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
