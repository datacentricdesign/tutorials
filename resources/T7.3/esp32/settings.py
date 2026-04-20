settings = {
    # ------------------------------------------------------------------
    # WiFi
    # ------------------------------------------------------------------
    # The name (SSID) of the WiFi network you want to connect to.
    # On the TU Delft campus use "TUD-facility".
    "ssid": "TUD-facility",

    # The WiFi password for your device.
    # On campus this is the password registered for your device in the
    # TU Delft network portal — it is not your personal NetID password.
    "password": "your-wifi-password",

    # ------------------------------------------------------------------
    # Data Foundry
    # ------------------------------------------------------------------
    # The device ID assigned to this actuator in Data Foundry.
    # Find it in your project under Sources > your device.
    "device_id": "your-device-id",

    # The OOCSI channel this actuator listens on for trigger events.
    # Must match the ACTUATOR_CHANNEL constant in Data Foundry script
    "oocsi_actuator_channel": "your-esp32-channel",

    # ------------------------------------------------------------------
    # OOCSI server — do not change
    # ------------------------------------------------------------------
    "oocsi_base": "oocsi.id.tue.nl",
}
