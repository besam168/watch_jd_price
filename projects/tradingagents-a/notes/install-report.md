# TradingAgents Shape A - Install Report

## Source
- Official repo: https://github.com/TauricResearch/TradingAgents
- Cloned commit: `fa4d01c23acef4882fd74dd5be75dd3c7a4bc5f7`

## Paths
- Project root: `C:\Users\besam\.openclaw\workspace\projects\tradingagents-a`
- Source repo: `C:\Users\besam\.openclaw\workspace\projects\tradingagents-a\repo`
- Virtualenv: `C:\Users\besam\.openclaw\workspace\projects\tradingagents-a\.venv`

## Environment
- OS: Windows
- Python: 3.12.10
- Git: 2.53.0.windows.1

## Install method
1. Clone official upstream repo
2. Create local venv with `python -m venv`
3. Upgrade pip/setuptools/wheel
4. Install package dependencies
5. Install local repo as editable package

## Key logs
- Initial install log: `logs/pip-install.log`
- Final install attempt and WinError details: `logs/pip-install-final.log`
- Dependency repair/local install: `logs/pip-fix-deps.log`
- Local editable install success: `logs/pip-local-install.log`
- Final package show: `logs/pip-show-final.log`

## Important finding
The first full install pass hit a Windows file-lock error during package installation:
- `WinError 32` on `openai\types\responses\response_audio_done_event.py`

Workaround that succeeded:
- install core dependencies into the venv
- then install the local repository with `pip install -e . --no-deps`

This produced a usable local editable installation for the official source tree.
