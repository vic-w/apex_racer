from pathlib import Path
import json

import FreeCAD as A
import Part
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
doc = A.openDocument(str(root / 'apex_racer.FCStd'))
report = json.loads((root / 'print_in_place/validation_report.json').read_text())['bed_contact']
image = Image.new('RGB', (1600, 820), '#f5f7f8')
draw = ImageDraw.Draw(image)
font = lambda size: ImageFont.truetype('C:/Windows/Fonts/arial.ttf', size)

def project(point):
    return (800 + point.x * 6.4, 605 - point.z * 6.4)

def paint(shape, color):
    vertices, triangles = shape.tessellate(.05)
    for triangle in triangles:
        draw.polygon([project(vertices[i]) for i in triangle], fill=color)

draw.text((70, 38), 'APEX / GT-01 - BED CONTACT', font=font(38), fill='#263238')
draw.text((70, 100), 'Side-down orientation | 0.20 mm first-layer slab',
          font=font(23), fill='#53636a')
for x in range(-100, 101, 10):
    draw.line((800+x*6.4, 200, 800+x*6.4, 650), fill='#e2e7e9')
for z in range(0, 61, 10):
    draw.line((120, 605-z*6.4, 1480, 605-z*6.4), fill='#e2e7e9')

for obj in doc.Objects:
    paint(obj.Shape, '#d9dfe2')
layer = Part.makeBox(220, .2, 80, A.Vector(-110, -47, -5))
for obj in doc.Objects:
    color = '#178975' if obj.Name == 'IntegratedBody' else '#66747d'
    paint(obj.Shape.common(layer), color)

nose = doc.getObject('IntegratedBody').Shape.common(
    Part.makeBox(25, 96, 70, A.Vector(80, -48, 0)))
for face in nose.Faces:
    if abs(face.BoundBox.YMin+47) < 1e-6 and abs(face.BoundBox.YMax+47) < 1e-6:
        paint(face, '#dca82e')

area = report['nose_planar_contact_mm2']
draw.text((1010, 155), f'Widened nose: {area:.1f} mm2', font=font(26), fill='#725316')
draw.line((1325, 192, 1370, 510), fill='#9b751e', width=3)
draw.text((150, 665), 'REAR', font=font(21), fill='#53636a')
draw.text((1370, 665), 'FRONT', font=font(21), fill='#53636a')
for x, color, label in [(100, '#178975', 'Body first layer'),
                        (580, '#66747d', 'Wheel first layer'),
                        (1060, '#dca82e', 'Nose planar contact')]:
    draw.rectangle((x, 745, x+22, 767), fill=color)
    draw.text((x+35, 740), label, font=font(24), fill='#263238')
image.save(root / 'print_in_place/bed_contact_preview.png')
print('Bed contact preview saved')
