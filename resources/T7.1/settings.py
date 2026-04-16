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
    # The device ID assigned to your probe in Data Foundry.
    # Find it in your project under Sources > your device.
    "device_id": "your-device-id",

    # The OOCSI channel this probe publishes to.
    # Choose any name — slashes create a hierarchy, e.g. "/study/kitchen".
    # This must match the channel you configured in the Data Foundry
    # IoT Dataset page under Configuration > Data from OOCSI.
    "oocsi_topic": "/study/living-room",

    # A label that is stored alongside every data point.
    # Change this between study phases to mark them in your dataset,
    # for example "BASELINE", "INTERVENTION", or "WASHOUT".
    "activity": "MEASURING",

    # ------------------------------------------------------------------
    # Sampling
    # ------------------------------------------------------------------
    # How many seconds to wait between readings.
    # 1 = one reading per second, 10 = one reading every 10 seconds.
    "collection_frequency": 1,

    # ------------------------------------------------------------------
    # OOCSI server — do not change
    # ------------------------------------------------------------------
    "oocsi_base": "oocsi.id.tue.nl",
}
