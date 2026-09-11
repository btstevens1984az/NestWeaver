# NestWeaver Bill of Materials (2026-era, approximate USD)

Prices fluctuate; treat figures as planning estimates for a single prototype.
Prefer reputable vendors; verify electrical ratings before purchase.

## Summary

| Subsystem | Approx. USD |
|-----------|-------------|
| Compute (Pi 5 + Hailo + storage) | $220–320 |
| Mobility (mecanum base + drivers) | $250–450 |
| Manipulation (6-DoF arm + gripper) | $300–900 |
| Perception (depth cam + mics/speakers) | $180–350 |
| Power (battery, BMS, wiring, e-stop) | $120–250 |
| Structure (printed parts, fasteners) | $40–120 |
| **Typical prototype total** | **~$1,100–2,400** |

## Detailed parts

| # | Part | Example / PN | Vendor ideas | Qty | Approx. USD | Notes |
|---|------|--------------|--------------|-----|-------------|-------|
| 1 | Raspberry Pi 5 (8GB) | Pi5-8GB | Raspberry Pi Authorized | 1 | 80 | Primary SBC |
| 2 | Active cooler / case | Pi5 official cooler | Same | 1 | 15 | Sustained AI + motor loads |
| 3 | NVMe or 256GB+ microSD | A2 / NVMe HAT optional | Samsung, WD | 1 | 25–60 | OS + models |
| 4 | Hailo-8L / Hailo-8 M.2 or HAT | Hailo AI HAT+ / M.2 | Hailo / Pi distributors | 1 | 70–150 | On-device vision |
| 5 | USB3 / PCIe adapter as needed | M.2 HAT for Pi5 | Pineboards, Pimoroni | 1 | 20–40 | If not using AI HAT |
| 6 | Mecanum wheel set 100mm | Generic aluminum mecanum | RobotShop, Amazon industrial | 4 | 60–120 | Omnidirectional base |
| 7 | Base chassis plate | Custom (see OpenSCAD) | Print / laser cut | 1 | 20–50 | Mount motors + Pi |
| 8 | Geared DC / BLDC hub motors | 12V–24V with encoders | DFRobot, Cytron kits | 4 | 80–160 | Prefer encoders |
| 9 | Motor drivers / ESCs | Cytron MDD10A / BTS7960 / VESC | Cytron, SparkFun | 2–4 | 40–120 | Match motor current |
| 10 | 6-DoF arm | SO-ARM101 / WidowX-class / MyCobot-class | Seeed, Trossen, Elephant | 1 | 300–900 | Prosumer arms vary widely |
| 11 | Parallel gripper | Arm kit gripper or DH-Robotics DIY | Bundle / Ali industrial | 1 | 30–150 | Soft pads for bottles |
| 12 | Depth camera | Intel RealSense D435i / D455 | Intel, Newegg | 1 | 250–350 | Or Orbbec Astra equivalent ~$150 |
| 13 | Budget depth alt | Orbbec Dabai / Stereo USB | Orbbec | 1 | 80–150 | Lower cost option |
| 14 | USB mic array | ReSpeaker 2/4-Mic | Seeed | 1 | 30–70 | Far-field voice |
| 15 | Speaker | 5W USB/I2S | Generic | 1 | 10–25 | TTS playback |
| 16 | IMU (if not in cam) | BNO085 / MPU9250 | Adafruit, SparkFun | 1 | 15–35 | Base orientation |
| 17 | Li-ion / LiFePO4 pack | 6S Li-ion or 4S LiFePO4 10–20Ah | Dualsky, generic BMS kits | 1 | 80–180 | Size to motors |
| 18 | BMS + buck converters | 5V/3A for Pi, 12V arm rail | Mean Well style bucks | 2–3 | 25–60 | Isolate logic vs motors |
| 19 | E-stop mushroom + relay | 22mm NC e-stop + contactor | Omron / generic | 1 | 20–40 | Hard power interrupt |
| 20 | Wiring / XT60 / fuses | Silicone wire, ANL fuse | Generic | 1 kit | 20–40 | See power budget |
| 21 | Fasteners / standoffs | M2.5/M3 kit | McMaster / Amazon | 1 | 15 | |
| 22 | 3D filament (PETG/ABS) | 1–2 kg | Prusa, Polymaker | 1 | 25–40 | Mounts + mast |

## Suggested starter kits (faster Day-1)

1. **Compute kit**: Pi 5 8GB + AI HAT+ (Hailo) + cooler + 256GB SD  
2. **Mobile base kit**: mecanum robot chassis with encoder motors + dual MDD drivers  
3. **Arm kit**: SO-ARM-class open arm with ROS 2 examples  
4. **Sense kit**: RealSense D435i + ReSpeaker  

## Consumables & tools (not in robot BOM)

- Soldering iron, crimp tool, multimeter, logic-safe bench PSU  
- PETG printer (≥220mm bed recommended)  
- Torque screwdriver for arm assembly  

## Procurement notes

- Confirm Hailo module interface (HAT vs M.2) matches your Pi 5 carrier.  
- Keep motor current spikes off the Pi 5 5V rail — separate battery domain.  
- Choose arm payload ≥ bottle weight × 2 safety margin (~0.5–1.0 kg class).  
- For indoor SLAM, depth camera + wheel odometry is enough to start; add lidar later if needed.
