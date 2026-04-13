from __future__ import annotations

from collect_formal_global_intel_report import collect_and_render
from send_formal_global_intel_report import send_latest

if __name__ == "__main__":
    result = collect_and_render()
    subject = send_latest()
    print("PIPELINE_OK")
    print(result["subject"])
    print(subject)
