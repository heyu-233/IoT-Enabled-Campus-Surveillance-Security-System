#!/bin/sh

export LD_LIBRARY_PATH=/root:$LD_LIBRARY_PATH
LOCK_FILE="/tmp/edge_agent.lock"
LOG_FILE="/root/edge_agent_boot.log"

log() {
    echo "[start_edge_agent] $*" >> "$LOG_FILE"
}

# cleanup: remove lock if stored PID is not alive
if [ -f "$LOCK_FILE" ]; then
    OLD_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
        log "already running pid=$OLD_PID"
        exit 0
    fi
    log "stale lock file (pid=$OLD_PID not alive), removing"
    rm -f "$LOCK_FILE"
fi

# wait for network to stabilize
log "waiting for network..."
for i in 1 2 3 4 5 6; do
    /root/net_up.sh >> "$LOG_FILE" 2>&1
    sleep 3
    if ip addr show eth0 2>/dev/null | grep -q 'inet '; then
        log "eth0 ready"
        break
    fi
    log "retry $i..."
done

log "launching edge_agent.sh"
/root/edge_agent.sh >> "$LOG_FILE" 2>&1 &
