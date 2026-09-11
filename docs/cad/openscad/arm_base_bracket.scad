// NestWeaver — arm base bracket (parametric)

/* [Arm bracket] */
base_w = 90;
base_d = 70;
base_t = 6;
column_h = 40;
column_od = 36;
column_id = 28;
bolt_circle_d = 50;
bolt_d = 4.2;

$fn = 80;

difference() {
  union() {
    cube([base_w, base_d, base_t], center=true);
    translate([0, 0, base_t/2])
      cylinder(h=column_h, d=column_od);
  }
  translate([0, 0, base_t/2 - 0.1])
    cylinder(h=column_h + 1, d=column_id);
  for (a = [0:90:270])
    rotate([0, 0, a])
      translate([bolt_circle_d/2, 0, -base_t])
        cylinder(h=base_t*2 + column_h, d=bolt_d);
  // wire channel
  translate([0, 0, base_t/2 + 8])
    rotate([0, 90, 0])
      cylinder(h=column_od, d=8, center=true);
}
