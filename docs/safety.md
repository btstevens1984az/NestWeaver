# Safety

NestWeaver is an experimental mobile manipulator. **You** are responsible for safe operation around people, pets, and property.

## Interlocks (implemented in software)

| Interlock | Behavior |
|-----------|----------|
| E-stop | Latches `E_STOP`; blocks all motion until release + acknowledge |
| Soft limits | Rejects base speeds / joint / EE poses outside configured bounds |
| Collision stop | Latches fault on bumper / camera collision signal |
| Battery cutoff | Blocks motion below cutoff fraction |
| Watchdogs | Heartbeat / perception / control timeouts degrade or fault |
| Torque limit | Latches when commanded/measured torque exceeds cap |
| Geofence | Latches on map boundary breach |
| Child/pet proximity | WARN: allows base crawl intent, blocks arm motion |

See `src/nestweaver/safety/interlocks.py` and `configs/safety/default.yaml`.

## Hardware requirements

1. **Hard e-stop** that removes motor power independently of the Pi.  
2. Current-limited drivers and correctly rated fuses.  
3. Mechanical soft padding on gripper and base corners.  
4. Tip-over stability: keep CG low; test arm extended on soft floor first.

## Operational rules

- First runs on jack stands / blocks so wheels cannot drive away.  
- Verify `nestweaver doctor` and unit tests before enabling motor power.  
- Never leave the robot unattended while motors are armed.  
- Establish household geofences (stairs, kitchens with open flames, etc.).  
- Teach kids that e-stop is for everyone — make it reachable and obvious.

## Disclaimer

Software cannot make a robot inherently safe. This project provides hooks and defaults, not a certified functional-safety system (no IEC 61508 / ISO 13849 claim).
