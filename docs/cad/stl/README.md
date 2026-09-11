# Exported STL parts

OpenSCAD sources live in `../openscad/`. Export STLs here before slicing.

| Expected STL | Source | Notes |
|--------------|--------|-------|
| `chassis_motor_mount.stl` | `chassis_motor_mount.scad` | Print flat on bed; PETG |
| `arm_base_bracket.stl` | `arm_base_bracket.scad` | May need brim; check bolt circle vs your arm |
| `camera_mast_clamp.stl` | `camera_mast_clamp.scad` | Print clamp upright; add heat-set inserts optional |

```bash
# Headless export example (OpenSCAD CLI)
openscad -o docs/cad/stl/chassis_motor_mount.stl docs/cad/openscad/chassis_motor_mount.scad
openscad -o docs/cad/stl/arm_base_bracket.stl docs/cad/openscad/arm_base_bracket.scad
openscad -o docs/cad/stl/camera_mast_clamp.stl docs/cad/openscad/camera_mast_clamp.scad
```
