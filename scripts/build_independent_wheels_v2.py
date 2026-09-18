from pathlib import Path
import runpy,json
import FreeCAD as A
import Part,Mesh,MeshPart
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'print_in_place'
g=runpy.run_path(str(ROOT/'scripts/build_racer.py'))
V=A.Vector;cyl=g['cyl'];box=g['box'];roundrect=g['roundrect']
body=g['body'];canopy=g['canopy'];wing=g['wing']
# Bond the formerly removable canopy to its pocket floor.
seat=Part.Face(roundrect(-6,0,26.3,82,52,9)).extrude(V(0,0,1.1))
fixed=body.fuse(seat).fuse(canopy)
# Fill the wing assembly clearances so the blade and towers are one solid.
for y in (-24,24):fixed=fixed.fuse(box(-78.6,y-2.6,57.1,5.2,5.2,4.1))
fixed=fixed.fuse(wing)
# Each tire and rim become one moving wheel; bridge their original glue clearance.
bridge=cyl(13.6,1.8,(0,0,0)).cut(cyl(3,1.8,(0,0,0)))
wheel=g['tire'].fuse(g['rim']).fuse(bridge).cut(cyl(3,15,(0,0,-.5))).removeSplitter()
assert wheel.isValid() and len(wheel.Solids)==1
wheels=[];sweeps=[]
for x,end in [(-63,'Rear'),(63,'Front')]:
    for sign,side in [(1,'Left'),(-1,'Right')]:
        axis=V(0,sign,0)
        # Integrated axle anchored six mm into chassis; 0.5 mm radial clearance.
        shaft=cyl(2.5,26.4,(x,22*sign,18),(0,sign,0))
        inner=cyl(4.5,2.3,(x,31.2*sign,18),(0,sign,0))
        # 45-degree conical captive head, avoids a wide unsupported upper shoulder.
        outer=Part.makeCone(2.5,4.5,2,V(x,47.7*sign,18),axis)
        outer=outer.fuse(cyl(4.5,.8,(x,49.7*sign,18),(0,sign,0)))
        fixed=fixed.fuse(shaft).fuse(inner).fuse(outer)
        p=A.Placement(V(x,34*sign,18),A.Rotation(V(0,0,1),axis))
        w=wheel.copy();w.Placement=p.multiply(w.Placement);wheels.append((end+side+'Wheel',w))
        # A rotationally invariant, conservative 360-degree envelope.
        env=cyl(18,12,(0,0,0)).fuse(cyl(13.7,1.2,(0,0,12))).cut(cyl(3,14,(0,0,-.1)))
        env.Placement=p.multiply(env.Placement);sweeps.append((end+side,env))
fixed=fixed.removeSplitter()
assert fixed.isValid() and len(fixed.Solids)==1,('fixed',len(fixed.Solids))
A.closeDocument(g['doc'].Name);doc=A.newDocument('ApexRacerPrintInPlace')
scene={'meshes':{},'instances':[],'version':'print-in-place','print_in_place':True}
def add(name,shape,color):
    obj=doc.addObject('PartDesign::Feature',name);obj.Shape=shape
    obj.addProperty('App::PropertyColor','DesignColor','Print').DesignColor=color
    obj.addProperty('App::PropertyString','Assembly','Print').Assembly='Print together in one job; do not auto-arrange separate shells'
    m=MeshPart.meshFromShape(Shape=shape,LinearDeflection=.10,AngularDeflection=.17,Relative=False)
    pts,tri=m.Topology;scene['meshes'][name]={'vertices':[[p.x/1000,p.y/1000,p.z/1000] for p in pts],'triangles':tri}
    scene['instances'].append({'name':name,'mesh':name,'color':color,'pose':{'xyz_mm':[0,0,0],'quaternion_xyzw':[0,0,0,1]}})
    return obj
add('IntegratedBody',fixed,(.72,.035,.055))
for name,w in wheels:add(name,w,(.11,.12,.14))
doc.recompute();doc.saveAs(str(ROOT/'apex_racer.FCStd'))
Part.export(doc.Objects,str(ROOT/'apex_racer.step'))
# Same render geometry, shown in red to represent a single-material print.
for inst in scene['instances']:inst['color']=(.72,.035,.055)
(ROOT/'scene.json').write_text(json.dumps(scene,separators=(',',':')))
assembled=Part.makeCompound([fixed]+[s for _,s in wheels])
printshape=assembled.copy();printshape.rotate(V(0,0,0),V(1,0,0),90)
printshape.translate(V(0,0,-printshape.BoundBox.ZMin))
mesh=MeshPart.meshFromShape(Shape=printshape,LinearDeflection=.10,AngularDeflection=.17,Relative=False)
mesh.write(str(OUT/'apex_racer_side_down.stl'))
assert mesh.isSolid()
side_scene={'meshes':{},'instances':[]}
for name,s in [('IntegratedBody',fixed)]+wheels:
    t=s.copy();t.rotate(V(0,0,0),V(1,0,0),90);t.translate(V(0,0,54))
    mm=MeshPart.meshFromShape(Shape=t,LinearDeflection=.12,AngularDeflection=.2,Relative=False)
    pts,tri=mm.Topology;side_scene['meshes'][name]={'vertices':[[p.x/1000,p.y/1000,p.z/1000] for p in pts],'triangles':tri}
    side_scene['instances'].append({'name':name,'mesh':name,'color':(.72,.035,.055),'pose':{'xyz_mm':[0,0,0],'quaternion_xyzw':[0,0,0,1]}})
(OUT/'side_scene.json').write_text(json.dumps(side_scene,separators=(',',':')))
report={'mode':'Single print job with captive rotating wheels','rigid_bodies':5,'stl_files_required':1,'radial_axle_clearance_mm':.5,'inner_axial_clearance_mm':.5,'outer_head_root_axial_clearance_mm':.5,'wheel_360_sweep_checks':[], 'all_shapes_valid':True,'stl_closed':True,'physical_print_test':False,'print_bounds_mm':[printshape.BoundBox.XLength,printshape.BoundBox.YLength,printshape.BoundBox.ZLength]}
for name,env in sweeps:
    overlap=env.common(fixed).Volume
    clearance=env.distToShape(fixed)[0]
    report['wheel_360_sweep_checks'].append({'wheel':name,'conservative_envelope_overlap_mm3':overlap,'min_clearance_mm':clearance})
    assert overlap<.01 and clearance>.39,(name,overlap,clearance)
for i,(n,a) in enumerate(wheels):
    for m,b in wheels[i+1:]:assert not a.BoundBox.intersect(b.BoundBox)
(OUT/'validation_report.json').write_text(json.dumps(report,indent=2))
(ROOT/'validation_report.json').write_text(json.dumps(report,indent=2))
(ROOT/'build_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
