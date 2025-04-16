#!/bin/bash

SDR_IFACE=$(ifconfig | grep -B1 192.168..0.1 | grep -o "^\w*")

# set all cores to performance
sudo apt install -y cpufrequtils
for ((i=0;i<$(nproc);i++)); do
    sudo cpufreq-set -c $i -r -g performance
done

# some other network tuning
sudo sysctl -w net.core.wmem_max=62500000
sudo sysctl -w net.core.rmem_max=62500000
sudo sysctl -w net.core.wmem_default=62500000
sudo sysctl -w net.core.rmem_default=62500000
sudo ethtool -G $SDR_IFACE tx 4096 rx 4096

# MTU update
sudo ifconfig $SDR_IFACE mtu 9000
