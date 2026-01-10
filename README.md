# Tauron eLicznik - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/staszekj/tauron-elicznik-ha.svg)](https://github.com/staszekj/tauron-elicznik-ha/releases)

Home Assistant integration for **Tauron eLicznik** - Polish energy meter readings from Tauron Dystrybucja.

## Features

- 📊 **Energy consumption** (energia pobrana) - total kWh consumed
- ☀️ **Energy exported** (energia oddana) - total kWh sent to grid (solar/prosumer)
- ⚡ **Net-metering balance** - kWh left to use (80% ratio in Poland)
- 📅 **Days until billing period ends**
- 📈 **Daily/Monthly usage projections**
- 🔄 **Manual refresh button** - Force data update on demand

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/staszekj/tauron-elicznik-ha` as **Integration**
4. Search for "Tauron eLicznik" and install
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration → Tauron eLicznik**

### Manual Installation

1. Download the latest release
2. Copy `custom_components/tauron_elicznik` to your `config/custom_components/` folder
3. Restart Home Assistant
4. Add the integration via UI

## Configuration

You'll need:
- **Username**: Your Tauron eLicznik email (e.g., `user@example.com`)
- **Password**: Your Tauron eLicznik password
- **Billing period end**: Last day of your billing period (for net-metering calculations)
- **Previous readings**: Optional - starting values for the billing period

## Sensors

| Sensor | Description | Unit |
|--------|-------------|------|
| `sensor.tauron_elicznik_consumed_energy` | Total energy consumed | kWh |
| `sensor.tauron_elicznik_exported_energy` | Total energy exported | kWh |
| `sensor.tauron_elicznik_energy_balance` | Net-metering balance remaining | kWh |
| `sensor.tauron_elicznik_daily_energy_budget` | Required daily usage to zero balance | kWh |
| `sensor.tauron_elicznik_monthly_energy_budget` | Projected monthly usage needed | kWh |
| `sensor.tauron_elicznik_days_until_billing` | Days until billing period ends | days |
| `sensor.tauron_elicznik_last_reading_date` | Date of last meter reading | date |

## Button

| Button | Description |
|--------|-------------|
| `button.tauron_elicznik_refresh_data` | Manually trigger data refresh from Tauron API |

## Polling Interval

By default, data is polled every **12 hours**. Since Tauron meter readings are typically updated once per day (after midnight for the previous day), more frequent polling would just return the same data.

You can manually trigger a refresh anytime:
- Press the "Refresh data" button in the UI
- Add the button to your dashboard for easy access
- Use the `button.press` service in automations

## Net-Metering Calculation

In Poland, prosumers can use 80% of the energy they export to the grid. This integration calculates:

```
kWh_left = (energia_oddana_increment × 0.8) - energia_pobrana_increment
```

Where increments are calculated from the start of your billing period.

## Requirements

- Home Assistant 2024.1.0 or newer
- Active Tauron eLicznik account at https://elicznik.tauron-dystrybucja.pl

## Troubleshooting

- **Cannot connect**: Verify your credentials at https://elicznik.tauron-dystrybucja.pl
- **No data**: Meter readings are typically available with 1-day delay
- **Invalid auth**: Make sure you're using your email address, not username

## License

MIT License - see [LICENSE](LICENSE) file.

## Credits

Inspired by the Node-RED implementation for Tauron eLicznik.
