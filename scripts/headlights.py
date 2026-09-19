"""Headlights wrapping around the bonnet/front/side junctions."""

import math
import FreeCAD as A
import Part
from body_surface import make_body, rounded_planform

V = A.Vector
BEZEL_DEPTH = .65
LENS_DEPTH = .18
BEZEL_WIDTH = .9


def lamp_outline():
    """A swept ribbon in the diagonal corner's elevation plane."""
    curves = []
    for points in [[(-22, 15), (-15, 23), (8, 38), (15, 32)],
                   [(15, 32), (7, 27), (-16, 12), (-22, 15)]]:
        curve = Part.BezierCurve()
        curve.setPoles([V(u, z, 0) for u, z in points])
        curves.append(curve.toShape())
    outer = Part.Wire(curves)
    inner = outer.makeOffset2D(-BEZEL_WIDTH)
    if Part.Face(inner).Area > Part.Face(outer).Area:
        inner = outer.makeOffset2D(BEZEL_WIDTH)
    assert inner.isClosed() and Part.Face(inner).Area < Part.Face(outer).Area
    return Part.Face(outer), Part.Face(inner)


def corner_tool(footprint, sign):
    tangent = V(-1, sign, 0)/math.sqrt(2)
    normal = V(1, sign, 0)/math.sqrt(2)
    origin = V(94, sign*39, 0)-normal*40
    matrix = A.Matrix()
    matrix.A11, matrix.A21, matrix.A31 = tangent.x, tangent.y, tangent.z
    matrix.A12, matrix.A22, matrix.A32 = 0, 0, 1
    matrix.A13, matrix.A23, matrix.A33 = normal.x, normal.y, normal.z
    matrix.A14, matrix.A24, matrix.A34 = origin.x, origin.y, origin.z
    plane = footprint.transformGeometry(matrix)
    return plane.extrude(normal*80)


def reference_skin(bonnet):
    return bonnet.common(rounded_planform()).removeSplitter()


def floor_for(skin, tool, sign, depth):
    shifted = skin.copy()
    shifted.translate(V(-depth, -sign*depth, -depth))
    floor = Part.makeCompound(shifted.Faces).common(tool)
    return shifted, floor


def add_headlights(body, bonnet):
    # An intact reference shell limits the cuts to the exterior skin, including
    # the front and side faces. Wheel cavities cannot create secondary cuts.
    skin = reference_skin(bonnet)
    floors = {'lamp_bezels': [], 'lamp_lenses': []}
    outer, inner = lamp_outline()
    for sign, side in [(-1, 'left'), (1, 'right')]:
        for name, footprint, depth in [('lamp_bezels', outer.cut(inner), BEZEL_DEPTH),
                                        ('lamp_lenses', inner, LENS_DEPTH)]:
            tool = corner_tool(footprint, sign)
            shifted, floor = floor_for(skin, tool, sign, depth)
            removed = body.common(tool).cut(shifted)
            assert removed.Volume > .1, (side, name, 'empty headlight cut')
            body = body.cut(removed).removeSplitter()
            assert body.isValid() and len(body.Solids) == 1, (side, name)
            floors[name].append(floor)
    return body, floors


def check_headlights(body, scale=1.0):
    """Require a real lens across the top, front and side surfaces."""
    bonnet, _ = make_body()
    skin = reference_skin(bonnet)
    _, inner = lamp_outline()
    checks = []
    for sign, side in [(-1, 'left'), (1, 'right')]:
        _, floor = floor_for(skin, corner_tool(inner, sign), sign, LENS_DEPTH)
        areas = {'top': 0., 'front': 0., 'side': 0., 'rounded_corner': 0.}
        probes = []
        for face in floor.Faces:
            bounds = face.BoundBox
            if bounds.ZMax < 12:
                continue
            if abs(bounds.XMax-bounds.XMin) < 1e-6:
                region = 'front'
            elif abs(bounds.YMax-bounds.YMin) < 1e-6:
                region = 'side'
            elif isinstance(face.Surface, Part.BSplineSurface) and face.Surface.NbUPoles == 11:
                region = 'top'
            else:
                region = 'rounded_corner'
            vertices, triangles = face.tessellate(.04)
            triangle = max(triangles, key=lambda t:
                (vertices[t[1]]-vertices[t[0]]).cross(vertices[t[2]]-vertices[t[0]]).Length)
            centroid = sum((vertices[i] for i in triangle), V())/3
            p = face.valueAt(*face.Surface.parameter(centroid))
            normal = face.normalAt(*face.Surface.parameter(p))
            assert body.distToShape(Part.Vertex(p*scale))[0] < .005, (side, region, 'lens absent')
            assert not body.isInside((p+normal*.08)*scale, 1e-6, False), (side, region, 'lens not exposed')
            assert body.isInside((p-normal*.4)*scale, 1e-6, False), (side, region, 'lens detached')
            areas[region] += face.Area*scale**2
            probes.append({'surface': region, 'position_mm': [c*scale for c in (p.x, p.y, p.z)]})
        assert all(areas[k] > .1*scale**2 for k in ('top', 'front', 'side')), (side, areas)
        assert min(abs(p['position_mm'][1]) for p in probes) > 20*scale, (side, probes)
        checks.append({'side': side, 'surface_areas_mm2': areas, 'probes': probes})
    return {'count': 2, 'style': 'outer-corner wraparound ribbon lenses',
            'bezel_width_in_projection_mm': BEZEL_WIDTH*scale,
            'bezel_recess_per_axis_mm': BEZEL_DEPTH*scale,
            'lens_recess_per_axis_mm': LENS_DEPTH*scale,
            'integral_with_body': True, 'checks': checks}
