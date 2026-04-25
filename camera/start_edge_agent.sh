#!/bin/sh

export LD_LIBRARY_PATH=/root:$LD_LIBRARY_PATH
LOCK_FILE="/tmp/edge_agent.lock"

if [ -f "$LOCK_FILE" ]; then
    PID=$(cat "$LOCK_FILE" 2>/dev/null)
    if [ -n "$PID" ] && kill -0 "$PID" 2>/dev/null; then
        echo "[start_edge_agent] already running pid=$PID" >> /root/edge_agent_boot.log
        exit 0
    fi
fi

echo "[start_edge_agent] preparing network" >> /root/edge_agent_boot.log
/root/net_up.sh >> /root/edge_agent_boot.log 2>&1
sleep 2

echo "[start_edge_agent] launching edge_agent.sh" >> /root/edge_agent_boot.log
/root/edge_agent.sh >> /root/edge_agent_boot.log 2>&1 &
