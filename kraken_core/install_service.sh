#!/bin/bash
echo "Installing KRAKEN as a background systemd service..."

# Copy service file to systemd
sudo cp kraken.service /etc/systemd/system/

# Reload systemd and enable/start Kraken
sudo systemctl daemon-reload
sudo systemctl enable kraken
sudo systemctl start kraken

echo "--------------------------------------------------------"
echo "✅ KRAKEN is now running in the background!"
echo "It will automatically start if the Oracle VM reboots."
echo ""
echo "Useful Commands:"
echo "View live engine logs:  sudo journalctl -u kraken -f"
echo "Check system status:    sudo systemctl status kraken"
echo "Stop the engine:        sudo systemctl stop kraken"
echo "Restart the engine:     sudo systemctl restart kraken"
echo "--------------------------------------------------------"
