import json
import csv
import os
import sys
import time
import argparse
import logging
import paho.mqtt.client as mqtt

# ----------------------------
# Configuration & Setup
# ----------------------------

parser = argparse.ArgumentParser(
    description="MQTT client to sync Zigbee2MQTT device list with inventory CSV."
)
parser.add_argument("--host", default="127.0.0.1", help="MQTT broker address")
parser.add_argument("--port", type=int, default=1883, help="MQTT broker port")
parser.add_argument("--username", default=None, help="MQTT username")
parser.add_argument("--password", default=None, help="MQTT password")
parser.add_argument("--inventory-file", dest="inventory", default="inventory.csv", help="Inventory CSV file")
parser.add_argument("--dry-run", action="store_true", help="Do not write CSV or publish MQTT messages")
args = parser.parse_args()

logging.basicConfig(level=logging.INFO, format="%(message)s")

META_FIELDS = ["ieee_address", "friendly_name", "manufacturer", "model_id"]
CSV_HEADER = ["disabled"] + META_FIELDS


# ----------------------------
# CSV Utilities
# ----------------------------

def load_inventory(filepath):
    if not os.path.exists(filepath):
        if args.dry_run:
            logging.info(f"[dry-run] Would create inventory file: {filepath}")
            return [], {}
        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(CSV_HEADER)
        return [], {}

    with open(filepath, newline="") as f:
        reader = csv.reader(f, delimiter=";")
        rows = [row for row in reader if row]

    header_index = {name: i for i, name in enumerate(CSV_HEADER)}
    inventory = {
        row[header_index["ieee_address"]]: {field: row[header_index[field]] for field in CSV_HEADER}
        for row in rows[1:]
    }
    return rows, inventory


def append_new_devices(filepath, rows, new_devices):
    if not new_devices:
        return

    if args.dry_run:
        for row in new_devices:
            logging.info(f"[dry-run] Would append device to inventory: {row}")
        return

    rows.extend(new_devices)
    with open(filepath, "w", newline="") as f:
        writer = csv.writer(f, delimiter=";")
        writer.writerows(rows)
    logging.info(f"Added {len(new_devices)} new device(s) to inventory.")


# ----------------------------
# Zigbee2MQTT Message Handler
# ----------------------------

def on_message(client, userdata, message):
    rows, inventory_db = load_inventory(args.inventory)
    header_index = {name: i for i, name in enumerate(CSV_HEADER)}

    # Parse incoming MQTT data
    try:
        devices = json.loads(message.payload)
    except json.JSONDecodeError:
        logging.error("Invalid JSON payload received.")
        return

    z2m_db = {
        dev["ieee_address"]: {k: dev[k] for k in META_FIELDS if k in dev}
        for dev in devices
    }

    # Detect unpaired devices
    for ieee, record in inventory_db.items():
        if ieee not in z2m_db and record["friendly_name"] != "Coordinator" and record["disabled"] == "":
            logging.info(f"Not paired: {record}")

    # Add new devices to inventory
    new_rows = []
    for ieee, record in z2m_db.items():
        if ieee not in inventory_db and record.get("friendly_name") != "Coordinator":
            new_row = [""] * len(CSV_HEADER)
            new_row[header_index["ieee_address"]] = ieee
            for field in META_FIELDS:
                if field in record:
                    new_row[header_index[field]] = record[field]
            new_rows.append(new_row)

    append_new_devices(args.inventory, rows, new_rows)

    # Rename mismatched devices
    for dev in devices:
        for row in rows[1:]:  # skip header
            if (
                dev["ieee_address"] == row[header_index["ieee_address"]] and
                dev["friendly_name"] != row[header_index["friendly_name"]]
            ):
                old = dev["friendly_name"]
                new = row[header_index["friendly_name"]]
                if args.dry_run:
                    logging.info(f"[dry-run] Would rename {old} to {new}")
                else:
                    logging.info(f"Renaming {old} to {new}")
                    client.publish(
                        "zigbee2mqtt/bridge/request/device/rename",
                        json.dumps({
                            "from": old,
                            "to": new,
                            "homeassistant_rename": True
                        })
                    )

    # Disconnect after one message
    client.loop_stop()
    client.disconnect()


# ----------------------------
# Main Entry Point
# ----------------------------

if __name__ == "__main__":
    mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqttc.on_message = on_message

    if args.username and args.password:
        mqttc.username_pw_set(args.username, args.password)

    mqttc.connect(args.host, args.port, 60)
    mqttc.loop_start()
    mqttc.subscribe("zigbee2mqtt/bridge/devices")

    # Wait for message processing
    time.sleep(5)
