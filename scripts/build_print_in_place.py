from pathlib import Path
import runpy,json,math
import FreeCAD as A
import Part,MeshPart
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'print_in_place'
g=runpy.run_path(str(ROOT/'scripts/build_racer.py'))
V=A.Vector;cyl=g['cyl'];box=g['box'];poly=g['polygon']
SHAFT_RADIUS=4.5
BORE_RADIUS=SHAFT_RADIUS+1.0
HUB_START=18.0
TIRE_START=33.5
TIRE_FACE=47.0
def yz_prism(points,x=-110,length=220):
    return Part.Face(poly([(x,y,z) for y,z in points])).extrude(V(length,0,0))
def roof_limit(apex,crown=10):
    shoulder=apex-(65-crown)
    return yz_prism([(-65,-5),(-65,shoulder),(-crown,apex),
                     (crown,apex),(65,shoulder),(65,-5)])
canopy=g['canopy'].common(roof_limit(43,10))
# Shared longitudinal loft eliminates the old hood/sidepod/front splice faces.
# Every section closes on z=5, producing one planar chassis underside.
def front_section(x, points):
    curve=Part.BSplineCurve()
    curve.interpolate([V(x,y,z) for y,z in points])
    return Part.Wire([curve.toShape(),
                      Part.makeLine(V(x,points[-1][0],points[-1][1]),
                                    V(x,points[0][0],points[0][1]))])
body_stations=[
    # x, half-width, outer-wall height, fender crest, central deck height
    (-99,34,15,29,26),(-90,43,20,34,29),(-75,47,24,38,30),
    (-55,47,25,36,30),(-30,47,25,33,30),(0,47,25,33,31),
    (25,47,25,34,33),(45,47,25,36,34),(63,47,24,38,34),
    (76,45,22,36,33),(86,40,20,32,30.5),(95,34,17,27,26.5),
    (100.5,27,13,22.5,21.5),
]
body_sections=[]
for x,w,wall,crest,deck in body_stations:
    half=[(-w,5),(-w,wall),(-.90*w,wall+4),(-.76*w,crest-5),
          (-.59*w,crest),(-.38*w,deck+.6)]
    points=half+[(0,deck)]+[(-y,z) for y,z in reversed(half)]
    body_sections.append(front_section(x,points))
body_shell=Part.makeLoft(body_sections,True,False,False,3).removeSplitter()
assert body_shell.isValid() and len(body_shell.Solids)==1
shell_surface_report={'construction':'single longitudinal smooth loft',
                      'untrimmed_faces':len(body_shell.Faces),
                      'planar_underside_z_mm':5,
                      'separate_hood_or_nose_fusions':0}
fixed=body_shell.common(box(-99,-47,5,199.5,94,69)).common(roof_limit(74))
fixed=fixed.fuse(canopy).removeSplitter()

# Front details share one horizontal datum so the fascia reads as a single
# assembly instead of a collection of unrelated holes.
def front_recess(points, x=95.5, depth=6.0):
    return yz_prism(points, x, depth)

for sign in (-1, 1):
    # Thin swept lamp pocket on the upper bumper.
    lamp=[(sign*10.0,23.4),(sign*14.0,26.2),(sign*26.0,27.1),
          (sign*30.0,25.4),(sign*25.0,23.7),(sign*14.0,22.9)]
    fixed=fixed.cut(front_recess(lamp,96.5,4.5))

    # Separate brake duct, angled toward the wheel rather than cut as a box.
    duct=[(sign*20.0,8.5),(sign*29.0,10.0),(sign*28.0,17.2),
          (sign*21.5,16.0)]
    fixed=fixed.cut(front_recess(duct,96.0,4.5))

# A shaped splitter follows the bumper plan and stops short of the tire faces.
splitter_outline=[(100.5,-17,5.8),(100.5,17,5.8),(98,25,5.8),
                  (91,30,5.8),(88,26,5.8),(90,-26,5.8),
                  (91,-30,5.8),(98,-25,5.8)]
splitter=Part.Face(poly(splitter_outline)).extrude(V(0,0,1.8)).removeSplitter()
if splitter.isValid() and len(splitter.Solids)==1:
    fixed=fixed.fuse(splitter).removeSplitter()

# Two recessed grille tiers retain a solid bumper beam between them.
lower_grille=[(-17.0,7.4),(-20.0,9.0),(-18.0,11.8),
              (18.0,11.8),(20.0,9.0),(17.0,7.4)]
upper_grille=[(-14.0,13.1),(-17.0,14.4),(-14.0,16.8),
              (14.0,16.8),(17.0,14.4),(14.0,13.1)]
fixed=fixed.cut(front_recess(lower_grille,96.5,4.0))
fixed=fixed.cut(front_recess(upper_grille,96.5,4.0))

