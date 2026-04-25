#!/bin/sh

MQTT_HOST="${MQTT_HOST:-127.0.0.1}"
MQTT_PORT="${MQTT_PORT:-1883}"
RTMP_URL="${RTMP_URL:-rtmp://127.0.0.1:1935/myapp/stream}"
NET_CHECK_HOST="${NET_CHECK_HOST:-127.0.0.1}"
MOSQUITTO_PUB_BIN="${MOSQUITTO_PUB_BIN:-/root/mosquitto_pub}"
MOSQUITTO_SUB_BIN="${MOSQUITTO_SUB_BIN:-/root/mosquitto_sub}"
NET_UP_SCRIPT="${NET_UP_SCRIPT:-/root/net_up.sh}"

STREAM_PROC="v4l2_rtmp_push"
STREAM_CMD="/root/v4l2_rtmp_push /dev/video0 ${RTMP_URL} 320 240 15 0"

LOCK_FILE="/tmp/edge_agent.lock"
HEARTBEAT_INTERVAL=5

export LD_LIBRARY_PATH=/root:$LD_LIBRARY_PATH

log() {
    echo "[agent] $*"
}

already_running() {
    if [ -f "$LOCK_FILE" ]; then
        OLD_PID=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
            return 0
        fi
    fi
    return 1
}

write_lock() {
    echo $$ > "$LOCK_FILE"
}

cleanup() {
    log "cleanup"
    rm -f "$LOCK_FILE"
    if [ -n "$HB_PID" ]; then
        kill "$HB_PID" 2>/dev/null
    fi
    exit 0
}

network_ok() {
    ping -c 1 "$NET_CHECK_HOST" >/dev/null 2>&1
}

ensure_network() {
    if network_ok; then
        return 0
    fi

    log "network not ready, reconfig eth0"
    "$NET_UP_SCRIPT" >/root/net_up.log 2>&1
    sleep 2

    if network_ok; then
        log "network recovered"
        return 0
    fi

    log "network still unavailable"
    return 1
}

stream_running() {
    pidof "$STREAM_PROC" >/dev/null 2>&1
}

start_stream() {
    if stream_running; then
        log "stream already running"
        return 0
    fi

    ensure_network || return 1

    log "starting stream"
    sh -c "$STREAM_CMD >/root/stream.log 2>&1 &"
    sleep 2

    if stream_running; then
        log "stream started"
        return 0
    else
        log "stream start failed"
        return 1
    fi
}

stop_stream() {
    if stream_running; then
        log "stopping stream"
        killall "$STREAM_PROC"
        sleep 1
    else
        log "stream not running"
    fi
}

buzzer_on() {
    log "buzzer on"
    # TODO: replace with the real buzzer control command.
}

buzzer_off() {
    log "buzzer off"
    # TODO: replace with the real buzzer off command.
}

led_blink() {
    log "led blink"
    # TODO: replace with the real LED blink command.
}

publish_heartbeat() {
    while true
    do
        if stream_running; then
            STREAMING=true
        else
            STREAMING=false
        fi

        "$MOSQUITTO_PUB_BIN" -h "$MQTT_HOST" -p "$MQTT_PORT" \
          -t edge/heartbeat \
          -m "{\"device\":\"edge\",\"alive\":true,\"streaming\":$STREAMING}"

        sleep "$HEARTBEAT_INTERVAL"
    done
}

if already_running; then
    OLD_PID=$(cat "$LOCK_FILE" 2>/dev/null)
    log "already running with pid $OLD_PID"
    exit 0
fi

write_lock
trap cleanup INT TERM

publish_heartbeat &
HB_PID=$!

"$MOSQUITTO_SUB_BIN" -h "$MQTT_HOST" -p "$MQTT_PORT" \
  -t edge/stream/start \
  -t edge/stream/stop \
  -t edge/buzzer/on \
  -t edge/buzzer/off \
  -t edge/led/blink -v | \
while read -r topic payload
do
    case "$topic" in
        edge/stream/start)
            start_stream
            ;;
        edge/stream/stop)
            stop_stream
            ;;
        edge/buzzer/on)
            buzzer_on
            ;;
        edge/buzzer/off)
            buzzer_off
            ;;
        edge/led/blink)
            led_blink
            ;;
        *)
            log "unknown topic: $topic payload: $payload"
            ;;
    esac
done
