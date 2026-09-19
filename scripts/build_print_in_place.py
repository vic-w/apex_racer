from pathlib import Path
import runpy,json,math
import FreeCAD as A
import Part,MeshPart
from sports_coupe import MODEL_SCALE,ROOF_HEIGHT,make_cabin,make_wing,detail_body,face_groups,check_packaging,check_cabin_surface
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
canopy=make_cabin()
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
    # Keep the rear quarter broad at the print plane near the rear wheel.
    (-99,48,15,29,26),(-90,48,20,34,29),(-75,48,24,38,30),
    (-55,47,25,36,30),(-30,47,25,33,30),(0,47,25,33,31),
    (25,47,25,34,33),(45,47,25,36,34),(63,47,24,38,34),
    # Oversize the cheeks before trimming to the +/-47 mm print planes.
    (76,48,22,36,33),(86,48,20,32,30.5),(95,48,17,27,26.5),
    (100.5,36,13,22.5,21.5),
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
# Trim only the sides; coincident end caps make the widened loft boolean fragile.
fixed=body_shell.common(box(-110,-47,0,220,94,80)).common(roof_limit(74))
fixed=fixed.fuse(canopy).common(box(-110,-47,0,220,94,80)).removeSplitter()

# Front details share one horizontal datum so the fascia reads as a single
# assembly instead of a collection of unrelated holes.
def front_recess(points, x=95.5, depth=6.0):
    return yz_prism(points, x, depth)

for sign in (-1, 1):
    # Thin swept lamp pocket on the upper bumper.
    lamp=[(sign*10.0,23.4),(sign*14.0,26.2),(sign*26.0,27.1),
          (sign*30.0,25.4),(sign*25.0,23.7),(sign*14.0,22.9)]
    fixed=fixed.cut(front_recess(lamp,96.5,4.5))

    # Diamond ducts close at 45 degrees in the side-down print direction.
    duct=[(sign*20.0,12.85),(sign*24.5,8.35),(sign*29.0,12.85),
          (sign*24.5,17.35)]
    fixed=fixed.cut(front_recess(duct,96.0,4.5))

# A shaped splitter follows the bumper plan and stops short of the tire faces.
splitter_outline=[(100.5,-17,5.8),(100.5,17,5.8),(98,25,5.8),
                  (91,30,5.8),(88,26,5.8),(90,-26,5.8),
                  (91,-30,5.8),(98,-25,5.8)]
splitter=Part.Face(poly(splitter_outline)).extrude(V(0,0,1.8)).removeSplitter()
if splitter.isValid() and len(splitter.Solids)==1:
    fixed=fixed.fuse(splitter).removeSplitter()

# Two recessed grille tiers retain a solid bumper beam between them.
lower_grille=[(-17.8,7.4),(-20.0,9.6),(-17.8,11.8),
              (17.8,11.8),(20.0,9.6),(17.8,7.4)]
upper_grille=[(-15.15,13.1),(-17.0,14.95),(-15.15,16.8),
              (15.15,16.8),(17.0,14.95),(15.15,13.1)]
fixed=fixed.cut(front_recess(lower_grille,96.5,4.0))
fixed=fixed.cut(front_recess(upper_grille,96.5,4.0))

fixed = fixed.removeSplitter()
assert fixed.isValid() and len(fixed.Solids)==1,('body',len(fixed.Solids))
# Continuous bearing hole with 45-degree flares into the wheel wells.
for x in (-63,63):
    # The bore radius leaves 1 mm radial running clearance around the shaft.
    fixed=fixed.cut(cyl(BORE_RADIUS,110,(x,-55,18),(0,1,0)))
    for sign in (-1,1):
        axis=V(0,sign,0)
        flare=Part.makeCone(BORE_RADIUS,19.5,18,V(x,15.7*sign,18),axis)
        well=cyl(19.5,24,(x,33.7*sign,18),(0,sign,0))
        fixed=fixed.cut(flare.fuse(well))
wing_base=43.0
wing=make_wing()
plate_half=math.sqrt(2)
for sign in (-1,1):
    root_y=14.5;root_z=28.4;top_z=wing_base+.4
    top_y=root_y+top_z-root_z
    section=[(sign*root_y-plate_half,root_z),(sign*root_y+plate_half,root_z),
             (sign*top_y+plate_half,top_z),(sign*top_y-plate_half,top_z)]
    fixed=fixed.fuse(yz_prism(section,-90,12))
