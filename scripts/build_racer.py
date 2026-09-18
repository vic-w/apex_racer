from pathlib import Path
import math,json
import FreeCAD as A
import Part,MeshPart
V=A.Vector
ROOT=Path(__file__).resolve().parents[1]
doc=A.newDocument('ApexRacer')
def box(x,y,z,a,b,c):return Part.makeBox(a,b,c,V(x,y,z))
def cyl(r,h,p,axis=(0,0,1)):return Part.makeCylinder(r,h,V(*p),V(*axis))
def polygon(points):return Part.makePolygon([V(*p) for p in points+[points[0]]])
def roundrect(cx,cy,z,l,w,r=4):
    s=Part.makePlane(l,w,V(cx-l/2,cy-w/2,z))
    # Planar rounded rectangle from exact tangent lines and quarter arcs.
    x0,x1=cx-l/2,cx+l/2;y0,y1=cy-w/2,cy+w/2
    pts=[(x0+r,y0),(x1-r,y0),(x1,y0+r),(x1,y1-r),(x1-r,y1),(x0+r,y1),(x0,y1-r),(x0,y0+r)]
    edges=[]
    centers=[(x1-r,y0+r),(x1-r,y1-r),(x0+r,y1-r),(x0+r,y0+r)]
    for i in range(4):
        a,b,c=pts[2*i],pts[2*i+1],pts[(2*i+2)%8]
        edges.append(Part.makeLine(V(*a,z),V(*b,z)))
        cx1,cy1=centers[i];u=V(b[0]-cx1,b[1]-cy1,0);v=V(c[0]-cx1,c[1]-cy1,0)
        mid=V(cx1,cy1,z)+(u+v).normalize()*r
        edges.append(Part.Arc(V(*b,z),mid,V(*c,z)).toShape())
    return Part.Wire(edges)

def section(x,w,h,shoulder):
    coords=[(-w,12),(-.98*w,23),(-.86*w,shoulder-1),(-.72*w,shoulder),(-.48*w,h+1),(0,h),(.48*w,h+1),(.72*w,shoulder),(.86*w,shoulder-1),(.98*w,23),(w,12)]
    c=Part.BSplineCurve();c.interpolate([V(x,y,z) for y,z in coords])
    e=[c.toShape(),Part.makeLine(V(x,w,12),V(x,w-5,5)),Part.makeLine(V(x,w-5,5),V(x,-w+5,5)),Part.makeLine(V(x,-w+5,5),V(x,-w,12))]
    return Part.Wire(e)
sections=[(-100,32,26,27),(-93,40,31,33),(-65,46,30,39),(-30,41,29,33),(0,40,29,32),(35,43,28,34),(63,46,27,39),(85,42,23,31),(100,31,19,24)]
body=Part.makeLoft([section(*s) for s in sections],True,False)
assert body.isValid()
body_raw=body.copy()
# Wheel wells open to the side and underside; solid central chassis carries axles.
for x in (-63,63):
    for sign in (-1,1):
        body=body.cut(cyl(18.8,35,(x,28*sign,18),(0,sign,0)))
        body=body.cut(cyl(2.2,12,(x,19*sign,18),(0,sign,0)))
# Flat-bottom canopy pocket with glue clearance.
pocket=Part.Face(roundrect(-6,0,26.6,82.5,52.5,9.25)).extrude(V(0,0,40))
body=body.cut(pocket)
canopy=Part.makeLoft([roundrect(-6,0,26.8,82,52,9),roundrect(-9,0,38,66,46,10),roundrect(-11,0,47,42,34,10),roundrect(-11,0,49,32,28,9)],True,False)
# Canopy is a single dark printed insert with a flat base.
# Sculpted nose intake pockets and a central splitter, all actual geometry.
for sign in (-1,1):
    intake=box(91,sign*14-9,9,15,18,7)
    body=body.cut(intake)
    # Diagonal recessed headlight ribbon, suitable for painting after printing.
    lamp=box(0,-7,0,16,2.2,4)
    lamp.rotate(V(0,0,0),V(0,0,1),sign*20)
    lamp.translate(V(77,sign*26,29))
    body=body.cut(lamp)
    # Bonnet vents, behind the front axle and outside the glass insert.
    for k in range(3):
        body=body.cut(box(38+k*4.5,sign*25-3,29,2.0,6,10))
    # Rear taillamp recesses and side sill air channels.
    body=body.cut(box(-103,sign*22-12,23,7,24,2.2))
    body=body.cut(box(-27,sign*40-2,11,49,4,6))
# Underbody diffuser channels exit the tail.
for y in (-24,-12,0,12,24):body=body.cut(box(-102,y-3,5,18,6,4))
# Two tapered, swept wing towers; horizontal top pegs locate the separate wing.
for y in (-24,24):
    tower=Part.makeLoft([roundrect(-66,y,28,9,7,1),roundrect(-76,y,57.7,5,5,1)],True,True)
    body=body.fuse(tower).fuse(box(-78.2,y-2.2,57.5,4.4,4.4,3.2))
