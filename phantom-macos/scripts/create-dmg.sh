#!/bin/bash
# create-dmg.sh — Package Phantom.app into a DMG with drag-to-Applications layout

set -euo pipefail

APP_PATH="${1:?Usage: create-dmg.sh <path-to-Phantom.app>}"
DMG_NAME="${2:-Phantom.dmg}"
VOLUME_NAME="Phantom"

if [ ! -d "$APP_PATH" ]; then
    echo "Error: $APP_PATH not found"
    exit 1
fi

# Use create-dmg if available (brew install create-dmg)
if command -v create-dmg &>/dev/null; then
    create-dmg \
        --volname "$VOLUME_NAME" \
        --window-pos 200 120 \
        --window-size 600 400 \
        --icon-size 100 \
        --icon "Phantom.app" 150 190 \
        --app-drop-link 450 190 \
        --no-internet-enable \
        "$DMG_NAME" \
        "$APP_PATH"
else
    # Fallback: simple DMG creation
    TEMP_DIR=$(mktemp -d)
    cp -R "$APP_PATH" "$TEMP_DIR/"
    ln -s /Applications "$TEMP_DIR/Applications"
    hdiutil create -volname "$VOLUME_NAME" -srcfolder "$TEMP_DIR" -ov -format UDZO "$DMG_NAME"
    rm -rf "$TEMP_DIR"
fi

echo "Created $DMG_NAME"
