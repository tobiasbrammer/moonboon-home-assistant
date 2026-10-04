# Moonboon Motor Connect for Home Assistant

This custom integration provides five action buttons for the Motor Connect
Basic: Low (15), Medium (50), High (100), Start, and Stop. The commands were
captured from the Moonboon iPhone app and the three speeds were verified with
the local Mac controller. It connects locally over Bluetooth; no Moonboon
account or cloud service is used.

The Home Assistant Bluetooth path is ready for a pilot but has not yet been
tested against a live Home Assistant adapter or proxy.

## Install with HACS

1. In HACS, add `https://github.com/tobiasbrammer/moonboon-home-assistant` as a custom
   **Integration** repository, then download Moonboon Motor Connect.
2. Restart Home Assistant so it loads the new custom integration.
3. Add a Bluetooth adapter or an ESPHome Bluetooth proxy that supports active
   connections near the motor. A Zigbee dongle cannot provide Bluetooth.
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

Only the decoded command format is included in this repository. Full Bluetooth
captures may contain unrelated traffic and should remain private.
