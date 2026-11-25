#!/usr/bin/env bash
# 저장소를 받으면 한 번 돌린다. 푸시 전에 tools/check.py 가 돌고, 실패하면 푸시를 멈춘다.
set -e
cd "$(git rev-parse --show-toplevel)"
cat > .git/hooks/pre-push <<'HOOK'
#!/usr/bin/env bash
git fetch -q origin main 2>/dev/null || true
python3 tools/check.py --base origin/main || { echo "검사 실패 — 푸시를 멈췄다 (tools/check.py)"; exit 1; }
HOOK
chmod +x .git/hooks/pre-push
echo "pre-push 훅을 깔았다 — .git/hooks/pre-push"
