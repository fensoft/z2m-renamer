# 🏷️ Zigbee2MQTT Device Renamer

Easily **backup and restore `friendly_name` values** for all your Zigbee2MQTT (Z2M) devices.
Automatically generates an inventory file and detects unpaired devices.

---

## 🔧 Features

* 🔁 Sync device names from Z2M with a local inventory
* 📦 Automatically generates and maintains `inventory.csv`
* ⚠️ Warns when devices are missing/unpaired (unless marked as `disabled`)
* ✍️ Supports rename automation via MQTT
* 🧪 Includes `--dry-run` mode for testing without writing or publishing

---

## 🏠 Usage in Home Assistant OS (HAOS)

**Recommended:** Install the [`Studio Code Server`](https://github.com/hassio-addons/addon-vscode) addon to run and edit scripts easily.

```bash
# Clone the repository
git clone https://github.com/fensoft/z2m-renamer
cd z2m-renamer

# Run the script (replace <mqttserver> with your broker address)
python3 main.py --host <mqttserver>
```

If your MQTT broker requires authentication:

```bash
python3 main.py --host <mqttserver> --username <user> --password <pass>
```

## 💻 Usage on Any Computer

```bash
# Clone the repository
git clone https://github.com/fensoft/z2m-renamer
cd z2m-renamer

# Install dependencies
python3 -m pip install -r requirements.txt

# Run the script
python3 main.py --host <mqttserver>
```

---

## 📝 Notes

* The script creates `inventory.csv` if it doesn’t exist.
* Devices listed but not currently paired will be reported unless marked `disabled`.
* Use the `--dry-run` option to preview changes without modifying files or sending MQTT commands.
