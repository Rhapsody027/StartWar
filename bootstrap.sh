#!/bin/bash

# Define the path to your dotfiles
DOTFILES_DIR="$HOME/startwar/dotfiles"

# Function to create symbolic links
create_symlink() {
  source="$1"
  target="$2"
  if [ ! -e "$target" ]; then
    ln -s "$source" "$target"
    echo "Created symlink: $source -> $target"
  else
    echo "Target already exists: $target"
  fi
}

# Create symbolic links for dotfiles
create_symlink "$DOTFILES_DIR/.zshrc" "$HOME/.zshrc"
create_symlink "$DOTFILES_DIR/.vimrc" "$HOME/.vimrc"

# Install Oh My Zsh if not installed
if [ ! -d "$HOME/.oh-my-zsh" ]; then
  echo "Installing Oh My Zsh..."
  sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
fi

# Setup plugins (example for zsh-syntax-highlighting)
if [ ! -d "$HOME/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting" ]; then
  echo "Installing zsh-syntax-highlighting plugin..."
  git clone https://github.com/zsh-users/zsh-syntax-highlighting.git "$HOME/.oh-my-zsh/custom/plugins/zsh-syntax-highlighting"
fi

# Additional setup steps can go here...

echo "Dotfile setup completed!"