fixed=fixed.fuse(wing).removeSplitter()
fixed,glass_floors,detail_floors,body_details,pillars=detail_body(fixed)
paint=face_groups(fixed,glass_floors,detail_floors)
packaging=check_packaging(fixed)
assert fixed.isValid() and len(fixed.Solids)==1,('body',len(fixed.Solids))
# Audit the stationary nose only; wheel contact must not mask a floating bumper.
nose=fixed.common(box(80,-48,0,25,96,70))
nose_bed_faces=[f for f in nose.Faces
                if abs(f.BoundBox.YMin+TIRE_FACE)<1e-6
                and abs(f.BoundBox.YMax+TIRE_FACE)<1e-6]
nose_contact_area=sum(f.Area for f in nose_bed_faces)
nose_first_layer=nose.common(box(80,-TIRE_FACE,0,25,.2,70))
assert nose_contact_area>150,('nose_bed_contact_mm2',nose_contact_area)
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
A.closeDocument(g['doc'].Name)

# The design is authored at a comfortable inspection scale, then the complete
# assembly is uniformly reduced for the A1 mini print bed.  This is equivalent
# to the 60% manual scale that was previously applied before slicing.
def scale_shape(shape):
    matrix=A.Matrix()
    matrix.A11=MODEL_SCALE;matrix.A22=MODEL_SCALE;matrix.A33=MODEL_SCALE
    return shape.transformGeometry(matrix)

fixed=scale_shape(fixed)
axles=[(name,scale_shape(shape)) for name,shape in axles]
envelopes=[(name,scale_shape(shape)) for name,shape in envelopes]
assert all(s.isValid() and len(s.Solids)==1 for s in [fixed]+[s for _,s in axles])
TIRE_FACE_OUT=TIRE_FACE*MODEL_SCALE
fixed_nose=fixed.common(box(80*MODEL_SCALE,-48*MODEL_SCALE,0,
                            25*MODEL_SCALE,96*MODEL_SCALE,70*MODEL_SCALE))
nose_bed_faces=[f for f in fixed_nose.Faces
                if abs(f.BoundBox.YMin+TIRE_FACE_OUT)<1e-6
                and abs(f.BoundBox.YMax+TIRE_FACE_OUT)<1e-6]
nose_contact_area=sum(f.Area for f in nose_bed_faces)
nose_first_layer=fixed_nose.common(box(80*MODEL_SCALE,-TIRE_FACE_OUT,0,
                                       25*MODEL_SCALE,.2,70*MODEL_SCALE))
wing_region=fixed.common(box(-101*MODEL_SCALE,-48*MODEL_SCALE,38*MODEL_SCALE,
                             35*MODEL_SCALE,96*MODEL_SCALE,14*MODEL_SCALE))
wing_bed_contact=wing_region.common(box(-110*MODEL_SCALE,-TIRE_FACE_OUT,0,
                                        220*MODEL_SCALE,.2,80*MODEL_SCALE)).Volume/.2
wing_planar_contact=sum(f.Area for f in wing_region.Faces
                        if abs(f.BoundBox.YMin+TIRE_FACE_OUT)<1e-6
                        and abs(f.BoundBox.YMax+TIRE_FACE_OUT)<1e-6)
assert wing_planar_contact>30
rear_contact_region=fixed.common(box(-101*MODEL_SCALE,-48*MODEL_SCALE,0,
                                     21*MODEL_SCALE,96*MODEL_SCALE,38*MODEL_SCALE))
rear_bed_faces=[f for f in rear_contact_region.Faces
                if abs(f.BoundBox.YMin+TIRE_FACE_OUT)<1e-6
                and abs(f.BoundBox.YMax+TIRE_FACE_OUT)<1e-6]
rear_body_contact_area=sum(f.Area for f in rear_bed_faces)
assert rear_body_contact_area>25,('rear_body_contact_mm2',rear_body_contact_area)
packaging=check_packaging(fixed,MODEL_SCALE)
cabin_surface=check_cabin_surface(fixed,MODEL_SCALE)
bed_contact_report={'body_region_x_mm':[80*MODEL_SCALE,100.5*MODEL_SCALE],
                    'bed_plane_y_mm':-TIRE_FACE_OUT,
                    'nose_planar_contact_mm2':nose_contact_area,
                    'first_layer_height_mm':.2,
                    'nose_first_layer_mean_area_mm2':nose_first_layer.Volume/.2,
                    'rear_body_planar_contact_mm2':rear_body_contact_area,
                    'rear_contact_region_x_mm':[-101*MODEL_SCALE,-80*MODEL_SCALE],
                    'permanent_widened_bumper':True,'permanent_widened_rear':True}
