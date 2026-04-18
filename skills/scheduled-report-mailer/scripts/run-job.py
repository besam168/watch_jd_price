from __future__ import annotations

import argparse
import json
import os
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


def run_step(python_exe: str, script_name: str, extra_env: dict[str, str] | None = None) -> tuple[int, str, str]:
    script_path = ROOT / script_name if not str(script_name).startswith(str(SKILL_ROOT)) else Path(script_name)
    env = os.environ.copy()
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("PYTHONUTF8", "1")
    if extra_env:
        env.update(extra_env)
    completed = subprocess.run(
        [python_exe, str(script_path)],
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.returncode, completed.stdout, completed.stderr


def heartbeat(message: str) -> None:
    print(message, flush=True)


def mark_stage(state: dict, job_name: str, stage: str, **extra: object) -> None:
    state["lastStage"] = stage
    state["lastStageAt"] = datetime.now().isoformat()
    if extra:
        state.update(extra)
    save_state(job_name, state)


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


def load_latest_evidence() -> dict:
    path = ROOT / "reports" / "scheduled" / "latest_report_evidence.json"
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def should_trigger_desktop_fallback(cfg: dict, eval_summary: dict) -> dict:
    fallback_cfg = cfg.get("desktop_fallback", {})
    enabled = bool(fallback_cfg.get("enabled", False))
    mode = str(fallback_cfg.get("mode", "conditional_trigger") or "conditional_trigger")
    reasons: list[str] = []

    if eval_summary.get("status") != "pass":
        reasons.append("quality_gate_not_pass")

    trigger_cfg = fallback_cfg.get("trigger", {}) if isinstance(fallback_cfg.get("trigger", {}), dict) else {}
    evidence = load_latest_evidence()
    headline_count = int(evidence.get("headlineCount", 0) or 0)
    evidence_count = int(evidence.get("headlineEvidenceCount", 0) or 0)
    has_placeholder = bool(evidence.get("hasPlaceholderSearchDiscovery", False))

    min_headlines = int(trigger_cfg.get("min_headlines", 0) or 0)
    min_evidence = int(trigger_cfg.get("min_evidence", 0) or 0)

    if min_headlines > 0 and headline_count < min_headlines:
        reasons.append(f"headline_count_below_{min_headlines}")
    if min_evidence > 0 and evidence_count < min_evidence:
        reasons.append(f"evidence_count_below_{min_evidence}")
    if trigger_cfg.get("block_placeholder_search_discovery", False) and has_placeholder:
        reasons.append("placeholder_search_discovery_present")

    if trigger_cfg.get("block_empty_summary_marker", False):
        report_path = ROOT / cfg.get("paths", {}).get("latest_report_txt", "reports/scheduled/latest_report.txt")
        report_text = report_path.read_text(encoding="utf-8", errors="replace") if report_path.exists() else ""
        if "今日无额外摘要" in report_text:
            reasons.append("empty_summary_marker_present")

    if not enabled:
        should_run = False
    elif mode == "always":
        should_run = True
        if not reasons:
            reasons.append("mode_always")
    else:
        should_run = bool(reasons)

    return {
        "enabled": enabled,
        "mode": mode,
        "shouldRun": should_run,
        "reasons": reasons,
        "headlineCount": headline_count,
        "headlineEvidenceCount": evidence_count,
        "hasPlaceholderSearchDiscovery": has_placeholder,
    }


def load_evaluation_summary() -> dict:
    eval_path = STATE_DIR / "report-evaluation.json"
    if not eval_path.exists():
        return {
            "status": "unknown",
            "missing": [],
            "okCount": 0,
            "total": 0,
            "summaryText": "无验收结果",
            "anchorMissing": [],
            "contentCoverageOk": False,
        }
    data = json.loads(eval_path.read_text(encoding="utf-8"))
    checks = data.get("mustCheckResults", {})
    anchor_missing = [k for k, v in checks.items() if not v.get("ok")]
    missing = list(anchor_missing)
    ok_count = data.get("summary", {}).get("okCount", 0)
    total = data.get("summary", {}).get("total", 0)

    content_gate = data.get("contentCoverageGate", {})
    content_coverage_ok = bool(content_gate.get("ok", False))
    if not content_coverage_ok:
        missing = list(dict.fromkeys(missing + ["content-coverage"]))

    headline_gate = data.get("headlineEvidenceGate", {})
    if headline_gate and not headline_gate.get("ok"):
        missing = list(dict.fromkeys(missing + ["headline-evidence"]))

    if not content_coverage_ok:
        status = "fail"
        summary_text = (
            f"状态：未通过 | 锚点命中：{ok_count}/{total} | 缺口：{', '.join(missing)} | "
            f"建议：先补足可信国际时事内容，再谈发送"
        )
    elif headline_gate and not headline_gate.get("ok"):
        status = "partial"
        summary_text = (
            f"状态：部分通过 | 锚点命中：{ok_count}/{total} | 缺口：{', '.join(missing)} | "
            f"建议：内容已命中，但应优先补正文证据"
        )
    elif anchor_missing:
        status = "pass"
        summary_text = (
            f"状态：通过 | 锚点命中：{ok_count}/{total} | 缺口：{', '.join(anchor_missing)} | "
            f"建议：可发送；未命中锚点按观察项处理"
        )
    else:
        status = "pass"
        summary_text = f"状态：通过 | 锚点命中：{ok_count}/{total} | 缺口：无 | 建议：可直接发送"

    return {
        "status": status,
        "missing": missing,
        "okCount": ok_count,
        "total": total,
        "summaryText": summary_text,
        "anchorMissing": anchor_missing,
        "contentCoverageOk": content_coverage_ok,
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
    run_id = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    plan_script = SKILL_ROOT / "scripts" / "build-collect-plan.py"
    eval_script = SKILL_ROOT / "scripts" / "evaluate-report.py"
    desktop_fallback_script = SKILL_ROOT / "scripts" / "desktop-fallback.py"
    send_on_partial = cfg.get("delivery_policy", {}).get("send_on_partial", "send_with_warning")
    state: dict = {
        "job": args.job,
        "mode": "collect-only" if args.collect_only else "collect-and-send",
        "startedAt": started,
        "runId": run_id,
        "policy": summarize_policy(cfg),
        "plan": None,
        "collect": None,
        "send": None,
        "evaluation": None,
        "summary": None,
        "desktopFallback": None,
        "status": "running",
        "failedStage": None,
        "lastStage": "init",
        "lastStageAt": started,
        "outputs": {},
    }
    mark_stage(state, args.job, "plan:start")
    heartbeat(f"[run-job] {args.job} plan:start")
    plan_rc, plan_stdout, plan_stderr = run_step(python_exe, str(plan_script))
    state["plan"] = {"rc": plan_rc, "stdout": plan_stdout, "stderr": plan_stderr}
    mark_stage(state, args.job, "plan:done")
    heartbeat(f"[run-job] {args.job} plan:done rc={plan_rc}")

    mark_stage(state, args.job, "collect:start")
    heartbeat(f"[run-job] {args.job} collect:start")
    rc, stdout, stderr = run_step(
        python_exe,
        job["collect_script"],
        extra_env={"SWS_COLLECT_RUN_ID": run_id},
    )
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
    mark_stage(state, args.job, "collect:done")
    heartbeat(f"[run-job] {args.job} collect:done rc={rc}")
    if rc != 0:
        state["status"] = "failed"
        state["failedStage"] = "collect"
        state["finishedAt"] = datetime.now().isoformat()
        save_state(args.job, state)
        print("JOB_FAILED_AT_COLLECT")
        return rc

    mark_stage(state, args.job, "evaluate:start")
    heartbeat(f"[run-job] {args.job} evaluate:start")
    eval_rc, eval_stdout, eval_stderr = run_step(python_exe, str(eval_script))
    state["evaluation"] = {"rc": eval_rc, "stdout": eval_stdout, "stderr": eval_stderr}
    append_log(args.job, f"===== EVALUATE {datetime.now().isoformat()} rc={eval_rc} =====")
    append_log(args.job, eval_stdout or "(no eval stdout)")
    if eval_stderr:
        append_log(args.job, "[eval stderr]")
        append_log(args.job, eval_stderr)

    eval_summary = load_evaluation_summary()
    state["summary"] = eval_summary
    mark_stage(state, args.job, "evaluate:done")
    heartbeat(
        f"[run-job] {args.job} evaluate:done rc={eval_rc} status={eval_summary['status']}"
    )
    append_log(args.job, "===== SUMMARY =====")
    append_log(args.job, eval_summary["summaryText"])

    fallback_decision = should_trigger_desktop_fallback(cfg, eval_summary)
    state["desktopFallbackDecision"] = fallback_decision
    mark_stage(state, args.job, "desktop-fallback:decision")
    heartbeat(
        f"[run-job] {args.job} desktop-fallback:decision shouldRun={fallback_decision['shouldRun']} reasons={','.join(fallback_decision['reasons']) or 'none'}"
    )
    append_log(args.job, "===== DESKTOP_FALLBACK_DECISION =====")
    append_log(
        args.job,
        f"enabled={fallback_decision['enabled']} shouldRun={fallback_decision['shouldRun']} reasons={','.join(fallback_decision['reasons']) or 'none'} "
        f"headlineCount={fallback_decision['headlineCount']} headlineEvidenceCount={fallback_decision['headlineEvidenceCount']} "
        f"hasPlaceholderSearchDiscovery={fallback_decision['hasPlaceholderSearchDiscovery']}",
    )

    if fallback_decision["shouldRun"]:
        mark_stage(state, args.job, "desktop-fallback:start")
        heartbeat(f"[run-job] {args.job} desktop-fallback:start")
        fb_rc, fb_stdout, fb_stderr = run_step(python_exe, str(desktop_fallback_script))
        state["desktopFallback"] = {
            "rc": fb_rc,
            "stdout": fb_stdout,
            "stderr": fb_stderr,
            "decision": fallback_decision,
        }
        append_log(args.job, f"===== DESKTOP_FALLBACK {datetime.now().isoformat()} rc={fb_rc} =====")
        append_log(args.job, fb_stdout or "(no desktop fallback stdout)")
        if fb_stderr:
            append_log(args.job, "[desktop fallback stderr]")
            append_log(args.job, fb_stderr)

        mark_stage(state, args.job, "desktop-fallback:done")
        heartbeat(f"[run-job] {args.job} desktop-fallback:done rc={fb_rc}")
        eval_rc_after_fb, eval_stdout_after_fb, eval_stderr_after_fb = run_step(python_exe, str(eval_script))
        state["evaluationAfterFallback"] = {
            "rc": eval_rc_after_fb,
            "stdout": eval_stdout_after_fb,
            "stderr": eval_stderr_after_fb,
        }
        append_log(args.job, f"===== EVALUATE_AFTER_FALLBACK {datetime.now().isoformat()} rc={eval_rc_after_fb} =====")
        append_log(args.job, eval_stdout_after_fb or "(no eval-after-fallback stdout)")
        if eval_stderr_after_fb:
            append_log(args.job, "[eval-after-fallback stderr]")
            append_log(args.job, eval_stderr_after_fb)

        eval_summary = load_evaluation_summary()
        state["summary"] = eval_summary
        mark_stage(state, args.job, "evaluate-after-fallback:done")
        heartbeat(
            f"[run-job] {args.job} evaluate-after-fallback:done rc={eval_rc_after_fb} status={eval_summary['status']}"
        )
        append_log(args.job, "===== SUMMARY_AFTER_FALLBACK =====")
        append_log(args.job, eval_summary["summaryText"])

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
            mark_stage(state, args.job, "quality-gate:blocked-partial")
            print("JOB_BLOCKED_AT_PARTIAL")
            print(eval_summary["summaryText"])
            return 3
        if state["status"] == "fail":
            state["failedStage"] = "quality-gate"
            state["finishedAt"] = datetime.now().isoformat()
            state["outputs"] = resolve_outputs(cfg)
            mark_stage(state, args.job, "quality-gate:blocked-fail")
            print("JOB_BLOCKED_AT_FAIL")
            print(eval_summary["summaryText"])
            return 4

        mark_stage(state, args.job, "send:start")
        heartbeat(f"[run-job] {args.job} send:start")
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
        mark_stage(state, args.job, "send:done")
        heartbeat(f"[run-job] {args.job} send:done rc={rc}")
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
    mark_stage(state, args.job, "done")
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
