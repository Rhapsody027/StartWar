# Quick Setup

這是一個簡單的環境設置工具，用來自動化安裝開發環境及配置 dotfiles。支持多平台（Linux 和 macOS），並自動設置 Zsh、Vim、tmux 等常見開發工具，並同步你的個人配置。

## 功能

- 自動安裝開發工具和常用套件
- 自動設定 dotfiles（`.zshrc`、`.vimrc` 等）
- 支援 Oh My Zsh 和 Powerlevel10k
- 自動安裝 Neovim、Lazygit 和其他 CLI 工具
- 預設選項自動處理作業系統（Linux/macOS）
- 手動安裝指令指南，適用於自動安裝失敗的情況

## 安裝流程

### 使用安裝腳本（推薦）

1. **下載或克隆此專案：**

   ```bash
   git clone https://github.com/Rhapsody027/StartWar.git
   cd StartWar
   ```

2. **執行 `install.sh` 安裝腳本：**

   `install.sh` 會根據你所使用的作業系統（macOS 或 Ubuntu）自動安裝所需工具和配置檔案。

   ```bash
   bash install.sh
   ```

   這個過程會：
   - 偵測作業系統
   - 安裝常用的 CLI 工具
   - 安裝並設定 Zsh 和相關插件
   - 設定你的 dotfiles（`.zshrc`, `.tmux.conf`, 等）
   
3. **安裝完成後**，你可以重新啟動終端機，並檢查安裝是否成功。

---

### 手動安裝指令

如果自動安裝過程中發生錯誤，或者你希望手動安裝，請按照以下步驟操作。

#### 1. 更新套件列表並安裝必要工具

- **Ubuntu 系統：**

   ```bash
   sudo apt update
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
   ```

- **macOS 系統：**

   如果你使用 macOS，可以透過 Homebrew 安裝所需工具：

   ```bash
   brew install \
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
     python3 \
     lsd \
     jq \
     playerctl \
     g++ \
     python3-dev
   ```

#### 2. 安裝 Neovim（如果未安裝）

- **Ubuntu 系統：**

   ```bash
   sudo apt install -y neovim
   ```

- **macOS 系統：**

   ```bash
   brew install neovim
   ```

#### 3. 安裝 Oh My Zsh（如果未安裝）

如果你尚未安裝 Oh My Zsh，可以透過以下命令安裝：

```bash
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

#### 4. 安裝 Powerlevel10k（如未安裝）

Powerlevel10k 是一款非常受歡迎的 Zsh 主題，可以提供美觀且功能豐富的提示符。安裝方法：

```bash
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git \
  ~/.oh-my-zsh/custom/themes/powerlevel10k
```

#### 5. 手動設定 dotfiles

如果 `bootstrap.sh` 沒有自動創建 symlink，你可以手動創建 symlink：

```bash
ln -s ~/path/to/dotfiles/.zshrc ~/.zshrc
ln -s ~/path/to/dotfiles/.vimrc ~/.vimrc
ln -s ~/path/to/dotfiles/.tmux.conf ~/.tmux.conf
ln -s ~/path/to/dotfiles/.gitconfig ~/.gitconfig
```

#### 6. 安裝 Lazygit（如未安裝）

```bash
sudo add-apt-repository ppa:lazygit-team/release -y
sudo apt update
sudo apt install lazygit
```

### 補充：如何將 Zsh 設為預設 Shell

若你希望將 Zsh 設為預設 shell，請運行以下命令：

```bash
chsh -s $(which zsh)
```

---

## 常見問題

### 1. 安裝過程中沒有安裝某些套件，該怎麼辦？

請參考上面的手動安裝指令，根據你的作業系統手動安裝缺少的套件。

### 2. 如何重設 dotfiles？

若你需要重設 dotfiles，可以直接刪除現有的 symlink，然後重新執行 `bootstrap.sh`：

```bash
rm ~/.zshrc
rm ~/.vimrc
rm ~/.tmux.conf
rm ~/.gitconfig
bash bootstrap.sh
```
