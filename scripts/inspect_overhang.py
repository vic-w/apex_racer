from pathlib import Path
import json,math
import FreeCAD as A
import Part
r=Path('apex_racer');d=A.openDocument(str(r/'apex_racer.FCStd'));s=d.getObject('IntegratedBody').Shape
v=json.loads((r/'validation_report.json').read_text())
for p in v['overhang_audit'][0]['largest_facets']:
    q=A.Vector(*p[:3]);vert=Part.Vertex(q)
    dist,f=min((f.distToShape(vert)[0],i) for i,f in enumerate(s.Faces));face=s.Faces[f]
    u,w=face.Surface.parameter(q);n=face.normalAt(u,w)
    print(p,'distance',dist,'surface',type(face.Surface).__name__,'normalY',n.y)
