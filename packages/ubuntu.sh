#!/bin/bash

set -e

echo "==> 初始化 Ubuntu CLI 開發環境"

# 更新套件清單
echo "==> 更新套件清單..."
sudo apt update

# 安裝基本工具
echo "==> 安裝常用 CLI 工具..."
sudo apt install -y \
  bat \
  btop \
  curl \
  fzf \
  ripgrep \
  tmux \
  vim \
  zsh \
  git \
  gh \
  npm \
  python3-pip \
  lsd \
  jq \
  playerctl \
  sudo \
  g++ \
  python3-dev \
  python3-venv \
  python3-wheel

# 安裝 Neovim（如尚未安裝）
if ! command -v nvim &>/dev/null; then
  echo "==> 安裝 Neovim..."
  sudo apt install -y neovim
fi

# 修正 batcat 符號鏈結（Ubuntu 系統需要）
if [ ! -e "/usr/bin/bat" ]; then
  echo "==> 建立 batcat 符號鏈結..."
  sudo ln -s /usr/bin/batcat /usr/bin/bat
fi

# 安裝 Oh My Zsh（如尚未安裝）
if [ ! -d "$HOME/.oh-my-zsh" ]; then
  echo "==> 安裝 Oh My Zsh..."
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
fi

# 安裝 Powerlevel10k（如尚未安裝）
if [ ! -d "$HOME/.oh-my-zsh/custom/themes/powerlevel10k" ]; then
  echo "==> 安裝 Powerlevel10k..."
  git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
    ~/.oh-my-zsh/custom/themes/powerlevel10k
fi

# 設定 ZSH 為預設 shell（如尚未設定）
if [ "$SHELL" != "$(which zsh)" ]; then
  echo "==> 設定 zsh 為預設 shell..."
  chsh -s "$(which zsh)"
fi

# 安裝 Lazygit（如尚未安裝）
if ! command -v lazygit &>/dev/null; then
  echo "==> 安裝 Lazygit..."
  sudo add-apt-repository ppa:lazygit-team/release -y
  sudo apt update
  sudo apt install -y lazygit
fi

# install LazyVim
if [ ! -d "$HOME/.config/nvim" ]; then
  echo "==> 安裝 LazyVim..."
  git clone https://github.com/LazyVim/starter ~/.config/nvim
  rm -rf ~/.config/nvim/.git
fi

echo "==> 所有設定與安裝完成 🎉"
echo "📦 請重新啟動 Terminal 或執行 'zsh' 以套用變更"
