#!/bin/bash

# Deactivate any existing virtual environment
if [[ -n "${VIRTUAL_ENV}" ]]; then
    deactivate
fi

# Temporarily remove pyenv from PATH to avoid conflicts
export PATH_BACKUP="$PATH"
export PATH=$(echo "$PATH" | sed 's|/Users/rickylenon/.pyenv/shims:||g')
export PATH=$(echo "$PATH" | sed 's|/Users/rickylenon/.pyenv/bin:||g')

# Activate the virtual environment
source venv/bin/activate

# Verify the correct Python is being used
echo "✅ Virtual environment activated"
echo "Python path: $(which python)"
echo "Python version: $(python --version)"
echo "Virtual env: $VIRTUAL_ENV"

# Add a function to restore PATH if needed
restore_path() {
    export PATH="$PATH_BACKUP"
    echo "Original PATH restored"
}

echo "Note: Run 'restore_path' if you need to restore original PATH"
