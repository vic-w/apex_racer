from pathlib import Path
import json,zipfile
import FreeCAD as A
import Mesh
root=Path(__file__).resolve().parents[1]
with zipfile.ZipFile(root/'apex_racer.FCStd') as z:assert 'GuiDocument.xml' in z.namelist()
doc=A.openDocument(str(root/'apex_racer.FCStd'));assert len(doc.Objects)==3
assert all(o.Shape.isValid() and len(o.Shape.Solids)==1 for o in doc.Objects)
m=Mesh.Mesh(str(root/'print_in_place/apex_racer_side_down.stl'));assert m.isSolid()
m3=Mesh.Mesh(str(root/'apex_racer.3mf'));assert m3.isSolid()
report=json.loads((root/'validation_report.json').read_text());assert report['rigid_bodies']==3
assert all(r['conservative_envelope_overlap_mm3']<.01 for r in report['wheel_360_sweep_checks'])
with zipfile.ZipFile(root/'apex_racer_print_pack.zip') as z:assert len([p for p in z.namelist() if p.endswith('.stl')])==1
print('Saved CAD: 3 valid solids with GUI state. STL and 3MF are closed. Two full-rotation axle checks passed.')
