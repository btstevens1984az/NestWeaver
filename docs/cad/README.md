# NestWeaver CAD

Parametric OpenSCAD parts for a printable NestWeaver prototype.

## Files

| File | Purpose |
|------|---------|
| `openscad/chassis_motor_mount.scad` | Mecanum motor / Pi mount plate |
| `openscad/arm_base_bracket.scad` | 6-DoF arm pedestal bracket |
| `openscad/camera_mast_clamp.scad` | Depth camera mast clamp + shoe |

## Workflow

1. Install [OpenSCAD](https://openscad.org/).
2. Open a `.scad` file → **F5** preview → **F6** render.
3. **File → Export → Export as STL…** into `docs/cad/stl/`.
4. Slice in PrusaSlicer / Cura: PETG recommended, 4 perimeters, 30% infill for load parts.

## STL folder

See [`stl/README.md`](stl/README.md). Generated `.stl` binaries are gitignored by default to keep the repo light; export locally before printing.
