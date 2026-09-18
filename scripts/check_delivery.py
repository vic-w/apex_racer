from pathlib import Path
import json,zipfile
import FreeCAD as A
import Mesh,Part
root=Path(__file__).resolve().parents[1]
with zipfile.ZipFile(root/'apex_racer.FCStd') as z:assert 'GuiDocument.xml' in z.namelist()
doc=A.openDocument(str(root/'apex_racer.FCStd'));assert len(doc.Objects)==3
assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in doc.Objects)
m=Mesh.Mesh(str(root/'print_in_place/apex_racer_side_down.stl'));assert m.isSolid()
m3=Mesh.Mesh(str(root/'apex_racer.3mf'));assert m3.isSolid()
assert abs(m.BoundBox.ZMin)<1e-5 and abs(m3.BoundBox.ZMin)<1e-5
assert m.CountFacets==m3.CountFacets
# Allow one micron for decimal-coordinate rounding in the 3MF export.
assert all(abs(getattr(m.BoundBox,k)-getattr(m3.BoundBox,k))<.001
           for k in ('XMin','XMax','YMin','YMax','ZMin','ZMax'))
report=json.loads((root/'print_in_place/validation_report.json').read_text());assert report['rigid_bodies']==3
assert all(r['conservative_envelope_overlap_mm3']<.01 for r in report['wheel_360_sweep_checks'])
body=doc.getObject('IntegratedBody').Shape
nose=body.common(Part.makeBox(25,96,70,A.Vector(80,-48,0)))
contact=sum(f.Area for f in nose.Faces
            if abs(f.BoundBox.YMin+47)<1e-6 and abs(f.BoundBox.YMax+47)<1e-6)
assert contact>150,('nose_bed_contact_mm2',contact)
assert abs(contact-report['bed_contact']['nose_planar_contact_mm2'])<.01
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
