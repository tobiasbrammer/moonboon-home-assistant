# Moonboon Motor Connect for Home Assistant

This custom integration provides five action buttons for the Motor Connect
Basic: Low (15), Medium (50), High (100), Start, and Stop. The commands were
captured from the Moonboon iPhone app and the three speeds were verified with
the local Mac controller. It connects locally over Bluetooth; no Moonboon
account or cloud service is used.

The integration can connect directly through a Home Assistant Bluetooth adapter
or through the included Raspberry Pi gateway. The Pi gateway has been tested on
Raspberry Pi OS with Home Assistant OS on the same LAN.

## Install with HACS

1. In HACS, add `https://github.com/tobiasbrammer/moonboon-home-assistant` as a custom
   **Integration** repository, then download Moonboon Motor Connect.
2. Restart Home Assistant so it loads the new custom integration.
3. Use a Bluetooth adapter or an ESPHome Bluetooth proxy that supports active
   connections near the motor, or set up the Pi gateway below. A Zigbee dongle
   cannot provide Bluetooth.
4. Disconnect the Moonboon iPhone app, power on the motor, and press its
   Bluetooth button once. In Settings > Devices & services, add or confirm
   Moonboon Motor Connect. Do not hold the button for 10 seconds, which resets
   the motor.
5. Press Low, Medium, or High in the device page. Start and Stop are separate
   buttons. Test with an empty cradle before using automations.

The motor accepts one active Bluetooth client at a time. If a button reports a
connection error, close the iPhone app and retry. The integration releases its
connection after each command. The buttons are actions rather than state
entities because the captured protocol does not provide reliable ongoing state.

## Raspberry Pi gateway

The gateway uses the Pi's own Bluetooth radio. Install it on a Pi running
Raspberry Pi OS with BlueZ and Python 3.11 or newer:

```sh
sudo install -d -o "$USER" -g "$USER" /opt/moonboon-gateway
mkdir -p /opt/moonboon-gateway/custom_components/moonboon
cp -R pi_gateway /opt/moonboon-gateway/
cp custom_components/moonboon/const.py custom_components/moonboon/protocol.py \
  /opt/moonboon-gateway/custom_components/moonboon/
python3 -m venv /opt/moonboon-gateway/.venv
/opt/moonboon-gateway/.venv/bin/pip install bleak==2.1.1
sudo install -m 644 pi_gateway/moonboon-gateway.service \
  /etc/systemd/system/moonboon-gateway.service
sudo systemctl daemon-reload
sudo systemctl enable --now moonboon-gateway
```

The service file assumes the Pi has address `192.168.1.10`, Home Assistant has
address `192.168.1.9`, and the Pi user is `pi`. Adjust these before installing
on a different LAN. The gateway only accepts HTTP requests from the Home
Assistant IP and binds to the Pi's LAN IP. Restrict port 8765 to the trusted LAN.
In Home Assistant, add Moonboon Motor Connect and enter the Pi IP address.
The gateway can be configured while the motor is out of range; commands will
report that the motor was not found until it advertises nearby.

Only the decoded command format is included in this repository. Full Bluetooth
captures may contain unrelated traffic and should remain private.
