
include <threads_v2.scad>
use <knurledFinishLib_v2.scad>


$fn=100;


// The maximum lens size that the holder should accomodate.  This scales
// the diameter of the lens holder, as well as the length of the sliders
maxLensDiameter = 23.64;

// Height of stand. Does not include the diameter of the lens holder
height = 25;

// Length of bolt. Shouldn't be any reason to change this.
boltLength = 15;

// A scaling factor applied to the bolt.  Smaller values may be required
// if threads are not printed well.  NOTE: this applies a scaling in all
// axis to the bolt, so too much scaling will distort the threads
// sufficiently that they no longer mesh!
boltScaling = 0.95;

// The height of the extrusion nut may need to be scaled for a tight
// fit, depending on your extrusion and printer
extrusionNutHeightScaling = 1;



// PRIVATE -- don't edit these variables
outerDiameter = maxLensDiameter + (14.18*2);
outerRadius = outerDiameter/2;
innerDiameter = outerDiameter - (9.75*2);
    
module holder() {
    union() {
        difference() {
            cylinder(d=outerDiameter,h=5);
            translate([0,0, -1]) cylinder(d=innerDiameter,h=12);
            for (i = [0:2]) {
                rotate([0,0,120*i + 59]) translate([0,(innerDiameter/2)+5,-2]) 
                    cylinder(d=6.1,h=22);
            }
        }
    }  
    for (i = [0:2]) {
        difference() {
             rotate([0,0,120*i + 60]) 
                translate([-8,-(7.5/2) + (innerDiameter/2)+4, 5])
                cube([16,7.5,5]);
            rotate([0,0,120*i + 60]) 
                translate([-5,-(7.5/2) + (innerDiameter/2)+3.9, 4])
                cube([10,9,7]);
        }
        
        rotate([0,0,120*i + 58]) translate([0,(innerDiameter/2)+4.5,0]) 
            MetricNut(6, 5);
    }
}


module stand() {
    union() {
        difference() {
            toleranceWidth = 5.9*1.05;
            offset = (10-toleranceWidth)/2;
            union() {
                // stalk
                translate([0,0,0]) cube([10,10, height+3]);
                
                 // bottom pedestal
                difference() {
                    translate([0,0,height+5]) mirror([0,0,1]) difference() {
                        translate([-5,0,height-10]) cube([20,10, 15]);
                        translate([-15,11,height-9]) 
                            rotate([90,90,0]) cylinder(d=30,h=12);
                        translate([15+10,11,height-9]) 
                            rotate([90,90,0]) cylinder(d=30,h=12);
                    }
                }
            }
            translate([offset, offset,-1]) 
                cube([toleranceWidth, toleranceWidth ,height]);
        }
        
        // top pedestal
        difference() {
            translate([-5,0,height-10]) cube([20,10, 15]);
            translate([-15,11,height-9]) rotate([90,90,0]) cylinder(d=30,h=12);
            translate([15+10,11,height-9]) rotate([90,90,0]) cylinder(d=30,h=12);
        }
    }
}

module slider() {
    outerLength = outerRadius + 4 + 9;
    innerLength = outerLength - 7;
    //slider
        union() {
            difference() {
                translate([-5,-(25/2) + 21, 0]) 
                    cube([10,outerLength,5]);
                translate([-6.1/2,-(18/2) + 21, -1])
                    cube([6.1,innerLength,7]);
            }
            difference() {
                rotate([0,0,0]) translate([0,3.5,2.5]) {
                    b = 7.1;
                    h = 7.1;
                    w = 5;

                    //Start with an extruded triangle
                    rotate(a=[0,0,45])
                    linear_extrude(height = w, center = true, convexity = 10, twist = 0)
                    polygon(points=[[0,0],[h,0],[0,b]], paths=[[0,1,2]]);
                }
               rotate([45,0,0])  translate([-2.5,0.5,-2]) cube(5);
            }
        }
}

module complete_holder() {
    translate([0,0,outerRadius + height]) rotate([90,60,0]) holder();
    translate([-5,-10,0]) stand();
}

module extrusionNut() {
    scale([1,1,extrusionNutHeightScaling]) translate([0,0,5.6]) union() {
        difference() {
            union() {
                for (i = [0:5]) {
                    translate([0,2*i,0]) rotate([0,180,0]) import("tnut.stl", convexity=10);
                }
                
            }
            translate([-12,10,-10]) cube([15,20,10]);
        }
        difference() {
            translate([-8.5,2,-.5]) cube([5.9,5.9,height-10]);
            translate([-6,-1,2]) cube([1,5.9+4,height-10]); // slot
            translate([-5.5,10,2]) rotate([90,0,0]) cylinder(d=2,h=10); //relief
        }
        translate([-3,8,height-1.5-10]) rotate([90,0,0]) 
            cylinder(d=2.5,h=6);
        translate([-3-5,8,height-1.5-10]) rotate([90,0,0]) 
            cylinder(d=2.5,h=6);
        translate([-8,0,-5.60]) 
            cube([5,10,0.60]);
    }
}

module bolt() {
    scale([boltScaling,boltScaling,boltScaling]) intersection() {
        difference() {
            union() {
                MetricBolt(6, boltLength);
                translate([0,0,0]) knurl(k_cyl_hg = 6, k_cyl_od = 13);
            }
            translate([0,0,-3]) cylinder(d=14,h=3);
        }
        // Shave off some of the knurling, the points are painful!
        cylinder(d=12.5,boltLength+6);
    }
}



for (i= [0:2]) {
    translate([i*14.5,18,0])  bolt();
    translate([i*14.5,18 + 5,0]) slider();
    translate([i*14.5,18 - 15,0]) MetricWasher(6);
}

translate([-10,0,0]) extrusionNut();
translate([-outerRadius - 10,0,0]) rotate([-90,0,0]) complete_holder();


