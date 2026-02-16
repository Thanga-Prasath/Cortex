#!/bin/bash
# Sunday Voice Assistant - Permission Repair Script
# This script handles permission issues and group memberships for Linux systems.

echo "==================================="
echo "Sunday - Permission Repair Tool"
echo "==================================="

# Get current user and home
CURRENT_USER=$(whoami)
PROJECT_DIR=$(pwd)

echo "[1/3] Checking group memberships..."

# Add user to audio and video groups if not already there
GROUPS=("audio" "video" "plugdev")
for grp in "${GROUPS[@]}"; do
    if getent group "$grp" > /dev/null; then
        if id -G -n "$CURRENT_USER" | grep -qw "$grp"; then
            echo "✅ User is already in '$grp' group."
        else
            echo "🔧 Adding user to '$grp' group..."
            sudo usermod -aG "$grp" "$CURRENT_USER"
            NEED_REBOOT=true
        fi
    else
        echo "⚠️  Group '$grp' does not exist on this system. Skipping."
    fi
done

echo ""
echo "[2/3] Generating sudoers configuration..."

# Define the commands the assistant needs to run without password
SUDOERS_FILE="/etc/sudoers.d/sunday-assistant"
TEMP_SUDOERS="./sunday-assistant.tmp"

# Create a temporary file with the rules
cat << EOF > "$TEMP_SUDOERS"
# Sunday Voice Assistant - Sudoers Rules
# Automatically generated on $(date)
$CURRENT_USER ALL=(ALL) NOPASSWD: /usr/sbin/ufw, /usr/bin/nmcli, /usr/sbin/shutdown, /usr/sbin/reboot, /usr/bin/apt, /usr/bin/apt-get
EOF

echo "Rules created in $TEMP_SUDOERS"
echo "To apply these rules, run:"
echo "sudo cp $TEMP_SUDOERS $SUDOERS_FILE && sudo chmod 0440 $SUDOERS_FILE"
echo ""

read -p "Would you like to apply these sudoers rules now? (y/n): " APPLY_SUDOERS
if [[ "$APPLY_SUDOERS" == "y" || "$APPLY_SUDOERS" == "Y" ]]; then
    sudo cp "$TEMP_SUDOERS" "$SUDOERS_FILE"
    sudo chmod 0440 "$SUDOERS_FILE"
    rm "$TEMP_SUDOERS"
    echo "✅ Sudoers rules applied successfully."
else
    echo "❌ Sudoers rules NOT applied. You may experience permission errors."
fi

echo ""
echo "[3/4] Fixing local binary permissions..."

# Make sure project's internal binaries are executable
if [ -d "$PROJECT_DIR/piper_engine/piper" ]; then
    echo "🔧 Setting execution permissions for Piper engine..."
    chmod +x "$PROJECT_DIR"/piper_engine/piper/piper 2>/dev/null
    chmod +x "$PROJECT_DIR"/piper_engine/piper/espeak-ng 2>/dev/null
    chmod +x "$PROJECT_DIR"/piper_engine/piper/piper_phonemize 2>/dev/null
    echo "✅ Project binaries are now executable."
fi

echo ""
echo "[4/4] Finalizing..."

if [ "$NEED_REBOOT" = true ]; then
    echo "⚠️  Important: You may need to logout and log back in (or reboot) for group changes to take effect."
fi

echo "==================================="
echo "✅ Permission repair complete!"
echo "==================================="
