# =============================================================================
# Sensor probe — Connected Interaction Kit
# =============================================================================
# Reads distance from a VL53L0X Time-of-Flight sensor and sends each reading
# to Data Foundry over WiFi using the OOCSI messaging protocol.
#
# Before running this file:
#   1. Edit settings.py with your WiFi credentials, Data Foundry device ID,
#      and chosen OOCSI topic.
#   2. Make sure the OOCSI topic in settings.py matches the one you entered
#      in your Data Foundry IoT Dataset configuration.
# =============================================================================


# --- Imports ------------------------------------------------------------------
# These lines load the libraries this program depends on.
# The libraries live in the lib/ folder on the CIRCUITPY drive.

import time                              # used to pause between readings
import board                             # provides the pin names for this board
import busio                             # used to set up the I2C bus
import digitalio                         # used to control individual pins

from adafruit_esp32spi import adafruit_esp32spi   # WiFi co-processor driver
from oocsi_esp32spi import OOCSI                  # OOCSI messaging client
import adafruit_vl53l0x                           # VL53L0X distance sensor driver

# Load your personal settings (WiFi password, device ID, topic, etc.)
from settings import settings


# --- Hardware setup -----------------------------------------------------------
# Tell the board how the ESP32 WiFi co-processor is wired up.
# These pin numbers are fixed by the BitsyExpander hardware — do not change them.
esp32_cs    = digitalio.DigitalInOut(board.D9)
esp32_ready = digitalio.DigitalInOut(board.D11)
esp32_reset = digitalio.DigitalInOut(board.D12)
spi         = busio.SPI(board.SCK, board.MOSI, board.MISO)

# Set up the I2C bus that the distance sensor uses.
# SDA and SCL are the two wires of the Grove I2C connector.
i2c = busio.I2C(board.SCL, board.SDA)


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
# OOCSI is the messaging system that carries your sensor data to Data Foundry.
# The device_id identifies your probe on the network.
print("\nConnecting to OOCSI...")
oocsi = OOCSI(settings["device_id"], settings["oocsi_base"], esp)


# --- Set up the distance sensor -----------------------------------------------
# The sensor is connected via the Grove I2C port on the BitsyExpander.
dist_sensor = adafruit_vl53l0x.VL53L0X(i2c)


# --- Main loop ----------------------------------------------------------------
# This loop runs forever. Each iteration:
#   1. Reads the current distance from the sensor (in millimetres).
#   2. Packages it into a message with some metadata.
#   3. Sends the message to Data Foundry via OOCSI.
#   4. Waits before taking the next reading.
print("Sending data to Data Foundry on topic:", settings["oocsi_topic"])

while True:
    # Read the distance in millimetres.
    distance = dist_sensor.range

    print("Distance: ", distance, "mm")

    # Build the message. Every key here becomes a column in your Data Foundry
    # dataset, so name them to match what you want to see in your data table.
    message = {
        "device_id": settings["device_id"],   # identifies which probe sent this
        "activity":  settings["activity"],    # study phase label from settings.py
        "distance":  distance,                # the measured value in millimetres
    }

    # Send the message to the OOCSI topic configured in settings.py.
    # Data Foundry is subscribed to that topic and will store the message
    # with a timestamp automatically.
    oocsi.send(settings["oocsi_topic"], message)

    # Wait before taking the next reading.
    # The length of the pause is set by collection_frequency in settings.py.
    time.sleep(settings["collection_frequency"])