fixed = fixed.removeSplitter()
assert fixed.isValid() and len(fixed.Solids)==1,('body',len(fixed.Solids))
# Continuous bearing hole with 45-degree flares into the wheel wells.
for x in (-63,63):
    # 7 mm shaft with a 9 mm bore leaves 1 mm radial running clearance.
    fixed=fixed.cut(cyl(BORE_RADIUS,110,(x,-55,18),(0,1,0)))
    for sign in (-1,1):
        axis=V(0,sign,0)
        flare=Part.makeCone(BORE_RADIUS,19.5,18,V(x,15.7*sign,18),axis)
        well=cyl(19.5,24,(x,33.7*sign,18),(0,sign,0))
        fixed=fixed.cut(flare.fuse(well))
# Wing edges align with wheel faces and sills on the print bed.
# Lowered wing position for better proportions — was too tall before.
wing_z = 48  # down from 58
tip_top = 57  # down from 67/69
outline=[(-91,-43,wing_z),(-87,-47,wing_z),(-69,-47,wing_z),(-65,-43,wing_z),(-65,43,wing_z),(-69,47,wing_z),(-87,47,wing_z),(-91,43,wing_z)]
wing=Part.Face(poly(outline)).extrude(V(0,0,3.2))
for sign in (-1,1):
    tip=[(sign*35,wing_z),(sign*35,wing_z+3.2),(sign*44.6,wing_z+9),(sign*47,wing_z+9),(sign*47,wing_z)]
    wing=wing.fuse(yz_prism(tip,-87,18))
# Two longitudinal plates: 16 mm fore-aft chord, 2 mm normal thickness.
# A 45-degree lateral lean permits layer-by-layer growth in the side-down print.
plate_half=math.sqrt(2)
for sign in (-1,1):
    lower=15.7;upper=36.0
    section=[(sign*lower-plate_half,29.7),(sign*lower+plate_half,29.7),
             (sign*upper+plate_half,wing_z+0.6),(sign*upper-plate_half,wing_z+0.6)]
    fixed=fixed.fuse(yz_prism(section,-85,16))
fixed=fixed.fuse(wing).removeSplitter()
assert fixed.isValid() and len(fixed.Solids)==1,('body',len(fixed.Solids))
# Each wheel grows from a 45-degree conical hub; no separate cap or pin.
hub=Part.makeCone(SHAFT_RADIUS,18,TIRE_START-HUB_START,V(0,0,HUB_START),V(0,0,1))
wheel=hub.fuse(cyl(18,TIRE_FACE-1-TIRE_START,(0,0,TIRE_START)))
wheel=wheel.fuse(Part.makeCone(18,17,1,V(0,0,TIRE_FACE-1),V(0,0,1)))
wheel_face_rings=[(4.5,.75,1.0),(12.7,1.0,1.25)]
wheel_face_radial_width=2.0
wheel_face_radial_depth=1.2
for r,half,depth in wheel_face_rings:
    triangle=Part.Face(poly([(r-half,0,47.01),(r+half,0,47.01),(r,0,47.01-depth)]))
    wheel=wheel.cut(triangle.revolve(V(0,0,0),V(0,0,1),360))
for i in range(10):
    groove=Part.Face(poly([(4.8,-wheel_face_radial_width/2,47.01),(4.8,wheel_face_radial_width/2,47.01),(4.8,0,47.01-wheel_face_radial_depth)])).extrude(V(8.2,0,0))
    groove.rotate(V(0,0,0),V(0,0,1),i*36);wheel=wheel.cut(groove)
for z in (37,42):
    groove=Part.Face(poly([(18.01,0,z-.6),(18.01,0,z+.6),(17.5,0,z)]))
    wheel=wheel.cut(groove.revolve(V(0,0,0),V(0,0,1),360))
wheel=wheel.removeSplitter()
assert wheel.isValid() and len(wheel.Solids)==1
axles=[];envelopes=[]
for x,name in [(-63,'RearDumbbellAxle'),(63,'FrontDumbbellAxle')]:
    axle=cyl(SHAFT_RADIUS,2*(HUB_START+1),(x,-HUB_START-1,18),(0,1,0))
    env=axle.copy()
    for sign in (-1,1):
        p=A.Placement(V(x,0,18),A.Rotation(V(0,0,1),V(0,sign,0)))
        w=wheel.copy();w.Placement=p.multiply(w.Placement);axle=axle.fuse(w)
        cap=hub.fuse(cyl(18,TIRE_FACE-TIRE_START,(0,0,TIRE_START)))
        cap.Placement=p.multiply(cap.Placement);env=env.fuse(cap)
    axle=axle.removeSplitter()
    assert axle.isValid() and len(axle.Solids)==1,(name,axle.isValid(),len(axle.Solids))
    axles.append((name,axle));envelopes.append((name,env))
A.closeDocument(g['doc'].Name);doc=A.newDocument('ApexDumbbellRacer')
scene={'meshes':{},'instances':[],'version':'dumbbell-axles','print_in_place':True,'dumbbell_axles':True}
def mesh_entry(target,name,shape,color):
    m=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.08,Relative=False)
    pts,tri=m.Topology;target['meshes'][name]={'vertices':[[p.x/1000,p.y/1000,p.z/1000] for p in pts],'triangles':tri}
    target['instances'].append({'name':name,'mesh':name,'color':color,'pose':{'xyz_mm':[0,0,0],'quaternion_xyzw':[0,0,0,1]}})
    return m
