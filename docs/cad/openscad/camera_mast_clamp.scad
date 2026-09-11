// NestWeaver — camera mast clamp for RealSense-class cameras

/* [Mast] */
mast_od = 22;
clamp_gap = 1.2;
wall = 4;
height = 28;
camera_plate_w = 50;
camera_plate_d = 20;
camera_plate_t = 4;
hole_spacing = 30;
hole_d = 3.2;

$fn = 80;

module clamp_body() {
  difference() {
    cylinder(h=height, d=mast_od + 2*wall);
    translate([0, 0, -0.1])
      cylinder(h=height + 0.2, d=mast_od);
    translate([0, -clamp_gap/2, -0.1])
      cube([mast_od, clamp_gap, height + 0.2]);
  }
}

union() {
  clamp_body();
  translate([mast_od/2 + wall, -camera_plate_d/2, height/2 - camera_plate_t/2])
    difference() {
      cube([camera_plate_w, camera_plate_d, camera_plate_t]);
      for (x = [10, 10 + hole_spacing])
        translate([x, camera_plate_d/2, -0.1])
          cylinder(h=camera_plate_t + 0.2, d=hole_d);
    }
  // pinch bolt ears
  for (y = [-12, 12])
    translate([0, y, height/2])
      difference() {
        cube([10, 8, 10], center=true);
        rotate([0, 90, 0])
          cylinder(h=12, d=3.2, center=true);
      }
}
