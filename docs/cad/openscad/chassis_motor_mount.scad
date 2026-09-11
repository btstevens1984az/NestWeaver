// NestWeaver — chassis motor mount (parametric)
// OpenSCAD ≥ 2021. Open this file and press F6 to render, then export STL.

/* [Motor mount] */
plate_length = 120;
plate_width = 80;
plate_thickness = 5;
motor_hole_spacing = 25;
motor_hole_d = 3.2;
shaft_clearance_d = 14;
corner_radius = 6;
standoff_h = 8;

$fn = 64;

module rounded_plate(l, w, t, r) {
  hull() {
    for (x = [-l/2 + r, l/2 - r])
      for (y = [-w/2 + r, w/2 - r])
        translate([x, y, 0]) cylinder(h=t, r=r);
  }
}

difference() {
  union() {
    rounded_plate(plate_length, plate_width, plate_thickness, corner_radius);
    // Pi standoff bosses
    for (x = [-30, 30])
      for (y = [-20, 20])
        translate([x, y, plate_thickness])
          cylinder(h=standoff_h, d=8);
  }
  // motor bolt pattern
  for (x = [-motor_hole_spacing/2, motor_hole_spacing/2])
    for (y = [-motor_hole_spacing/2, motor_hole_spacing/2])
      translate([x, y, -0.1])
        cylinder(h=plate_thickness + standoff_h + 1, d=motor_hole_d);
  // shaft clearance
  translate([0, 0, -0.1])
    cylinder(h=plate_thickness + 1, d=shaft_clearance_d);
  // cable pass-through
  translate([plate_length/2 - 15, 0, -0.1])
    cylinder(h=plate_thickness + 1, d=10);
  // Pi mounting holes M2.5
  for (x = [-29, 29])
    for (y = [-24.5, 24.5])
      translate([x, y, -0.1])
        cylinder(h=plate_thickness + standoff_h + 1, d=2.7);
}
