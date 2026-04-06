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

    if not args.collect_only:
        rc, stdout, stderr = run_step(python_exe, job["send_script"])
        state["send"] = {"rc": rc, "stdout": stdout, "stderr": stderr}
        append_log(args.job, f"===== SEND {datetime.now().isoformat()} rc={rc} =====")
        append_log(args.job, stdout or "(no stdout)")
        if stderr:
            append_log(args.job, "[stderr]")
            append_log(args.job, stderr)
        if rc != 0:
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
