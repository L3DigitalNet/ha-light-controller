# Incident Disablement Runbook

When Light Controller causes problems (lights stuck, HA slowdown, exceptions flooding logs).

## 1. Immediate Containment

Disable the integration without removing it:

**Settings** > **Devices & Services** > **Light Controller** > three-dot menu > **Disable**

This stops all service handlers and entity updates. Lights remain controllable via native `light.turn_on`/`light.turn_off`.

## 2. Evidence Capture

Before changing anything else:

1. **Download diagnostics**: Settings > Devices & Services > Light Controller > three-dot > Download diagnostics
2. **Save logs**: Settings > System > Logs > Download full log
3. Note the timestamp when the issue started

## 3. Fallback to Native Light Control

With the integration disabled, use HA's built-in services directly:

```yaml
service: light.turn_on
target:
  entity_id: light.living_room
data:
  brightness_pct: 80
  color_temp_kelvin: 3000
```

Automations that call `ha_light_controller.ensure_state` will fail silently. Replace with `light.turn_on`/`light.turn_off` calls until the issue is resolved.

## 4. Rollback

If disabling isn't enough (corrupt config entry, entity registry pollution):

1. Remove the integration: Settings > Devices & Services > Light Controller > Delete
2. Restart Home Assistant
3. Reinstall from HACS if the issue was version-specific (pin to a known-good version)

## 5. Verification

After re-enabling or reinstalling:

1. Check logs for errors: Settings > System > Logs, filter for `ha_light_controller`
2. Test one preset activation manually
3. Verify entity states update within the expected delay
