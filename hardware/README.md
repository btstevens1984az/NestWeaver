# NestWeaver Hardware Notes

## Pin map (Raspberry Pi 5 — logical)

| Function | Pi GPIO / Bus | Notes |
|----------|---------------|-------|
| I²C SDA/SCL | GPIO2 / GPIO3 | IMU, optional expander |
| UART TX/RX | GPIO14 / GPIO15 | Arm controller serial (or USB) |
| SPI | SPI0 | Optional displays / ADCs |
| Hailo | PCIe / HAT connector | Do not share with conflicting HAT |
| RealSense | USB3 | Blue USB3 ports only |
| Mic array | USB2 | |
| E-stop sense | GPIO17 (input, NC→GND) | Debounced in software + hard relay |
| Motor enable | GPIO27 (output) | Must deassert on fault |
| Status LED | GPIO22 | Green = OK, blink = WARN |
| Bumper / cliff | GPIO5,6,13,19 | Active-low |

Exact BCM numbering should be re-verified against your carrier board revision.

## Power budget (approx. continuous / peak)

| Rail | Continuou | Peak | Source |
|------|-----------|------|--------|
| 5V logic (Pi + Hailo + USB cam) | 4–6 A | 8 A | Buck from pack |
| 12–24V motors (base) | 5–10 A | 20–30 A | Direct pack via drivers |
| Arm bus | 2–5 A | 10 A | Shared or dedicated |
| Accessories | 0.5 A | 1 A | 5V |

**Battery sizing example**: 6S 5000 mAh (~18.5V nominal) → roughly 1–2 hours light duty, less with continuous nav + arm.

## E-stop architecture

1. Mushroom switch breaks motor contactor coil (hardware).  
2. NC contact also pulls GPIO17 low → `SafetyInterlock.set_e_stop(True)`.  
3. Software stops cmd_vel / joint streams within one control cycle.  
4. Reset requires switch release **and** operator acknowledge (`clear_faults(acknowledge=True)`).

## Schematic notes

```
[Pack+]--fuse--[BMS]--+--[Motor drivers]--[Mecanum motors]
                      +--[Arm PSU]--[Arm]
                      +--[Buck 5V]--[Pi5]--[Hailo]
                                    |----[USB hub]--[RealSense][Mic][Speaker]
[Pack-]----------------------------common GND (star point near BMS)

[E-STOP NC]-- cuts contactor to motor drivers (base+arm)
           -- GPIO17 sense to Pi
```
