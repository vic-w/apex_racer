from pathlib import Path
import json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1]
scene=json.loads((root/'scene.json').read_text())
pip=scene.get('print_in_place',False)
dumbbell=scene.get('dumbbell_axles',False)
side_scene=json.loads((root/('print_in_place/mechanism_scene.json' if dumbbell else 'print_in_place/side_scene.json')).read_text()) if pip else scene
if pip and not dumbbell:
    side_scene['meshes']['bed']={'vertices':[[-.11,-.08,-.0003],[.11,-.08,-.0003],[.11,.01,-.0003],[-.11,.01,-.0003]],'triangles':[[0,1,2],[0,2,3]]}
    side_scene['instances'].append({'name':'bed','mesh':'bed','color':[.63,.67,.72],'pose':{'xyz_mm':[0,0,0],'quaternion_xyzw':[0,0,0,1]}})
def rot(q):
    x,y,z,w=q
    return np.array([[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]])
im=Image.new('RGB',(1800,1250),(228,232,237));d=ImageDraw.Draw(im)
def font(n):return ImageFont.truetype('C:/Windows/Fonts/arial.ttf',n)
d.text((65,40),'APEX  /  GT-01',font=font(54),fill=(28,37,49))
length_mm=json.loads((root/'print_in_place/validation_report.json').read_text())['print_bounds_mm'][0] if dumbbell else 200
d.text((68,108),f'{length_mm:.1f} mm  |  '+('ONE PRINT / DUMBBELL AXLES' if dumbbell else 'ONE PRINT / ROTATING WHEELS' if pip else 'MULTIPART PRINTABLE RACER'),font=font(21),fill=(85,98,113))
views=[(.75,.40,920,475,4600),(.75,.70,555,985,2700) if dumbbell else (.75,.48,555,1060,2400) if pip else (2.55,.38,565,1010,3500)]
for index,(az,el,ox,oy,scale) in enumerate(views):
    viewscene=side_scene if index==1 else scene
    pixels=np.array(im);depth=np.full((1250,1800),-np.inf)
    n=np.array([math.cos(el)*math.cos(az),math.cos(el)*math.sin(az),math.sin(el)])
    u=np.cross([0,0,1],n);u/=np.linalg.norm(u);v=np.cross(n,u);project=np.array([u,v,n]);triangles=[]
    for inst in viewscene['instances']:
        mesh=viewscene['meshes'][inst['mesh']];pts=np.array(mesh['vertices'])@rot(inst['pose']['quaternion_xyzw']).T+np.array(inst['pose']['xyz_mm'])/1000
        q=(pts-np.array([0,0,.023]))@project.T;faces=np.array(mesh['triangles'],dtype=int)
        ns=np.cross(pts[faces[:,1]]-pts[faces[:,0]],pts[faces[:,2]]-pts[faces[:,0]])
        lens=np.linalg.norm(ns,axis=1);lens[lens==0]=1;ns/=lens[:,None]
        smooth=np.zeros_like(pts)
        for j in range(3):np.add.at(smooth,faces[:,j],ns)
        sl=np.linalg.norm(smooth,axis=1);sl[sl==0]=1;smooth/=sl[:,None]
        light=.42+.58*np.maximum(0,smooth@np.array([.35,.25,.903]))
        spec=np.maximum(0,smooth@((n+np.array([.35,.25,.903]))/np.linalg.norm(n+np.array([.35,.25,.903]))))**28
        for i,f in enumerate(faces):
            if ns[i]@n<=0:continue
            color=np.clip(np.array(inst['color'])[None,:]*255*light[f,None]+spec[f,None]*45,0,255)
            t=q[f].copy();t[:,0]=ox+t[:,0]*scale;t[:,1]=oy-t[:,1]*scale
            xmin=max(0,int(np.floor(t[:,0].min())));xmax=min(1799,int(np.ceil(t[:,0].max())))
            ymin=max(0,int(np.floor(t[:,1].min())));ymax=min(1249,int(np.ceil(t[:,1].max())))
            if xmax<xmin or ymax<ymin:continue
            x,y=np.meshgrid(np.arange(xmin,xmax+1)+.5,np.arange(ymin,ymax+1)+.5)
            a,b,c=t;den=(b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
            if abs(den)<1e-10:continue
            wa=((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
            wb=((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den;wc=1-wa-wb
            z=wa*a[2]+wb*b[2]+wc*c[2];region=depth[ymin:ymax+1,xmin:xmax+1]
            mask=(wa>=0)&(wb>=0)&(wc>=0)&(z>region)
            rgb=wa[:,:,None]*color[0]+wb[:,:,None]*color[1]+wc[:,:,None]*color[2]
            pixels[ymin:ymax+1,xmin:xmax+1][mask]=rgb[mask].astype(np.uint8);region[mask]=z[mask]
    im=Image.fromarray(pixels);d=ImageDraw.Draw(im)
d.text((1120,900),'PRINT IN PLACE' if pip else 'PRINT / ASSEMBLE',font=font(29),fill=(36,48,62))
lines=['Two one-piece wheel axles','1.0 mm bearing / 1.5 mm arch','2 mm longitudinal wing plates','Chassis section shown at left'] if dumbbell else ['One STL / one print job','4 captive rotating wheels','0.5 mm axle clearance','Side-down / local supports'] if pip else ['01  Sculpted body + canopy','02  Wing with swept towers','03  Four tires, rims and pins','Flat bases / glue-fit assembly']
for i,line in enumerate(lines):d.text((1120,955+i*46),line,font=font(22),fill=(82,96,111))
im.save(root/'apex_racer_preview.png')
print('Preview saved')
