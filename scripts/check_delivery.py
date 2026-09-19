from pathlib import Path
import hashlib,json,zipfile
import FreeCAD as A
import Mesh,Part,MeshPart
from sports_coupe import MODEL_SCALE,check_packaging,check_cabin_surface,check_fender_coverage,check_rear_transition
from body_surface import check_corners,check_fairness,check_end_profiles
from headlights import check_headlights
root=Path(__file__).resolve().parents[1]
with zipfile.ZipFile(root/'apex_racer.FCStd') as z:assert 'GuiDocument.xml' in z.namelist()
doc=A.openDocument(str(root/'apex_racer.FCStd'));assert len(doc.Objects)==3
assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in doc.Objects)
m=Mesh.Mesh(str(root/'print_in_place/apex_racer_side_down.stl'));assert m.isSolid()
m3=Mesh.Mesh(str(root/'apex_racer.3mf'));assert m3.isSolid()
assert abs(m.BoundBox.ZMin)<1e-5 and abs(m3.BoundBox.ZMin)<1e-5
assert all(v<=180 for v in (m.BoundBox.XLength,m.BoundBox.YLength,m.BoundBox.ZLength)), 'A1 mini build volume'
assert m.CountFacets==m3.CountFacets
# Allow one micron for decimal-coordinate rounding in the 3MF export.
assert all(abs(getattr(m.BoundBox,k)-getattr(m3.BoundBox,k))<.001
           for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))
report=json.loads((root/'print_in_place/validation_report.json').read_text());assert report['rigid_bodies']==3
assert abs(report['model_scale']-MODEL_SCALE)<1e-9 and report['a1_mini_bed_fit']
if 'slicing_check' in report:
    slicing=report['slicing_check']
    assert slicing['slicing_succeeded'] and not slicing['support_toolpaths']
    assert slicing['stl_sha256']==hashlib.sha256((root/'print_in_place/apex_racer_side_down.stl').read_bytes()).hexdigest()
assert all(r['conservative_envelope_overlap_mm3']<.01 for r in report['wheel_360_sweep_checks'])
body=doc.getObject('IntegratedBody').Shape
headlights=check_headlights(body,MODEL_SCALE)
assert headlights['count']==report['headlights']['count']==2
assert len(doc.getObject('IntegratedBody').HeadlampLensFaces)>=2
assert len(doc.getObject('IntegratedBody').HeadlampBezelFaces)>=2
corners=check_corners(body,MODEL_SCALE)
assert len(corners['checks'])==4
end_profiles=check_end_profiles(body,MODEL_SCALE)
for end in ('front','rear'):
    assert abs(end_profiles[end]['terminal_thickness_mm']-
               report['end_profiles'][end]['terminal_thickness_mm'])<.01
saved_surface=next(face.Surface for face in body.Faces
                   if isinstance(face.Surface,Part.BSplineSurface)
                   and face.Surface.NbUPoles==11 and face.Surface.NbVPoles==9)
fairness=check_fairness(saved_surface,MODEL_SCALE,MODEL_SCALE)
assert abs(fairness['max_bonnet_to_fender_height_difference_mm']-
           report['body_surface_fairness']['max_bonnet_to_fender_height_difference_mm'])<.01
fenders=check_fender_coverage(body,MODEL_SCALE)
rear_transition=check_rear_transition(body,MODEL_SCALE)
assert len(fenders['checks'])==4
for measured,recorded in zip(fenders['checks'],report['fender_coverage']['checks']):
    assert abs(measured['min_sampled_shell_thickness_mm']-recorded['min_sampled_shell_thickness_mm'])<.01
packaging=check_packaging(body,MODEL_SCALE)
assert len(packaging['checks'])==2
cabin=report['cabin']
assert cabin['fixed_door_count']==2 and len(cabin['details'])==10
assert all(detail['removed_volume_mm3']>.1 for detail in cabin['details'])
surface=check_cabin_surface(body,MODEL_SCALE)
assert abs(surface['upper_glazing_width_mm']-cabin['surface_measurements']['upper_glazing_width_mm'])<.01
assert abs(surface['side_window_sill_above_print_bed_mm']-cabin['surface_measurements']['side_window_sill_above_print_bed_mm'])<.01
assert all(p['minimum_window_recess_separation_mm']>MODEL_SCALE for p in cabin['pillars'])
assert abs(m.BoundBox.YLength-cabin['roof_height_mm'])<.1
wing=body.common(Part.makeBox(35*MODEL_SCALE,96*MODEL_SCALE,11*MODEL_SCALE,
                              A.Vector(-101*MODEL_SCALE,-48*MODEL_SCALE,41*MODEL_SCALE)))
wing_mesh=MeshPart.meshFromShape(Shape=wing,LinearDeflection=.01,AngularDeflection=.08,Relative=False)
assert abs(wing_mesh.BoundBox.ZMax-report['rear_spoiler']['top_z_mm'])<.05
wing_contact=wing.common(Part.makeBox(220*MODEL_SCALE,.2,80*MODEL_SCALE,
                                      A.Vector(-110*MODEL_SCALE,-47*MODEL_SCALE,0))).Volume/.2
