#!/bin/sh

MQTT_HOST="192.168.1.10"
MQTT_PORT="1883"

STREAM_PROC="v4l2_rtmp_push"
STREAM_CMD="/root/v4l2_rtmp_push /dev/video0 rtmp://192.168.1.10:1935/myapp/stream 320 240 15 0"

LOCK_FILE="/tmp/edge_agent.lock"
HEARTBEAT_INTERVAL=5
LIGHT_INTERVAL=1

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
    if [ -n "$LIGHT_PID" ]; then
        kill "$LIGHT_PID" 2>/dev/null
    fi
    exit 0
}

network_ok() {
    ping -c 1 192.168.1.10 >/dev/null 2>&1
}

ensure_network() {
    if network_ok; then
        return 0
    fi

    log "network not ready, reconfig eth0"
    /root/net_up.sh >/root/net_up.log 2>&1
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

ALARM_PID=""
ALARM_COOLDOWN=6
LAST_ALARM_TIME=0

trigger_alarm() {
    NOW=$(date +%s)
    if [ $((NOW - LAST_ALARM_TIME)) -lt $ALARM_COOLDOWN ]; then
        log "alarm cooldown active, skipping ($((ALARM_COOLDOWN - NOW + LAST_ALARM_TIME))s remaining)"
        return
    fi
    LAST_ALARM_TIME=$NOW
    log "alarm triggered"

    for pid in $ALARM_PID; do
        [ -n "$pid" ] && kill $pid 2>/dev/null
        wait $pid 2>/dev/null
    done

    (
        echo 255 > /sys/class/leds/sys-led/brightness
        sleep 6
        echo 0 > /sys/class/leds/sys-led/brightness
    ) &
    LED_PID=$!

    (
        for i in 1 2 3; do
            echo 255 > /sys/class/leds/beep/brightness
            sleep 1
            echo 0 > /sys/class/leds/beep/brightness
            sleep 1
        done
    ) &
    BEEP_PID=$!
    ALARM_PID="$LED_PID $BEEP_PID"
}

buzzer_on() {
    trigger_alarm
}

buzzer_off() {
    log "buzzer off"
    for pid in $ALARM_PID; do
        [ -n "$pid" ] && kill $pid 2>/dev/null
        wait $pid 2>/dev/null
    done
    ALARM_PID=""
    echo 0 > /sys/class/leds/beep/brightness
    echo 0 > /sys/class/leds/sys-led/brightness
}

led_blink() {
    trigger_alarm
}

poll_light_sensor() {
    i2cset -y 0 0x1e 0x00 0x00 2>/dev/null  # 复位
    sleep 0.5
    i2cset -y 0 0x1e 0x00 0x01 2>/dev/null  # 激活ALS
    sleep 0.5
    while true; do
        l=$(i2cget -y 0 0x1e 0x0c b 2>/dev/null | sed 's/^0x//')
        h=$(i2cget -y 0 0x1e 0x0d b 2>/dev/null | sed 's/^0x//')
        if [ -n "$h" ] && [ -n "$l" ]; then
            val=$(( (0x$h * 256) + 0x$l ))
            /root/mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" \
                -t sensors/light \
                -m "{\"device_id\":\"edge\",\"als_value\":$val}"
        fi
        sleep "$LIGHT_INTERVAL"
    done
}

camera_adjust() {
    gamma="$1"
    echo "$gamma" > /tmp/camera_gamma
    log "camera gamma set to $gamma"
}

publish_heartbeat() {
    while true
    do
        if stream_running; then
            STREAMING=true
        else
            STREAMING=false
        fi

        /root/mosquitto_pub -h "$MQTT_HOST" -p "$MQTT_PORT" \
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

poll_light_sensor &
LIGHT_PID=$!

/root/mosquitto_sub -h "$MQTT_HOST" -p "$MQTT_PORT" \
  -t edge/stream/start \
  -t edge/stream/stop \
  -t edge/buzzer/on \
  -t edge/buzzer/off \
  -t edge/led/blink \
  -t edge/camera/adjust -v | \
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
        edge/camera/adjust)
            gamma=$(echo "$payload" | sed 's/.*"gamma":\([0-9.]*\).*/\1/')
            camera_adjust "$gamma"
            ;;
        *)
            log "unknown topic: $topic payload: $payload"
            ;;
    esac
done