parts=[('IntegratedBody',fixed)]+axles;overhang=[]
for name,s in parts:
    o=doc.addObject('PartDesign::Feature',name);o.Shape=s
    o.addProperty('App::PropertyColor','DesignColor','Print').DesignColor=(.72,.035,.055)
    o.addProperty('App::PropertyString','Function','Print').Function='Fixed chassis with axle tunnels' if name=='IntegratedBody' else 'Left wheel + axle + right wheel: one rotating solid'
    m=mesh_entry(scene,name,s,(.72,.035,.055))
    area=0;total=0;regions=[];confirmed_area=0
    for f in m.Facets:
        a,b,c=[V(*p) for p in f.Points];normal=(b-a).cross(c-a);ar=normal.Length/2;total+=ar
        if normal.Length and normal.y/normal.Length < -math.sqrt(.5)-.005 and (a.y+b.y+c.y)/3 > -46.85:
            area+=ar
            center=(a+b+c)/3;vertex=Part.Vertex(center)
            _,_,supports=s.distToShape(vertex)
            support=supports[0]
            if support[0]=='Face':
                face=s.Faces[support[1]];u,v=support[2]
            else:
                nearest=min(range(len(s.Faces)),key=lambda i:s.Faces[i].distToShape(vertex)[0])
                face=s.Faces[nearest];u,v=face.Surface.parameter(center)
            if face.normalAt(u,v).y < -math.sqrt(.5)-.005:confirmed_area+=ar
            if ar>1:regions.append([round(v,2) for v in [(a.x+b.x+c.x)/3,(a.y+b.y+c.y)/3,(a.z+b.z+c.z)/3,ar]])
    overhang.append({'part':name,'surface_area_mm2':total,'steeper_than_45_downward_area_mm2':area,'cad_confirmed_steeper_than_45_area_mm2':confirmed_area,'largest_facets':sorted(regions,key=lambda v:-v[3])[:12]})
doc.recompute();doc.saveAs(str(ROOT/'apex_racer.FCStd'));Part.export(doc.Objects,str(ROOT/'apex_racer.step'))
(ROOT/'scene.json').write_text(json.dumps(scene,separators=(',',':')))
compound=Part.makeCompound([s for _,s in parts]);printshape=compound.copy()
printshape.rotate(V(0,0,0),V(1,0,0),90);printshape.translate(V(0,0,-printshape.BoundBox.ZMin))
mesh=MeshPart.meshFromShape(Shape=printshape,LinearDeflection=.025,AngularDeflection=.08,Relative=False)
mesh.write(str(OUT/'apex_racer_side_down.stl'));assert mesh.isSolid()
side={'meshes':{},'instances':[]}
for name,s in parts:
    t=s.copy();t.rotate(V(0,0,0),V(1,0,0),90);t.translate(V(0,0,47));mesh_entry(side,name,t,(.72,.035,.055))
(OUT/'side_scene.json').write_text(json.dumps(side,separators=(',',':')))
mechanism={'meshes':{},'instances':[]}
mesh_entry(mechanism,'ChassisSection',fixed.cut(box(-110,-60,18,220,120,90)),(.31,.35,.40))
for name,s in axles:mesh_entry(mechanism,name,s,(.85,.52,.12))
(OUT/'mechanism_scene.json').write_text(json.dumps(mechanism,separators=(',',':')))
report={'mode':'Single print job; two integrated dumbbell axles through chassis bores','rigid_bodies':3,'stl_files_required':1,'shaft_diameter_mm':7,'bore_diameter_mm':9,'radial_bearing_clearance_mm':1.0,'tire_arch_radial_clearance_mm':1.5,'wheel_face_texture':{'ring_count':len(wheel_face_rings),'ring_width_mm':[2*half for _,half,_ in wheel_face_rings],'ring_depth_mm':[depth for _,_,depth in wheel_face_rings],'radial_groove_count':10,'radial_groove_width_mm':wheel_face_radial_width,'radial_groove_depth_mm':wheel_face_radial_depth},'wing_supports':{'count':2,'normal_thickness_mm':2,'longitudinal_chord_mm':16,'lateral_lean_deg':45},'wheel_360_sweep_checks':[], 'all_shapes_valid':True,'stl_closed':True,'physical_print_test':False,'print_bounds_mm':[printshape.BoundBox.XLength,printshape.BoundBox.YLength,printshape.BoundBox.ZLength],'overhang_audit':overhang}
for name,env in envelopes:
    vol=env.common(fixed).Volume;gap=env.distToShape(fixed)[0]
    report['wheel_360_sweep_checks'].append({'axle':name,'conservative_envelope_overlap_mm3':vol,'min_clearance_mm':gap})
    assert vol<.01 and gap>.89,(name,vol,gap)
assert not axles[0][1].BoundBox.intersect(axles[1][1].BoundBox)
report['body_surfaces']=shell_surface_report
report['shaft_diameter_mm']=2*SHAFT_RADIUS
report['bore_diameter_mm']=2*BORE_RADIUS
for p in [OUT/'validation_report.json',ROOT/'validation_report.json',ROOT/'build_report.json']:p.write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