assert wing_contact>30 and abs(wing_contact-report['rear_spoiler']['first_layer_mean_area_mm2'])<.01
wing_planar=sum(f.Area for f in wing.Faces
                if abs(f.BoundBox.YMin+47*MODEL_SCALE)<1e-6
                and abs(f.BoundBox.YMax+47*MODEL_SCALE)<1e-6)
assert abs(wing_planar-report['rear_spoiler']['planar_contact_mm2'])<.01
# Probe recesses on both sides of the saved CAD, independently of render colours.
for sign in (-1,1):
    assert body.isInside(A.Vector(0,sign*46*MODEL_SCALE,12.8*MODEL_SCALE),1e-6,True)
    assert not body.isInside(A.Vector(0,sign*46.7*MODEL_SCALE,11.5*MODEL_SCALE),1e-6,True)
    assert body.isInside(A.Vector(0,sign*45.8*MODEL_SCALE,11.5*MODEL_SCALE),1e-6,True)
# Measure the actual contact plane in the scaled saved model.
nose=body.common(Part.makeBox(25*MODEL_SCALE,96*MODEL_SCALE,70*MODEL_SCALE,
                              A.Vector(80*MODEL_SCALE,-48*MODEL_SCALE,0)))
contact=sum(f.Area for f in nose.Faces
            if abs(f.BoundBox.YMin+47*MODEL_SCALE)<1e-6
            and abs(f.BoundBox.YMax+47*MODEL_SCALE)<1e-6)
assert contact>150*MODEL_SCALE**2,('nose_bed_contact_mm2',contact)
assert abs(contact-report['bed_contact']['nose_planar_contact_mm2'])<.01
rear=body.common(Part.makeBox(21*MODEL_SCALE,96*MODEL_SCALE,38*MODEL_SCALE,
                              A.Vector(-101*MODEL_SCALE,-48*MODEL_SCALE,0)))
rear_contact=sum(f.Area for f in rear.Faces
                 if abs(f.BoundBox.YMin+47*MODEL_SCALE)<1e-6
                 and abs(f.BoundBox.YMax+47*MODEL_SCALE)<1e-6)
assert rear_contact>25 and abs(rear_contact-report['bed_contact']['rear_body_planar_contact_mm2'])<.01
# Verify that export did not lift contact patches off the bed or alter the CAD.
cad_print=Part.makeCompound([o.Shape for o in doc.Objects])
cad_print.rotate(A.Vector(),A.Vector(1,0,0),90)
cad_print.translate(A.Vector(0,0,47*MODEL_SCALE))
cad_mesh=MeshPart.meshFromShape(Shape=cad_print,LinearDeflection=.025,AngularDeflection=.08,Relative=False)
# Reloading curved BReps can change tessellation; compare solids and dimensions.
components=m.getSeparateComponents()
assert len(components)==3 and all(c.isSolid() for c in components)
for measured,expected in zip(sorted(abs(c.Volume) for c in components),
                             sorted(abs(c.Volume) for c in cad_mesh.getSeparateComponents())):
    assert abs(measured-expected)/expected<.0001,(measured,expected)
assert all(abs(getattr(m.BoundBox,k)-getattr(cad_mesh.BoundBox,k))<.001
           for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))
if (root/'apex_racer_print_pack.zip').exists():
    with zipfile.ZipFile(root/'apex_racer_print_pack.zip') as z:
        assert z.testzip() is None
        assert len([p for p in z.namelist() if p.endswith('.stl')])==1
        for name in ('apex_racer_side_down.stl','README.md','validation_report.json',
                     'bed_contact_preview.png'):
            assert z.read(name)==(root/'print_in_place'/name).read_bytes(),name
    print('Local print archive matches the current print files.')
print('Saved CAD: 3 valid solids with GUI state. STL and 3MF are closed. Two full-rotation axle checks passed.')
print('Stationary nose contact on the print bed: {:.1f} mm2.'.format(contact))
print('Rear body contact near the wheel: {:.1f} mm2.'.format(rear_contact))
print('Two occupant reference envelopes fit; both fixed door grooves are present in the saved CAD.')
print('All four fenders cover the upper tire tread with clearance; rear cabin transition has no steep step.')
print('Fair main skin: no extra longitudinal valleys. All four square bumper corners are removed.')
print('Both swept headlights have real recessed bezels and integral curved lens faces.')
print('Tapered end thickness: front {:.2f} mm; rear {:.2f} mm.'.format(
    end_profiles['front']['terminal_thickness_mm'],end_profiles['rear']['terminal_thickness_mm']))
print('Roof: {:.1f} mm; rear wing: {:.1f} mm; wing bed contact: {:.1f} mm2.'.format(
    cabin['roof_height_mm'],wing_mesh.BoundBox.ZMax,wing_contact))
