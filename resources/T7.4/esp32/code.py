# =============================================================================
# Sedentary alert actuator — Connected Interaction Kit
# =============================================================================
# Listens on an OOCSI channel for sedentary_alert events sent by the Data
# Foundry script, and responds with a gentle vibration pattern.
#
# Before running this file:
#   1. Edit settings.py with your WiFi credentials, Data Foundry device ID,
#      and chosen OOCSI channel.
#   2. Make sure the oocsi_actuator_channel in settings.py matches
#      ACTUATOR_CHANNEL in the Data Foundry script.
#   3. Connect the vibration motor to the Grove connector on pin D4.
# =============================================================================


# --- Imports ------------------------------------------------------------------

import asyncio
import random
import time
import board
import busio
import digitalio

from adafruit_esp32spi import adafruit_esp32spi
from oocsi_esp32spi import OOCSI

from settings import settings


# --- Hardware setup -----------------------------------------------------------
# ESP32 WiFi co-processor — pins are fixed by the BitsyExpander hardware.
esp32_cs    = digitalio.DigitalInOut(board.D9)
esp32_ready = digitalio.DigitalInOut(board.D11)
esp32_reset = digitalio.DigitalInOut(board.D12)
spi         = busio.SPI(board.SCK, board.MOSI, board.MISO)

# Built-in LED on D13 — used as a heartbeat indicator while the device is running.
led = digitalio.DigitalInOut(board.D13)
led.direction = digitalio.Direction.OUTPUT

# Vibration motor connected via Grove connector to pin D4.
vibration_motor = digitalio.DigitalInOut(board.D4)
vibration_motor.direction = digitalio.Direction.OUTPUT
vibration_motor.value = False  # motor off at startup


# --- Vibration pattern --------------------------------------------------------
# Three short pulses — noticeable without being startling.
# Adjust the sleep durations and loop count to change the pattern.

def vibrate_alert():
    for _ in range(3):
        vibration_motor.value = True
        time.sleep(0.2)
        vibration_motor.value = False
        time.sleep(0.2)


# --- OOCSI message handler ----------------------------------------------------
# Called each time a message arrives on the subscribed channel.
# The event dict contains the fields sent by the Data Foundry script:
#   event   – "sedentary_alert"
#   still_s – approximate seconds of continuous stillness that triggered this

def on_message(sender, _recipient, event):
    print("Message from", sender, "->", event)
    if event.get("event") == "sedentary_alert":
        print("Sedentary alert! Stillness duration:", event.get("still_s", 0), "s")
        vibrate_alert()


# --- Connect to WiFi ----------------------------------------------------------
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

if esp.status == adafruit_esp32spi.WL_IDLE_STATUS:
    print("\nESP32 WiFi module found.")
    print("Firmware version:", str(esp.firmware_version, "utf-8"))

print("\nScanning for available networks...")
network_list = [str(ap.ssid, "utf-8") for ap in esp.scan_networks()]
if settings["ssid"] not in network_list:
    print(settings["ssid"], "not found. Available networks:", network_list)
    print("Check the 'ssid' value in settings.py and try again.")
    raise SystemExit(0)

print(settings["ssid"], "found. Connecting...")
while not esp.is_connected:
    try:
        esp.connect_AP(settings["ssid"], settings["password"])
    except (RuntimeError, ConnectionError) as e:
        print("Connection failed:", e, "— retrying...")
        continue

print("Connected! IP address:", esp.pretty_ip(esp.ip_address))


# --- Connect to OOCSI and subscribe -------------------------------------------
# A random suffix is appended to the device ID to prevent name collisions when
# multiple instances run at the same time (e.g. during a workshop).
print("\nConnecting to OOCSI...")
client_name = settings["device_id"] + "-" + str(random.randint(1000, 9999))
oocsi = OOCSI(client_name, settings["oocsi_base"], esp)

oocsi.subscribe(settings["oocsi_actuator_channel"], on_message)
print("Listening on channel:", settings["oocsi_actuator_channel"])


# --- Async tasks --------------------------------------------------------------
# blink() pulses the built-in LED every second as a visual heartbeat,
# confirming the device is running and the event loop is alive.
# oocsi.keepAlive() drives the async OOCSI message loop.

async def blink():
    while True:
        led.value = True
        await asyncio.sleep(1)
        led.value = False
        await asyncio.sleep(1)

async def loop():
    asyncio.create_task(blink())
    await oocsi.keepAlive()

print("Ready. Waiting for sedentary alerts...")
asyncio.run(loop())
