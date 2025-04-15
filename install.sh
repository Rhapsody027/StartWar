#!/bin/bash

set -e

echo "==> 初始化開發環境"

# 偵測作業系統
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
  echo "==> 偵測到 Linux/WSL 環境"
  bash packages/ubuntu.sh
else
  echo "==> 尚未支援此系統：$OSTYPE"
  exit 1
fi

# 建立 symlink
bash bootstrap.sh

echo "==> 所有設定已完成！重新開一個 terminal 試試吧 🙌"
