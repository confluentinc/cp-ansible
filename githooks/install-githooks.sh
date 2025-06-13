#!/bin/bash

echo "installing repository githooks to $(git config core.hookspath)"

sudo cp -n prepare-commit-msg "$(git config core.hookspath)"
sudo chmod +x "$(git config core.hookspath)prepare-commit-msg"

echo "githooks installed"
