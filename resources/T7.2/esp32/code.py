# =============================================================================
# Solar generation probe — Connected Interaction Kit
# =============================================================================
# Reads light intensity from a photoresistor and sends each reading to Data
# Foundry over WiFi using the OOCSI messaging protocol.
#
# The photoresistor acts as a proxy for solar irradiance: it cannot measure
# watts per square metre, but it captures the relative rhythm of the sun —
# clouds passing, day length, window orientation — which is what the probe
# is designed to make tangible to participants.
#
# Before running this file:
#   1. Assemble the photoresistor custom component and plug its Grove connector
#      into the A2 port on the BitsyExpander.
#      Guide: https://id-studiolab.github.io/Connected-Interaction-Kit/
#             tutorials/assembling-custom-components/photoresistor
#   2. Edit settings.py with your WiFi credentials, Data Foundry device ID,
#      and chosen OOCSI topic.
#   3. Make sure the OOCSI topic in settings.py matches the one you entered
#      in your Data Foundry IoT Dataset configuration.
# =============================================================================


# --- Imports ------------------------------------------------------------------
# These lines load the libraries this program depends on.
# The libraries live in the lib/ folder on the CIRCUITPY drive.

import time       # used to pause between readings
import board      # provides the pin names for this board
import busio      # used to set up the SPI bus for the WiFi co-processor
import digitalio  # used to control individual digital pins
import analogio   # used to read the analog voltage from the photoresistor

from adafruit_esp32spi import adafruit_esp32spi   # WiFi co-processor driver
from oocsi_esp32spi import OOCSI                  # OOCSI messaging client

# Load your personal settings (WiFi credentials, device ID, topic, etc.)
from settings import settings


# --- Hardware setup -----------------------------------------------------------
# Tell the board how the ESP32 WiFi co-processor is wired up.
# These pin numbers are fixed by the BitsyExpander hardware — do not change them.
esp32_cs    = digitalio.DigitalInOut(board.D9)
esp32_ready = digitalio.DigitalInOut(board.D11)
esp32_reset = digitalio.DigitalInOut(board.D12)
spi         = busio.SPI(board.SCK, board.MOSI, board.MISO)

# Photoresistor on analog pin A2 (fixed by the Custom Component Board).
# The component board wires the photoresistor and a 10 kΩ resistor as a
# voltage divider: more light → lower photoresistor resistance → higher
# voltage at A2 → higher ADC reading.
# The ADC returns a 16-bit integer: 0 (no light) to 65535 (full scale).
photo_resistor = analogio.AnalogIn(board.A2)


# --- Connect to WiFi ----------------------------------------------------------
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("ESP32 WiFi module found.")
    print("Firmware version:", str(esp.firmware_version, "utf-8"))

# Scan for available networks and check that the one in settings.py is visible.
print("\nScanning for WiFi networks...")
network_list = [str(ap.ssid, "utf-8") for ap in esp.scan_networks()]
if settings["ssid"] not in network_list:
    print("Network not found:", settings["ssid"])
    print("Available networks:", network_list)
    print("Check the 'ssid' value in settings.py and try again.")
    raise SystemExit(0)

# Try to connect, retrying automatically if the first attempt fails.
print("Connecting to", settings["ssid"], "...")
while not esp.is_connected:
    try:
        esp.connect_AP(settings["ssid"], settings["password"])
    except (RuntimeError, ConnectionError) as e:
        print("Connection failed:", e)
        print("Retrying...")
        continue

print("Connected! IP address:", esp.pretty_ip(esp.ip_address))


# --- Connect to OOCSI ---------------------------------------------------------
# OOCSI is the messaging system that carries sensor data to Data Foundry.
# The device_id identifies this probe on the network.
print("\nConnecting to OOCSI...")
oocsi = OOCSI(settings["device_id"], settings["oocsi_base"], esp)


# --- Main loop ----------------------------------------------------------------
# This loop runs forever. Each iteration:
#   1. Reads the raw ADC value from the photoresistor.
#   2. Normalises it to a 0–100 generation index.
#   3. Packages both values into a message with metadata.
#   4. Sends the message to Data Foundry via OOCSI.
#   5. Waits before taking the next reading.
print("Sending data to Data Foundry on topic:", settings["oocsi_topic"])

# ADC full scale is 65535 (16-bit). Typical ranges in practice:
#   Bright outdoor sun:      50000–65535
#   Window, sunny day:       20000–50000
#   Window, overcast:         5000–20000
#   Indoors away from window:    0–5000
#
# If your deployment location never approaches 65535, lower MAX_LIGHT to the
# maximum you observed in bench testing — this spreads the generation index
# across the actual range and improves sensitivity.
MAX_LIGHT = 65535

while True:
    # Read the raw photoresistor ADC value (0–65535).
    raw_light = photo_resistor.value

    # Normalise to a 0–100 generation index.
    # This is a relative proxy, not a calibrated solar irradiance measurement.
    generation_index = min(100, int(raw_light / MAX_LIGHT * 100))

    print(f"raw_light={raw_light}  generation_index={generation_index}")

    # Build the message. Every key becomes a column in the Data Foundry dataset.
    message = {
        "device_id":        settings["device_id"],   # identifies which probe sent this
        "activity":         settings["activity"],    # study phase label from settings.py
        "raw_light":        raw_light,               # raw ADC reading (0–65535)
        "generation_index": generation_index,        # normalised index (0–100)
    }

    # Send the message to the OOCSI topic configured in settings.py.
    # Data Foundry is subscribed to that topic and stores the message
    # with a server-side timestamp automatically.
    oocsi.send(settings["oocsi_topic"], message)

    # Wait before taking the next reading.
    # The pause length is set by collection_frequency in settings.py.
    time.sleep(settings["collection_frequency"])
