#!/bin/bash
# Cloudflare Tunnel Setup für JARVIS
# Einmalig ausführen – danach startet der Tunnel automatisch beim Mac-Login
set -e

echo "=== JARVIS Cloudflare Tunnel Setup ==="
echo ""

# 1. cloudflared installieren
if ! command -v cloudflared &>/dev/null; then
  echo "Installiere cloudflared..."
  brew install cloudflare/cloudflare/cloudflared
else
  echo "✓ cloudflared bereits installiert"
fi

# 2. Authentifizierung
echo ""
echo "Melde dich bei Cloudflare an:"
cloudflared tunnel login

# 3. Tunnel erstellen
echo ""
echo "Erstelle Tunnel 'jarvis'..."
cloudflared tunnel create jarvis

# Tunnel-ID auslesen
TUNNEL_ID=$(cloudflared tunnel list | grep jarvis | awk '{print $1}')
echo "Tunnel-ID: $TUNNEL_ID"

# 4. Konfiguration erstellen
CONFIG_DIR="$HOME/.cloudflared"
mkdir -p "$CONFIG_DIR"

cat > "$CONFIG_DIR/config.yml" << EOF
tunnel: $TUNNEL_ID
credentials-file: $CONFIG_DIR/$TUNNEL_ID.json

ingress:
  - service: http://localhost:8080
EOF

echo "✓ Konfiguration: $CONFIG_DIR/config.yml"

# 5. DNS Route (optional – wenn du eine eigene Domain hast)
echo ""
echo "Willst du eine eigene Domain verwenden? (y/N)"
read -r USE_DOMAIN
if [[ "$USE_DOMAIN" == "y" || "$USE_DOMAIN" == "Y" ]]; then
  echo "Domain eingeben (z.B. jarvis.meinname.de):"
  read -r DOMAIN
  cloudflared tunnel route dns jarvis "$DOMAIN"
  echo "✓ DNS für $DOMAIN eingerichtet"
else
  echo "Kein eigener Domain – Cloudflare generiert eine *.cfargotunnel.com URL"
fi

# 6. Als macOS LaunchAgent einrichten (startet automatisch beim Login)
PLIST="$HOME/Library/LaunchAgents/com.jarvis.tunnel.plist"
cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jarvis.tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/local/bin/cloudflared</string>
        <string>tunnel</string>
        <string>run</string>
        <string>jarvis</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$HOME/jarvis/data/tunnel.log</string>
    <key>StandardErrorPath</key>
    <string>$HOME/jarvis/data/tunnel.log</string>
</dict>
</plist>
EOF

launchctl load "$PLIST"
echo "✓ LaunchAgent installiert – Tunnel startet automatisch beim Login"

# 7. Tunnel-URL anzeigen
echo ""
echo "========================================"
echo "✅ Setup abgeschlossen!"
echo ""
echo "Dein Tunnel läuft. URL auf Cloudflare Dashboard prüfen:"
echo "  https://one.dash.cloudflare.com → Networks → Tunnels → jarvis"
echo ""
echo "Nächste Schritte:"
echo "  1. API Token in .env setzen: JARVIS_API_TOKEN=dein-geheimer-token"
echo "  2. Tunnel-URL + Token in der iPhone PWA eingeben"
echo "  3. python main.py starten"
echo "========================================"
