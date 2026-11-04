#!/usr/bin/env bash
# 创建 /etc/security 目录并写入占位 whitelist 配置
mkdir -p /etc/security
echo "# placeholder whitelist" > /etc/security/whitelist.conf
chmod 640 /etc/security/whitelist.conf