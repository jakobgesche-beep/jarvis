#!/bin/bash
# Installiert den LaunchAgent für das tägliche Morgen-Briefing um 08:00

PLIST_PATH="$HOME/Library/LaunchAgents/com.jarvis.morning.plist"
JARVIS_PATH="$HOME/jarvis"

cat > "$PLIST_PATH" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jarvis.morning</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$JARVIS_PATH/scripts/morning_briefing.sh</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Hour</key>
        <integer>8</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>$JARVIS_PATH/data/morning.log</string>
    <key>StandardErrorPath</key>
    <string>$JARVIS_PATH/data/morning_error.log</string>
</dict>
</plist>
EOF

launchctl load "$PLIST_PATH"
echo "✅ LaunchAgent installiert – Jarvis weckt dich täglich um 08:00"