doc=A.newDocument('ApexSportsCoupe')
scene={'meshes':{},'instances':[],'version':'dumbbell-axles','print_in_place':True,'dumbbell_axles':True}
def mesh_entry(target,name,shape,color):
    m=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.025,AngularDeflection=.08,Relative=False)
    pts,tri=m.Topology;target['meshes'][name]={'vertices':[[p.x/1000,p.y/1000,p.z/1000] for p in pts],'triangles':tri}
    target['instances'].append({'name':name,'mesh':name,'color':color,'pose':{'xyz_mm':[0,0,0],'quaternion_xyzw':[0,0,0,1]}})
    return m
parts=[('IntegratedBody',fixed)]+axles;overhang=[]
# Check moving clearances before saving any deliverable.
rotation_checks=[]
for name,env in envelopes:
    vol=env.common(fixed).Volume;gap=env.distToShape(fixed)[0]
    assert vol<.01 and gap>.89*MODEL_SCALE,(name,vol,gap)
    rotation_checks.append({'axle':name,'conservative_envelope_overlap_mm3':vol,'min_clearance_mm':gap})
for name,s in parts:
    print('Meshing and auditing ' + name,flush=True)
    o=doc.addObject('PartDesign::Feature',name);o.Shape=s
    o.addProperty('App::PropertyColor','DesignColor','Print').DesignColor=(.72,.035,.055)
    o.addProperty('App::PropertyString','Function','Print').Function='Fixed chassis with axle tunnels' if name=='IntegratedBody' else 'Left wheel + axle + right wheel: one rotating solid'
    if name=='IntegratedBody':
        o.Label='Two-seat coupe body with fixed doors'
        o.addProperty('App::PropertyIntegerList','GlassFaces','Appearance').GlassFaces=paint['glass']
        o.addProperty('App::PropertyIntegerList','DetailFaces','Appearance').DetailFaces=paint['details']
        o.addProperty('App::PropertyString','CabinLayout','Design').CabinLayout='Two seats abreast; fixed doors; exterior model without interior fittings'
    m=mesh_entry(scene,name,s,(.72,.035,.055))
    area=0;total=0;regions=[];confirmed_area=0
    for f in m.Facets:
        a,b,c=[V(*p) for p in f.Points];normal=(b-a).cross(c-a);ar=normal.Length/2;total+=ar
        if normal.Length and normal.y/normal.Length < -math.sqrt(.5)-.005 and (a.y+b.y+c.y)/3 > -46.85*MODEL_SCALE:
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

# Colours identify the actual recessed CAD faces; the printable solid is unchanged.
scene['instances']=[i for i in scene['instances'] if i['name']!='IntegratedBody']
del scene['meshes']['IntegratedBody']
accent=set(paint['glass']+paint['details'])
mesh_entry(scene,'BodyPaint',Part.makeCompound([f for i,f in enumerate(fixed.Faces) if i not in accent]),(.72,.035,.055))
mesh_entry(scene,'GlassRecesses',Part.makeCompound([fixed.Faces[i] for i in paint['glass']]),(.075,.14,.18))
mesh_entry(scene,'DoorDetails',Part.makeCompound([fixed.Faces[i] for i in paint['details']]),(.16,.025,.035))
doc.recompute();doc.saveAs(str(ROOT/'apex_racer.FCStd'));Part.export(doc.Objects,str(ROOT/'apex_racer.step'))
(ROOT/'scene.json').write_text(json.dumps(scene,separators=(',',':')))
compound=Part.makeCompound([s for _,s in parts]);printshape=compound.copy()
printshape.rotate(V(0,0,0),V(1,0,0),90);printshape.translate(V(0,0,TIRE_FACE_OUT))
mesh=MeshPart.meshFromShape(Shape=printshape,LinearDeflection=.025,AngularDeflection=.08,Relative=False)
assert abs(mesh.BoundBox.ZMin)<1e-5,('print_bed_z_mm',mesh.BoundBox.ZMin)
mesh.write(str(OUT/'apex_racer_side_down.stl'));assert mesh.isSolid()
side={'meshes':{},'instances':[]}
for name,s in parts:
    t=s.copy();t.rotate(V(0,0,0),V(1,0,0),90);t.translate(V(0,0,TIRE_FACE_OUT));mesh_entry(side,name,t,(.72,.035,.055))
