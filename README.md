# HA Light Controller

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="brand-images/dark_logo.png">
  <source media="(prefers-color-scheme: light)" srcset="brand-images/logo.png">
  <img alt="HA Light Controller" src="brand-images/logo.png" width="200">
</picture>

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![GitHub Release](https://img.shields.io/github/release/L3DigitalNet/HA-Light-Controller.svg)](https://github.com/L3DigitalNet/HA-Light-Controller/releases)
[![License](https://img.shields.io/github/license/L3DigitalNet/HA-Light-Controller.svg)](LICENSE)
[![Issues](https://img.shields.io/github/issues/L3DigitalNet/HA-Light-Controller.svg)](https://github.com/L3DigitalNet/HA-Light-Controller/issues)

HA Light Controller adds state verification and automatic retries to light commands.
When you call `light.turn_on`, Home Assistant sends the command once and assumes
success. This integration verifies that entities actually reached the target state and
retries if they didn't.

This solves the common problem of lights occasionally missing commands due to network
congestion, Zigbee/Z-Wave mesh issues, or unresponsive devices. Instead of building
retry logic into every script and automation, HA Light Controller handles verification
centrally with configurable tolerances and backoff strategies.

### How It Works

1. Sends the light command (on/off, brightness, color, etc.)
2. Waits a configurable delay for the state to update
3. Verifies entity attributes match target values within tolerance
4. Retries with exponential backoff if verification fails
5. Optionally logs success to the Home Assistant logbook

## Key Features

- **State verification** - Confirms entities reached target brightness, color, and
  temperature within configurable tolerances
- **Automatic retries** - Configurable retry attempts with exponential backoff
- **Group expansion** - Automatically expands `light.*` and `group.*` entities to
  individual lights
- **Per-entity overrides** - Set different attributes for each light in a single service
  call via the `targets` parameter
- **Presets** - Store light configurations as button entities for one-tap activation

## Installation

### HACS

1. Add `https://github.com/L3DigitalNet/HA-Light-Controller` as a custom repository
   (Integration)
2. Install "HA Light Controller"
3. Restart Home Assistant

### Manual

1. Copy `custom_components/ha_light_controller` to your `config/custom_components/`
   directory
2. Restart Home Assistant

## Removal

1. Go to **Settings** → **Devices & Services** → **Light Controller**
2. Click the three-dot menu → **Delete**
3. Restart Home Assistant
4. (Optional) Remove the `custom_components/ha_light_controller` directory

All preset entities (buttons and sensors) are automatically removed when the integration
is deleted.

## Configuration

Add the integration via **Settings** → **Devices & Services** → **Add Integration** →
"Light Controller".

Configuration options include default brightness, transition time, verification
tolerances (brightness, RGB, Kelvin), retry settings, and success logging.

## Usage

### Basic Service Call

```yaml
service: ha_light_controller.ensure_state
data:
  entities:
    - light.living_room_ceiling
    - light.living_room_lamp
  state: 'off'
```

### Per-Entity Overrides

```yaml
service: ha_light_controller.ensure_state
data:
  entities:
    - light.ceiling
    - light.lamp
  brightness_pct: 50
  targets:
    - entity_id: light.ceiling
      brightness_pct: 100
      color_temp_kelvin: 4000
    - entity_id: light.lamp
      brightness_pct: 30
      rgb_color: [255, 200, 150]
```

### Presets

Create and edit presets via the integration options UI or programmatically. The UI
supports per-entity configuration - set different brightness, color, and state for each
light in the preset. Preset deletion includes a confirmation step.

```yaml
service: ha_light_controller.create_preset
data:
  name: 'Movie Night'
  entities:
    - light.living_room
    - light.tv_backlight
  brightness_pct: 20
  color_temp_kelvin: 2700
```

Each preset creates a `button.*` entity for activation and a `sensor.*` entity for
status tracking.

## Documentation

See the **[Usage Guide](USAGE.md)** for complete service parameters, configuration
options, examples, and [diagnostics](USAGE.md#diagnostics).

## Links

- [Issue Tracker](https://github.com/L3DigitalNet/HA-Light-Controller/issues)
- [License (MIT)](LICENSE)