body=body.removeSplitter()
# Rear wing prints flat: swept outline, thick blade and upright endplates.
wingwire=polygon([(-91,-54,58),(-69,-54,58),(-63,-39,58),(-66,0,58),(-63,39,58),(-69,54,58),(-91,54,58),(-85,0,58)])
wing=Part.Face(wingwire).extrude(V(0,0,3.2))
for y in (-24,24):wing=wing.cut(box(-78.45,y-2.45,57,4.9,4.9,6))
for y in (-54,51.6):
    end=Part.Face(polygon([(-91,y,58),(-69,y,58),(-69,y,65),(-75,y,69),(-91,y,67)])).extrude(V(0,2.4,0))
    wing=wing.fuse(end)
wing=wing.removeSplitter()
# Separate tire and metallic rim. All printable on their flat inner faces.
tire=cyl(18,12,(0,0,0)).cut(cyl(13.25,12,(0,0,0)))
try:
    outer=[e for e in tire.Edges if e.Length>110]
    tire=tire.makeFillet(.8,outer)
except Exception:pass
for z in (3.5,8.5):
    ring=cyl(18.1,.7,(0,0,z)).cut(cyl(17.3,.7,(0,0,z)))
    tire=tire.cut(ring)
rim=cyl(13,1.8,(0,0,0)).fuse(cyl(5,12,(0,0,0)))
rim=rim.fuse(cyl(13,12,(0,0,0)).cut(cyl(11.6,12,(0,0,0))))
rim=rim.fuse(cyl(13.7,1.2,(0,0,12)).cut(cyl(11.6,1.2,(0,0,12))))
for i in range(10):
    spoke=Part.Face(polygon([(3,-.9,1.6),(12,-.2,1.6),(12,1.4,1.6),(3,.9,1.6)])).extrude(V(0,0,10.4))
    spoke.rotate(V(0,0,0),V(0,0,1),i*36)
    rim=rim.fuse(spoke)
rim=rim.cut(cyl(2.2,15,(0,0,-.5))).removeSplitter()
pin=cyl(2,24,(0,0,0))

if __name__ == '__main__':
    scene={'meshes':{},'instances':[]} ;report={'units':'mm','parts':{},'assembly_count':15,'notes':['Static display model; glue assembly; no RC or drivetrain','Nominal pin/hole diameters 4.0/4.4 mm; check printer fit','Body needs localized supports at wheel arches; other parts print on flat bases']}
    colors={'body':(.72,.035,.055),'canopy':(.065,.10,.13),'wing':(.10,.12,.15),'tire':(.045,.05,.06),'rim':(.65,.69,.74),'pin':(.25,.28,.32)}
    source={'body':body,'canopy':canopy,'wing':wing,'tire':tire,'rim':rim,'pin':pin}
    for name,shape in source.items():
        assert shape.isValid() and len(shape.Solids)==1,(name,shape.isValid(),len(shape.Solids))
        local=shape.copy();local.translate(V(0,0,-shape.BoundBox.ZMin))
        mesh=MeshPart.meshFromShape(Shape=local,LinearDeflection=.10,AngularDeflection=.17,Relative=False)
        mesh.write(str(ROOT/'stl'/(name+'.stl')))
        pts,tris=mesh.Topology
        scene['meshes'][name]={'vertices':[[v.x/1000,v.y/1000,v.z/1000] for v in pts],'triangles':tris}
        report['parts'][name]={'valid_solid':True,'solid_count':1,'triangles':len(tris),'volume_mm3':shape.Volume,'print_bounds_mm':[local.BoundBox.XLength,local.BoundBox.YLength,local.BoundBox.ZLength],'quantity':4 if name in ('tire','rim','pin') else 1}
    def instance(name,kind,p):
        s=source[kind].copy()
        obj=doc.addObject('PartDesign::Feature',name);obj.Shape=s
        obj.Placement=p.multiply(A.Placement(V(0,0,-s.BoundBox.ZMin),A.Rotation()))
        obj.addProperty('App::PropertyColor','DesignColor','Print').DesignColor=colors[kind]
        obj.addProperty('App::PropertyString','PrintFile','Print').PrintFile='stl/'+kind+'.stl'
        obj.addProperty('App::PropertyString','Assembly','Print').Assembly='Glue fit; decorative model'
        scene['instances'].append({'name':name,'mesh':kind,'color':colors[kind],'pose':{'xyz_mm':[p.Base.x,p.Base.y,p.Base.z],'quaternion_xyzw':list(p.Rotation.Q)}})
        return obj
    instance('Body','body',A.Placement(V(0,0,5),A.Rotation()))
    instance('Canopy','canopy',A.Placement(V(0,0,26.8),A.Rotation()))
    instance('RearWing','wing',A.Placement(V(0,0,58),A.Rotation()))
    for x,end in [(-63,'Rear'),(63,'Front')]:
        for sign,side in [(1,'Left'),(-1,'Right')]:
            rot=A.Rotation(V(0,0,1),V(0,sign,0))
            for kind in ('tire','rim'):instance(end+side+kind,kind,A.Placement(V(x,34*sign,18),rot))
            instance(end+side+'Axle','pin',A.Placement(V(x,22*sign,18),rot))
    doc.recompute();doc.saveAs(str(ROOT/'apex_racer.FCStd'))
    Part.export([o for o in doc.Objects if hasattr(o,'Shape')],str(ROOT/'apex_racer.step'))
    (ROOT/'scene.json').write_text(json.dumps(scene,separators=(',',':')))
    (ROOT/'build_report.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)
