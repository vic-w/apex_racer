from pathlib import Path
import json
import FreeCAD as A
import Part,Mesh
root=Path(__file__).resolve().parents[1]
doc=A.openDocument(str(root/'apex_racer.FCStd'))
report={'mesh_checks':{},'assembly_intersections':[]}
for p in (root/'stl').glob('*.stl'):
    m=Mesh.Mesh(str(p))
    closed=m.isSolid()
    assert closed,p.name
    assert m.CountFacets>0 and max(m.BoundBox.XLength,m.BoundBox.YLength,m.BoundBox.ZLength)<210
    report['mesh_checks'][p.name]={'closed':closed,'facets':m.CountFacets,'millimetres':True}
objects=doc.Objects
for i,a in enumerate(objects):
    assert a.Shape.isValid() and len(a.Shape.Solids)==1,a.Name
    for b in objects[i+1:]:
        if a.Shape.BoundBox.intersect(b.Shape.BoundBox):
            volume=a.Shape.common(b.Shape).Volume
            if volume>.05:report['assembly_intersections'].append([a.Name,b.Name,volume])
assert not report['assembly_intersections'],report['assembly_intersections']
report['assembled_parts']=len(objects)
report['physical_print_test']=False
(root/'validation_report.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2),flush=True)