(OUT/'side_scene.json').write_text(json.dumps(side,separators=(',',':')))
mechanism={'meshes':{},'instances':[]}
mesh_entry(mechanism,'ChassisSection',fixed.cut(box(-110*MODEL_SCALE,-60*MODEL_SCALE,18*MODEL_SCALE,
                                                    220*MODEL_SCALE,120*MODEL_SCALE,90*MODEL_SCALE)),(.31,.35,.40))
for name,s in axles:mesh_entry(mechanism,name,s,(.85,.52,.12))
(OUT/'mechanism_scene.json').write_text(json.dumps(mechanism,separators=(',',':')))
print_bounds=[mesh.BoundBox.XLength,mesh.BoundBox.YLength,mesh.BoundBox.ZLength]
assert all(value<180 for value in print_bounds),print_bounds
report={
    'mode':'Single print job; two integrated dumbbell axles through chassis bores',
    'model_scale':MODEL_SCALE,'a1_mini_bed_fit':True,'target_build_volume_mm':[180,180,180],
    'rigid_bodies':3,'stl_files_required':1,
    'radial_bearing_clearance_mm':1.0*MODEL_SCALE,
    'tire_arch_radial_clearance_mm':1.5*MODEL_SCALE,
    'wheel_face_texture':{
        'ring_count':len(wheel_face_rings),
        'ring_width_mm':[2*half*MODEL_SCALE for _,half,_ in wheel_face_rings],
        'ring_depth_mm':[depth*MODEL_SCALE for _,_,depth in wheel_face_rings],
        'radial_groove_count':10,'radial_groove_width_mm':wheel_face_radial_width*MODEL_SCALE,
        'radial_groove_depth_mm':wheel_face_radial_depth*MODEL_SCALE},
    'rear_spoiler':{
        'type':'swept tapered Bezier blade with rising trailing lip and endplates',
        'top_z_mm':49.0*MODEL_SCALE,'span_mm':94*MODEL_SCALE,
        'trailing_edge_thickness_mm':1.6*MODEL_SCALE,
        'endplate_thickness_mm':2*MODEL_SCALE,
        'endplate_transition_span_mm':8*MODEL_SCALE,
        'support_count':2,'support_normal_thickness_mm':2*MODEL_SCALE,'support_lean_deg':45,
        'planar_contact_mm2':wing_planar_contact,
        'first_layer_mean_area_mm2':wing_bed_contact},
    'wheel_360_sweep_checks':rotation_checks,'all_shapes_valid':True,'stl_closed':True,
    'physical_print_test':False,'overhang_audit':overhang}
assert not axles[0][1].BoundBox.intersect(axles[1][1].BoundBox)
report['body_surfaces']={'construction':shell_surface_report['construction'],
                         'untrimmed_faces':shell_surface_report['untrimmed_faces'],
                         'planar_underside_z_mm':shell_surface_report['planar_underside_z_mm']*MODEL_SCALE,
                         'separate_hood_or_nose_fusions':shell_surface_report['separate_hood_or_nose_fusions']}
report['bed_contact']=bed_contact_report
report['cabin']={'layout':'two-seat road coupe','roof_height_mm':ROOF_HEIGHT*MODEL_SCALE,
                 'surface_measurements':cabin_surface,
                 'pillars':[dict(p,minimum_window_recess_separation_mm=
                                  p['minimum_window_recess_separation_mm']*MODEL_SCALE) for p in pillars],
                 'fixed_door_count':2,'door_panel_length_mm':68*MODEL_SCALE,
                 'door_seam_width_mm':.9*MODEL_SCALE,'door_seam_lateral_depth_mm':.8*MODEL_SCALE,
                 'window_lateral_recess_mm':.8*MODEL_SCALE,'interior_modelled':False,
                 'packaging':packaging,
                 'details':[dict(detail,removed_volume_mm3=detail['removed_volume_mm3']*MODEL_SCALE**3)
                            for detail in body_details]}
report['print_bounds_mm']=print_bounds
report['print_bed_z_mm']=mesh.BoundBox.ZMin
report['shaft_diameter_mm']=2*SHAFT_RADIUS*MODEL_SCALE
report['bore_diameter_mm']=2*BORE_RADIUS*MODEL_SCALE
(OUT/'validation_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
