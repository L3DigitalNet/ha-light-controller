# HA Light Controller Usage Guide

Complete reference for services, configuration options, and examples.

## Table of Contents

- [How It Works](#how-it-works)
- [Supported Functions](#supported-functions)
- [Use Cases](#use-cases)
- [Configuration Options](#configuration-options)
- [Services](#services)
  - [ensure_state](#ha_light_controllerensure_state)
  - [activate_preset](#ha_light_controlleractivate_preset)
  - [create_preset](#ha_light_controllercreate_preset)
  - [create_preset_from_current](#ha_light_controllercreate_preset_from_current)
  - [delete_preset](#ha_light_controllerdelete_preset)
- [Working with Presets](#working-with-presets)
- [Example Automations](#example-automations)
- [Known Limitations](#known-limitations)
- [Troubleshooting](#troubleshooting)

---

## How It Works

Light Controller is entirely **event-driven** — it does not poll devices or maintain
background update loops. When you call a service (e.g., `ensure_state`), the integration:

1. Resolves target entities (expanding groups into individual lights)
2. Sends light commands via Home Assistant's `light.turn_on` / `light.turn_off` services
3. Waits a configurable delay for state to propagate
4. Reads entity state from HA's state machine to verify the command succeeded
5. Retries failed entities with configurable backoff

**Preset entities** (buttons and sensors) update via a listener pattern. When a preset is
activated, created, or deleted, the preset manager notifies all registered entity
listeners, which then update their state. No periodic refresh is needed.

The integration's `iot_class` is `calculated` — it derives state from other HA entities
rather than communicating with external devices directly.

---

## Supported Functions

| Feature | Description |
|---------|-------------|
| **State verification** | Confirms lights reached target brightness, color temperature, and RGB values within configurable tolerances |
| **Automatic retries** | Retries failed lights with configurable attempts, delays, and optional exponential backoff |
| **Hard timeout** | Aborts the operation after a configurable maximum runtime regardless of retry count |
| **Group expansion** | Automatically expands `light.*` groups and `group.*` helper groups to individual light entities |
| **Per-entity overrides** | Set different brightness, color, state, and transition for each light in a single service call |
| **Fire-and-forget mode** | Skip verification for faster execution when reliability isn't critical |
| **Preset management** | Store light configurations and activate them via button entities or service calls |
| **Preset capture** | Create presets by capturing the current state of lights (brightness, color, effect) |
| **Preset UI management** | Create, edit, and delete presets through the integration's options flow with per-entity configuration |
| **Status tracking** | Optional sensor entity per preset tracks activation status (idle, activating, success, failed) |
| **Logbook integration** | Optionally log successful operations to the Home Assistant logbook |
| **Service responses** | All services return structured response data (success, attempts, failed lights, elapsed time) |

---

## Use Cases

### Reliable Room Lighting

Replace `light.turn_on` in automations with `ensure_state` to guarantee lights actually
reach the target state. Useful for Zigbee/Z-Wave networks where commands occasionally
get lost:

```yaml
service: ha_light_controller.ensure_state
data:
  entities:
    - light.living_room_ceiling
    - light.living_room_lamp
  state: 'on'
  brightness_pct: 80
  color_temp_kelvin: 3000
```

### Movie Mode Preset

Create a preset where different lights have different settings — main lights dim, TV
backlight warm, accent lights off:

```yaml
service: ha_light_controller.create_preset
data:
  name: 'Movie Mode'
  entities:
    - light.ceiling
    - light.tv_backlight
    - light.accent
  targets:
    - entity_id: light.ceiling
      state: 'off'
    - entity_id: light.tv_backlight
      state: 'on'
      brightness_pct: 15
      color_temp_kelvin: 2700
    - entity_id: light.accent
      state: 'off'
```

Activate it from a dashboard button or automation:

```yaml
service: ha_light_controller.activate_preset
data:
  preset: 'Movie Mode'
```

### Wake-Up Routine

Gradually increase brightness and color temperature over time:

```yaml
automation:
  - alias: 'Wake Up Sequence'
    trigger:
      - platform: time
        at: '06:30:00'
    action:
      - service: ha_light_controller.ensure_state
        data:
          entities:
            - light.bedroom
          brightness_pct: 10
          color_temp_kelvin: 2700
          transition: 1
      - delay: '00:10:00'
      - service: ha_light_controller.ensure_state
        data:
          entities:
            - light.bedroom
          brightness_pct: 80
          color_temp_kelvin: 5000
          transition: 600
```

### Capture and Replay Scenes

Manually set your lights to a look you like, then capture it as a preset:

```yaml
service: ha_light_controller.create_preset_from_current
data:
  name: 'Cozy Evening'
  entities:
    - light.living_room_ceiling
    - light.floor_lamp
    - light.accent_strip
```

The integration reads each light's current brightness, color, and effect and stores them.
Activate it any time to restore that exact scene.

### All-Off with Verification

Ensure every light in the house is actually off at bedtime:

```yaml
automation:
  - alias: 'Bedtime All Off'
    trigger:
      - platform: time
        at: '23:00:00'
    action:
      - service: ha_light_controller.ensure_state
        data:
          entities:
            - group.all_lights
          state: 'off'
          max_retries: 5
          log_success: true
```

---

## Configuration Options

Access configuration options by going to **Settings** → **Devices & Services** → **Light
Controller** → **Configure** → **Settings**.

Settings are organized into collapsible sections. The **Defaults** section is expanded
by default; click other section headers to expand them.

### Default Settings

| Setting            | Description                                                        |
| ------------------ | ------------------------------------------------------------------ |
| Default brightness | Brightness percentage used when not specified in a command (1-100) |
| Transition time    | Default transition duration in seconds                             |

### Verification Tolerances

These settings control how precisely lights must match the target values to be
considered successful.

| Setting              | Description                                                                                               |
| -------------------- | --------------------------------------------------------------------------------------------------------- |
| Brightness tolerance | Acceptable difference in brightness percentage (e.g., 5 means 45-55% is acceptable when 50% is requested) |
| RGB tolerance        | Acceptable difference in each RGB color channel (0-255 scale)                                             |
| Kelvin tolerance     | Acceptable difference in color temperature (Kelvin)                                                       |

### Retry & Timing

| Setting             | Description                                                                   |
| ------------------- | ----------------------------------------------------------------------------- |
| Delay after send    | Seconds to wait after sending a command before checking the result            |
| Max retries         | Maximum number of retry attempts if a light doesn't respond                   |
| Timeout             | Maximum total time allowed for the entire operation                           |
| Exponential backoff | Gradually increase delay between retries (recommended for congested networks) |
| Max backoff         | Maximum delay between retries when using exponential backoff                  |

### Logging

| Setting     | Description                                               |
| ----------- | --------------------------------------------------------- |
| Log success | Write successful operations to the Home Assistant logbook |

---

## Services

### ha_light_controller.ensure_state

Primary service for controlling lights with state verification and automatic retries.

#### Basic Example

```yaml
service: ha_light_controller.ensure_state
data:
  entities:
    - light.living_room_ceiling
    - light.living_room_lamp
  state: 'on'
  brightness_pct: 75
  color_temp_kelvin: 3000
  transition: 2
```

#### All Parameters

| Parameter                 | Type   | Required | Description                                                      |
| ------------------------- | ------ | -------- | ---------------------------------------------------------------- |
| `entities`                | list   | Yes      | Light entities, light groups, or helper groups to control        |
| `state`                   | string | No       | Target state: `on` or `off` (default: `on`)                      |
| `brightness_pct`          | int    | No       | Brightness percentage (1-100)                                    |
| `rgb_color`               | list   | No       | RGB color as `[R, G, B]` (each value 0-255)                      |
| `color_temp_kelvin`       | int    | No       | Color temperature in Kelvin (e.g., 2700 for warm, 6500 for cool) |
| `effect`                  | string | No       | Effect name to apply (device-specific)                           |
| `targets`                 | list   | No       | Per-light override settings (see below)                          |
| `transition`              | float  | No       | Transition time in seconds                                       |
| `skip_verification`       | bool   | No       | Skip state verification for faster execution                     |
| `brightness_tolerance`    | int    | No       | Override configured brightness tolerance                         |
| `rgb_tolerance`           | int    | No       | Override configured RGB tolerance                                |
| `kelvin_tolerance`        | int    | No       | Override configured Kelvin tolerance                             |
| `delay_after_send`        | float  | No       | Override configured delay before verification                    |
| `max_retries`             | int    | No       | Override configured retry attempts                               |
| `max_runtime_seconds`     | float  | No       | Override configured timeout                                      |
| `use_exponential_backoff` | bool   | No       | Override configured backoff setting                              |
| `max_backoff_seconds`     | float  | No       | Override configured maximum backoff delay                        |
| `log_success`             | bool   | No       | Log success to logbook                                           |

#### Per-Light Overrides

Use `targets` to override settings for specific entities. Entities not in `targets` use
the top-level defaults.

```yaml
service: ha_light_controller.ensure_state
data:
  entities:
    - light.ceiling
    - light.lamp
    - light.accent
  state: 'on'
  brightness_pct: 50 # Default for entities not in targets
  targets:
    - entity_id: light.ceiling
      brightness_pct: 100
      color_temp_kelvin: 4000
    - entity_id: light.lamp
      brightness_pct: 30
      rgb_color: [255, 200, 150]
    - entity_id: light.accent
      brightness_pct: 75
      effect: 'colorloop'
```

---

### ha_light_controller.activate_preset

Activate a saved preset by its name or ID.

```yaml
service: ha_light_controller.activate_preset
data:
  preset: 'Evening Mode'
```

| Parameter | Type   | Required | Description       |
| --------- | ------ | -------- | ----------------- |
| `preset`  | string | Yes      | Preset name or ID |

---

### ha_light_controller.create_preset

Create a new preset programmatically via a service call.

```yaml
service: ha_light_controller.create_preset
data:
  name: 'Movie Night'
  entities:
    - light.living_room_ceiling
    - light.tv_backlight
  state: 'on'
  brightness_pct: 20
  color_temp_kelvin: 2700
  transition: 3
```

| Parameter           | Type   | Required | Description                                         |
| ------------------- | ------ | -------- | --------------------------------------------------- |
| `name`              | string | Yes      | Name for the preset                                 |
| `entities`          | list   | Yes      | Light entities to include                           |
| `state`             | string | No       | Target state: `on` or `off`                         |
| `brightness_pct`    | int    | No       | Brightness percentage                               |
| `rgb_color`         | list   | No       | RGB color as `[R, G, B]`                            |
| `color_temp_kelvin` | int    | No       | Color temperature in Kelvin                         |
| `effect`            | string | No       | Effect to apply                                     |
| `targets`           | list   | No       | Per-light overrides (same format as `ensure_state`) |
| `transition`        | float  | No       | Transition time in seconds                          |
| `skip_verification` | bool   | No       | Use fire-and-forget mode for this preset            |

---

### ha_light_controller.create_preset_from_current

Captures current state of specified lights and saves as a new preset.

```yaml
service: ha_light_controller.create_preset_from_current
data:
  name: 'Current Scene'
  entities:
    - light.living_room_ceiling
    - light.living_room_lamp
```

| Parameter  | Type   | Required | Description               |
| ---------- | ------ | -------- | ------------------------- |
| `name`     | string | Yes      | Name for the new preset   |
| `entities` | list   | Yes      | Light entities to capture |

---

### ha_light_controller.delete_preset

Delete a preset by its ID.

```yaml
service: ha_light_controller.delete_preset
data:
  preset_id: 'abc123-def456'
```

| Parameter   | Type   | Required | Description                           |
| ----------- | ------ | -------- | ------------------------------------- |
| `preset_id` | string | Yes      | The unique ID of the preset to delete |

---

## Working with Presets

Each preset creates two entities:

- `button.ha_light_controller_<preset_name>` - Activates the preset when pressed
- `sensor.ha_light_controller_<preset_name>_status` - Shows activation status

### Preset Button

The button entity uses a static `mdi:lightbulb-group` icon (declared in `icons.json`).

**Attributes:**

| Attribute           | Description                                           |
| ------------------- | ----------------------------------------------------- |
| `preset_id`         | Unique identifier for the preset                      |
| `entities`          | List of target light entities                         |
| `state`             | Target state (`on` or `off`)                          |
| `brightness_pct`    | Target brightness percentage                          |
| `rgb_color`         | RGB color (if set)                                    |
| `color_temp_kelvin` | Color temperature (if set)                            |
| `last_result`       | Result of the last activation (`success` or `failed`) |
| `last_activated`    | Timestamp of last activation                          |

### Preset Status Sensor

Shows the current activation status with dynamic icons:

| State         | Icon                       | Description                       |
| ------------- | -------------------------- | --------------------------------- |
| Idle          | `mdi:lightbulb-outline`    | Preset is ready to activate       |
| Activating... | `mdi:lightbulb-on`         | Preset is currently being applied |
| Success       | `mdi:lightbulb-on-outline` | All lights reached target state   |
| Failed        | `mdi:lightbulb-alert`      | Some lights failed verification   |

**Attributes:**

| Attribute        | Description                         |
| ---------------- | ----------------------------------- |
| `preset_id`      | Unique identifier for the preset    |
| `preset_name`    | Display name of the preset          |
| `target_state`   | Target state (`on` or `off`)        |
| `entity_count`   | Number of lights in the preset      |
| `last_activated` | Timestamp of last activation        |
| `last_success`   | Whether last activation succeeded   |
| `last_message`   | Status message from last activation |
| `last_attempts`  | Number of retry attempts used       |
| `last_elapsed`   | Time taken (e.g., `"1.2s"`)         |
| `failed_lights`  | List of lights that failed (if any) |
| `failed_count`   | Count of failed lights              |
| `skipped_lights` | List of skipped lights (if any)     |
| `skipped_count`  | Count of skipped lights             |

### Creating Presets via UI

**Settings** → **Devices & Services** → **Light Controller** → **Configure** → **Add
Preset**

The preset creation flow supports per-entity configuration:

1. **Basic Settings** - Enter preset name, select entities, optionally skip verification
2. **Entity Hub** - Manage entities and their configurations:
   - **Configure an entity** - Set state, brightness, color, and transition for each
     light individually
   - **Add more entities** - Include additional lights
   - **Remove an entity** - Remove lights from the preset (requires at least one)
   - **Save preset** - Finalize once at least one entity is configured

This allows presets where different lights have different settings (e.g., ceiling at
100% warm white, accent at 30% RGB red).

### Per-Entity Configuration in Presets

When creating a preset via the UI, you can configure each light individually:

- **State**: Set individual lights to "on" or "off" within the same preset
- **Transition**: Set different transition times for each light
- **Brightness/Color**: Set different brightness, color temperature, or RGB values per
  light

This allows creating complex presets like "Movie Mode" where:

- Main ceiling light is off
- TV backlight is on at 20% with warm color
- Accent lights are on at 10%

All activated via a single button press.

#### Service Call Example

```yaml
service: ha_light_controller.ensure_state
data:
  entities:
    - light.ceiling
    - light.tv_backlight
    - light.accent
  state: 'on' # Default state
  targets:
    - entity_id: light.ceiling
      state: 'off'
    - entity_id: light.tv_backlight
      state: 'on'
      brightness_pct: 20
      color_temp_kelvin: 2700
      transition: 2.0
    - entity_id: light.accent
      state: 'on'
      brightness_pct: 10
```

### Editing Presets via UI

**Settings** → **Devices & Services** → **Light Controller** → **Configure** → **Manage
Presets** → **Edit Preset**

Select an existing preset to modify. You'll enter the same Entity Hub used for creation,
with all settings pre-populated. Make changes and save to update the preset.

### Deleting Presets via UI

**Settings** → **Devices & Services** → **Light Controller** → **Configure** → **Manage
Presets** → **Delete Preset**

Select a preset to delete. A confirmation step shows the preset name and entity count
before deletion. Check the confirmation box to proceed.

### Dashboard Cards

```yaml
type: button
entity: button.ha_light_controller_evening_mode
tap_action:
  action: toggle
```

```yaml
type: entities
entities:
  - entity: button.ha_light_controller_evening_mode
  - entity: sensor.ha_light_controller_evening_mode_status
```

### Using Presets in Automations

Via button entity:

```yaml
service: button.press
target:
  entity_id: button.ha_light_controller_evening_mode
```

Via service:

```yaml
service: ha_light_controller.activate_preset
data:
  preset: 'Evening Mode'
```

---

## Example Automations

### Script with Per-Light Overrides

```yaml
script:
  living_room_evening:
    alias: 'Living Room Evening'
    sequence:
      - service: ha_light_controller.ensure_state
        data:
          entities:
            - light.living_room_ceiling
            - light.floor_lamp
            - light.accent_lights
          state: 'on'
          brightness_pct: 40
          color_temp_kelvin: 2700
          transition: 2
          targets:
            - entity_id: light.accent_lights
              rgb_color: [255, 180, 100]
              brightness_pct: 30
```

### Automation with Success Logging

```yaml
automation:
  - alias: 'Bedtime Lights'
    trigger:
      - platform: time
        at: '22:00:00'
    action:
      - service: ha_light_controller.ensure_state
        data:
          entities:
            - group.all_lights
          state: 'off'
          log_success: true
```

### Skip Verification (Fire-and-Forget)

```yaml
service: ha_light_controller.ensure_state
data:
  entities:
    - light.hallway
  state: 'on'
  brightness_pct: 100
  skip_verification: true
```

### Gradual Brightness Increase

```yaml
automation:
  - alias: 'Morning Wake Up'
    trigger:
      - platform: time
        at: '06:30:00'
    action:
      - service: ha_light_controller.ensure_state
        data:
          entities:
            - light.bedroom_ceiling
          state: 'on'
          brightness_pct: 10
          color_temp_kelvin: 2700
          transition: 1
      - delay: '00:05:00'
      - service: ha_light_controller.ensure_state
        data:
          entities:
            - light.bedroom_ceiling
          brightness_pct: 50
          color_temp_kelvin: 4000
          transition: 300
      - delay: '00:05:00'
      - service: ha_light_controller.ensure_state
        data:
          entities:
            - light.bedroom_ceiling
          brightness_pct: 100
          color_temp_kelvin: 5500
          transition: 300
```

### Capture Current State as Preset

```yaml
script:
  save_current_lighting:
    alias: 'Save Current Lighting'
    sequence:
      - service: ha_light_controller.create_preset_from_current
        data:
          name: 'Saved Scene'
          entities:
            - light.living_room_ceiling
            - light.living_room_lamp
            - light.tv_backlight
```

---

## Known Limitations

- **Light entities only**: Only `light.*` entities are controlled. Other entity types
  (switches, fans, covers) are not supported. `group.*` helper groups are expanded, but
  only their `light.*` members are controlled.

- **State verification depends on entity reporting**: Verification reads the entity's
  state from Home Assistant's state machine. If a light reports inaccurate values (some
  cheap bulbs round brightness or don't report color), verification may fail even though
  the light visually looks correct. Increase tolerances to compensate.

- **Transition on first attempt only**: The `transition` parameter is only sent on the
  first attempt. Retries skip transitions for faster recovery. Per-entity transitions in
  `targets` follow the same rule.

- **Single config entry**: Only one Light Controller instance can be configured. This is
  enforced via `async_set_unique_id`.

- **Color mode mutual exclusivity**: You can set `rgb_color` or `color_temp_kelvin` per
  entity, but not both. If both are provided, RGB takes precedence.

- **No effect verification**: Effects (e.g., `colorloop`) are sent but not verified.
  There is no standard way to confirm an effect is active since not all lights report
  their current effect.

- **Group expansion is one level deep**: `group.*` helpers are expanded to their direct
  `light.*` members. Nested groups (a group containing another group) are not recursively
  expanded.

- **Preset status sensor disabled by default**: The status sensor for each preset is
  disabled in the entity registry by default. Enable it manually in **Settings** →
  **Devices & Services** → **Light Controller** → **Entities** if you want to track
  activation status.

---

## Troubleshooting

### Lights Not Reaching Target State

If lights frequently fail verification:

1. **Increase tolerances**: Some lights report slightly different values than what was
   set. Try increasing brightness tolerance to 5-10%.

2. **Increase delay_after_send**: Some lights take time to report their new state. Try
   1-2 seconds.

3. **Increase max_retries**: For unreliable networks, try 5+ retries.

4. **Enable debug logging** to see exactly what's happening:

```yaml
logger:
  default: info
  logs:
    custom_components.ha_light_controller: debug
```

### Verification Always Fails for Specific Lights

- **Check capability**: Not all lights support all features. A light that doesn't
  support RGB will always fail RGB verification.
- **Check availability**: Ensure the light is powered on and connected to your network.
- **Check the reported state**: Use Developer Tools → States to see what values the
  light actually reports.

### Presets Not Appearing

- Preset button and sensor entities are created dynamically via a listener; no restart
  is needed. If they don't appear within a few seconds, reload the integration from
  **Settings** → **Devices & Services** → **Light Controller** → three-dot menu → **Reload**.
- Check **Settings** → **Devices & Services** → **Light Controller** → **Entities** to
  see if the button and sensor were created.
- Look for errors in the Home Assistant log.

### Commands Are Slow

- Reduce `delay_after_send` if your lights respond quickly.
- Enable `skip_verification` for non-critical commands.
- Use groups instead of individual lights where possible (Light Controller will expand
  them automatically, but sending to a group can be faster).

### Getting "Entity not found" Errors

- Verify the entity ID is correct (check in Developer Tools → States).
- Make sure you're using the full entity ID (e.g., `light.living_room`, not just
  `living_room`).
- For groups, use either `light.group_name` or `group.group_name` depending on how the
  group was created.

---

## Diagnostics

Light Controller supports Home Assistant's built-in diagnostics feature. To download a
diagnostics report:

1. Go to **Settings** → **Devices & Services** → **Light Controller**
2. Click the three-dot menu → **Download diagnostics**

The report includes a summary of configured presets (count, names, entity lists). Share
this file when reporting issues.

---

## Links

- [GitHub Repository](https://github.com/L3DigitalNet/HA-Light-Controller)
- [Issue Tracker](https://github.com/L3DigitalNet/HA-Light-Controller/issues)
