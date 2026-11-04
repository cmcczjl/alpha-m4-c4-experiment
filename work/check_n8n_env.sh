#!/usr/bin/env bash
# work/check_n8n_env.sh
# Diagnostics: detect timeout root cause for n8n environment validation
set -euo pipefail

log() { echo "[n8n-env] $*"; }

# 1. Check if n8n binary exists in PATH
if command -v n8n >/dev/null 2>&1; then
  log "PASS: n8n found in PATH: $(command -v n8n)"
else
  log "FAIL: n8n not in PATH; checking common locations..."
  for d in /usr/local/bin /opt/n8n ~/n8n; do
    [ -x "$d/n8n" ] && { log "FOUND: $d/n8n"; export PATH="$d:$PATH"; break; }
  done
  command -v n8n >/dev/null 2>&1 || { log "FAIL: n8n binary missing; install via npm i -g n8n"; exit 1; }
fi

# 2. Check Node.js version
NODE_VER="$(node -v 2>&1)" || { log "FAIL: node not found"; exit 1; }
log "Node version: $NODE_VER"
# n8n requires >=18; warn if lower
if node -e "const v=parseInt(process.version.slice(1),10); process.exit(v>=18?0:1)" 2>/dev/null; then
  log "PASS: Node >= 18"
else
  log "WARN: Node < 18; n8n may fail or hang on startup"
fi

# 3. Check n8n version
N8N_VER="$(n8n --version 2>&1)" || { log "FAIL: n8n --version failed: $N8N_VER"; exit 1; }
log "n8n version: $N8N_VER"

# 4. Probe startup timeout: start n8n web server on ephemeral port, wait up to 30s for port to accept connections
PORT=5678
N8N_HOST=127.0.0.1
N8N_PORT="$PORT" n8n start > /tmp/n8n_start.log 2>&1 &
PID=$!
log "Started n8n (pid=$PID), waiting up to 30s for port $PORT..."
ready=0
for i in $(seq 1 30); do
  if (exec 3<>/dev/tcp/$N8N_HOST/$PORT) 2>/dev/null; then
    exec 3>&-; exec 3<&-
    ready=1
    log "PASS: port $PORT ready after ${i}s"
    break
  fi
  sleep 1
done
if [ "$ready" -eq 1 ]; then
  # Try health endpoint
  RESP="$(curl -s -m 5 -o /dev/null -w '%{http_code}' "http://$N8N_HOST:$PORT/healthz" 2>&1)" || RESP="ERR"
  log "Health endpoint /healthz -> HTTP $RESP"
else
  log "TIMEOUT: port $PORT not ready after 30s"
fi

# 5. Always clean up
kill "$PID" 2>/dev/null || true
wait "$PID" 2>/dev/null || true
log "--- n8n startup log tail ---"
tail -n 40 /tmp/n8n_start.log

# 6. Summarize
log "Summary: n8n=$N8N_VER node=$NODE_VER port_ready=$ready"
exit 0