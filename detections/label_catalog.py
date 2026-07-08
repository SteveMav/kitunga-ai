from __future__ import annotations

from decimal import Decimal

MODEL_LABELS = [
    "1-5-Volt-Battery",
    "3-3-Volt-Battery",
    "7-Segment-Display",
    "9-Volt-Battery",
    "Arduino-Mega",
    "Arduino-Nano",
    "Arduino-Uno",
    "BJT-Transistor",
    "Bluetooth-Module",
    "Breadboard",
    "Bridge-Rectifier",
    "Buck-Converter",
    "Buzzer",
    "Capacitor-10mf",
    "Capacitor-470mf",
    "DC-Motor",
    "Diode",
    "ESP32",
    "ESP32-CAM",
    "FT-232-USB-Serial-Module",
    "Film-Capacitor",
    "Fuse",
    "Fuse-Base",
    "GSM-Module",
    "Gas-Sensor",
    "Heat-Sink",
    "High-Voltage-Ceramic-Capacitor",
    "Humidity-Sensor",
    "IC-Base-14-Pin",
    "IC-Base-28-Pin",
    "IC-Chip",
    "IGBT",
    "IR-Sensor",
    "Inductor",
    "Keypad",
    "LCD-Display",
    "LDR-Sensor",
    "LED-Light",
    "Low-Voltage-Ceramic-Capacitor",
    "MLC-Capacitor",
    "MOSFET",
    "Motion-Sensor",
    "Motor-Driver",
    "NTC-Thermistor",
    "OLED-Display",
    "Pin-Header",
    "Push-Switch",
    "RFID-Scanner",
    "Raindrops-Module",
    "Relay-Module",
    "Resistor",
    "Rocker-Switch",
    "Servo-Motor",
    "Soil-Moisture-Sensor",
    "Sonar-Sensor",
    "TCRT5000",
    "Tact-Switch",
    "Taper-Potentiometer",
    "Trimmer-Potentiometer",
    "Water-Sensor",
    "Zener-Diode",
]

LEGACY_LABEL_RENAMES = {
    "breadboard_830": "breadboard",
    "esp32_devkit": "esp32",
    "hc_sr04": "sonar_sensor",
    "relay_module_1ch": "relay_module",
    "servo_sg90": "servo_motor",
}

FRIENDLY_OVERRIDES = {
    "arduino_uno": {
        "name": "Arduino Uno",
        "category": "Microcontroleur",
        "price": Decimal("15.00"),
        "stock_quantity": 10,
    },
    "arduino_nano": {
        "name": "Arduino Nano",
        "category": "Microcontroleur",
        "price": Decimal("10.00"),
        "stock_quantity": 8,
    },
    "arduino_mega": {
        "name": "Arduino Mega",
        "category": "Microcontroleur",
        "price": Decimal("22.00"),
        "stock_quantity": 5,
    },
    "esp32": {
        "name": "ESP32 DevKit",
        "category": "Microcontroleur",
        "price": Decimal("9.50"),
        "stock_quantity": 14,
    },
    "esp32_cam": {
        "name": "ESP32-CAM",
        "category": "Microcontroleur",
        "price": Decimal("11.00"),
        "stock_quantity": 6,
    },
    "breadboard": {
        "name": "Breadboard 830 points",
        "category": "Prototypage",
        "price": Decimal("4.00"),
        "stock_quantity": 12,
    },
    "relay_module": {
        "name": "Module relais",
        "category": "Module",
        "price": Decimal("2.75"),
        "stock_quantity": 6,
    },
    "servo_motor": {
        "name": "Servo moteur SG90",
        "category": "Actionneur",
        "price": Decimal("5.00"),
        "stock_quantity": 8,
    },
    "sonar_sensor": {
        "name": "Capteur ultrason HC-SR04",
        "category": "Capteur",
        "price": Decimal("3.00"),
        "stock_quantity": 18,
    },
}


def normalize_label(label: str) -> str:
    normalized = label.strip().lower()
    for char in (" ", "-", ".", "/"):
        normalized = normalized.replace(char, "_")
    while "__" in normalized:
        normalized = normalized.replace("__", "_")
    return normalized.strip("_")


def canonical_label_for_model_label(model_label: str) -> str:
    return normalize_label(model_label)


def friendly_name(model_label: str) -> str:
    return model_label.replace("-", " ")


def infer_category(label: str) -> str:
    if "arduino" in label or label.startswith("esp32") or "ic_" in label:
        return "Microcontroleur"
    if "sensor" in label or "ldr" in label or "tcrt" in label:
        return "Capteur"
    if "motor" in label or "buzzer" in label or "relay" in label:
        return "Actionneur"
    if "display" in label or "keypad" in label or "switch" in label:
        return "Interface"
    if "capacitor" in label or "resistor" in label or "diode" in label or "transistor" in label:
        return "Composant"
    if "battery" in label or "converter" in label or "fuse" in label:
        return "Alimentation"
    if "breadboard" in label or "pin_header" in label:
        return "Prototypage"
    return "Module"


def default_price_for_category(category: str) -> Decimal:
    prices = {
        "Microcontroleur": Decimal("10.00"),
        "Capteur": Decimal("3.00"),
        "Actionneur": Decimal("5.00"),
        "Interface": Decimal("4.00"),
        "Composant": Decimal("0.50"),
        "Alimentation": Decimal("2.50"),
        "Prototypage": Decimal("2.00"),
        "Module": Decimal("3.50"),
    }
    return prices.get(category, Decimal("3.00"))


def product_defaults_for_model_label(model_label: str) -> dict:
    detection_label = canonical_label_for_model_label(model_label)
    override = FRIENDLY_OVERRIDES.get(detection_label, {})
    category = override.get("category", infer_category(detection_label))
    return {
        "name": override.get("name", friendly_name(model_label)),
        "category": category,
        "detection_label": detection_label,
        "price": override.get("price", default_price_for_category(category)),
        "currency": "USD",
        "stock_quantity": override.get("stock_quantity", 5),
        "is_active": True,
    }
