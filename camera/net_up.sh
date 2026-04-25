#!/bin/sh

ETH_DEV="${ETH_DEV:-eth0}"
ETH_IP="${ETH_IP:-192.0.2.2/24}"

echo "[net_up] configuring ${ETH_DEV} -> ${ETH_IP}"

ip addr flush dev "$ETH_DEV"
ip link set "$ETH_DEV" up
sleep 1
ip addr add "$ETH_IP" dev "$ETH_DEV"

ip addr show "$ETH_DEV"
