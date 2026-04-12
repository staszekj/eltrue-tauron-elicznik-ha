# Tauron eLicznik - Home Assistant Integration

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/staszekj/eltrue-tauron-ha.svg)](https://github.com/staszekj/eltrue-tauron-ha/releases)

Home Assistant integration for **Tauron eLicznik** - Polish energy meter readings from Tauron Dystrybucja.

## Features

- 📊 **Energy consumption** (energia pobrana) - total kWh consumed
- ☀️ **Energy exported** (energia oddana) - total kWh sent to grid (solar/prosumer)
- ⚡ **Net-metering balance** - kWh left to use (80% ratio in Poland)
- 📅 **Days until billing period ends**
- 📈 **Daily/Monthly usage projections**
- 🔄 **Manual refresh button** - Force data update on demand
- 🕐 **Full timestamp** of last meter reading and last API fetch

## Installation

### HACS (Recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu → **Custom repositories**
3. Add `https://github.com/staszekj/eltrue-tauron-ha` as **Integration**
4. Search for "Tauron eLicznik" and install
5. Restart Home Assistant
6. Go to **Settings → Devices & Services → Add Integration → Tauron eLicznik**

### Manual Installation

1. Download the latest release
2. Copy `custom_components/eltrue_tauron_ha` to your `config/custom_components/` folder
3. Restart Home Assistant
4. Add the integration via UI

## Configuration

You only need three fields to set up the integration:

| Field | Description | Example |
|-------|-------------|---------|
| **Username** | Your Tauron eLicznik email | `user@example.com` |
| **Password** | Your Tauron eLicznik password | |
| **Billing period start** | First day of your billing period | `2026-03-01` |

During setup, the integration automatically fetches your meter readings as of the billing period start date from the Tauron API — no need to enter them manually. The billing period end date is also calculated automatically (start + 1 year − 1 day).

## Sensors

| Sensor | Description | Unit | Device Class |
|--------|-------------|------|--------------|
| `sensor.eltrue_tauron_ha_consumed_energy` | Total energy consumed (lifetime counter) | kWh | energy |
| `sensor.eltrue_tauron_ha_exported_energy` | Total energy exported (lifetime counter) | kWh | energy |
| `sensor.eltrue_tauron_ha_consumed_energy_at_billing_start` | Consumed energy at start of billing period | kWh | energy |
| `sensor.eltrue_tauron_ha_exported_energy_at_billing_start` | Exported energy at start of billing period | kWh | energy |
| `sensor.eltrue_tauron_ha_energy_balance` | Net-metering balance remaining | kWh | energy |
| `sensor.eltrue_tauron_ha_daily_energy_budget` | Required daily usage to zero balance | kWh | energy |
| `sensor.eltrue_tauron_ha_monthly_energy_budget` | Projected monthly usage needed | kWh | energy |
| `sensor.eltrue_tauron_ha_days_until_billing` | Days until billing period ends | days | — |
| `sensor.eltrue_tauron_ha_last_reading_date` | Timestamp of last meter reading from Tauron | — | timestamp |
| `sensor.eltrue_tauron_ha_last_data_fetch` | Timestamp of last successful API call | — | timestamp |

## Button

| Button | Description |
|--------|-------------|
| `button.eltrue_tauron_ha_refresh_data` | Manually trigger data refresh from Tauron API |

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

Where increments are calculated from the start of your billing period:

```
energia_oddana_increment = exported_energy - exported_energy_at_billing_start
energia_pobrana_increment = consumed_energy - consumed_energy_at_billing_start
```

The `_at_billing_start` values are fetched automatically during integration setup.

## Requirements

- Home Assistant 2024.1.0 or newer
- Active Tauron eLicznik account at https://elicznik.tauron-dystrybucja.pl

## Troubleshooting

- **Cannot connect**: Verify your credentials at https://elicznik.tauron-dystrybucja.pl
- **No data**: Meter readings are typically available with 1-day delay
- **Invalid auth**: Make sure you're using your email address, not username
- **Wrong balance**: Check that your billing period start date is correct. The integration fetches meter readings for that exact date automatically

## License

MIT License - see [LICENSE](LICENSE) file.

## Credits

Inspired by the Node-RED implementation for Tauron eLicznik.
