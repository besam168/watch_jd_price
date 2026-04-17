import urllib.request
import xml.etree.ElementTree as ET
import re
from pathlib import Path

OUT = Path(r"C:\Users\besam\.openclaw\workspace\self-evolution\patrol-run-2026-04-17.txt")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
}


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=25) as resp:
        return resp.read().decode("utf-8", errors="ignore")


def grab_reddit_rss(label: str, url: str, limit: int = 5):
    lines = [f"=== {label} ==="]
    try:
        xml_text = fetch(url)
        root = ET.fromstring(xml_text)
        ns = {"a": "http://www.w3.org/2005/Atom"}
        entries = root.findall("a:entry", ns)[:limit]
        if not entries:
            lines.append("(no entries)")
        for i, entry in enumerate(entries, 1):
            title = (entry.findtext("a:title", default="", namespaces=ns) or "").strip().replace("\n", " ")
            link_el = entry.find("a:link", ns)
            href = link_el.attrib.get("href", "") if link_el is not None else ""
            lines.append(f"{i}. {title}")
            lines.append(f"   {href}")
    except Exception as e:
        lines.append(f"ERROR: {type(e).__name__}: {e}")
    lines.append("")
    return lines


def grab_github_topic(label: str, url: str, limit: int = 12):
    lines = [f"=== {label} ==="]
    try:
        html = fetch(url)
        repo_matches = re.findall(r'href="/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)"', html)
        repos = []
        banned_prefixes = (
            "topics/", "features/", "enterprise", "collections/", "trending", "marketplace",
            "orgs/", "users/", "settings/", "account/", "site/", "github/", "sponsors/", "login"
        )
        for repo in repo_matches:
            if repo in repos:
                continue
            if any(repo.startswith(prefix) for prefix in banned_prefixes):
                continue
            repos.append(repo)
        if not repos:
            lines.append("(no repos matched)")
        for i, repo in enumerate(repos[:limit], 1):
            lines.append(f"{i}. https://github.com/{repo}")
    except Exception as e:
        lines.append(f"ERROR: {type(e).__name__}: {e}")
    lines.append("")
    return lines


def main():
    lines = []
    lines += grab_reddit_rss("REDDIT LocalLLaMA top week", "https://www.reddit.com/r/LocalLLaMA/top/.rss?t=week")
    lines += grab_reddit_rss("REDDIT OpenAI top week", "https://www.reddit.com/r/OpenAI/top/.rss?t=week")
    lines += grab_reddit_rss("REDDIT ChatGPT top week", "https://www.reddit.com/r/ChatGPT/top/.rss?t=week")
    lines += grab_github_topic("GITHUB topic ai-agents", "https://github.com/topics/ai-agents")
    lines += grab_github_topic("GITHUB topic browser-automation", "https://github.com/topics/browser-automation")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print(str(OUT))


if __name__ == "__main__":
    main()
