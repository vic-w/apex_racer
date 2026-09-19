"""Fair body skin with a small control net and rounded bumper corners."""

import FreeCAD as A
import Part

V = A.Vector
CORNER_SETBACK = 12.0


def rounded_planform():
    """Curved corners that grow outward at no more than 45 degrees in print."""
    xmin, xmax, ymin, ymax = -99, 100.5, -47, 47
    r = CORNER_SETBACK
    points = [(xmin+r, ymin), (xmax-r, ymin), (xmax, ymin+2*r),
              (xmax, ymax-2*r), (xmax-r, ymax), (xmin+r, ymax),
              (xmin, ymax-2*r), (xmin, ymin+2*r)]
    controls = [(xmax, ymin+r), (xmax, ymax-r),
                (xmin, ymax-r), (xmin, ymin+r)]
    edges = []
    for i, control in enumerate(controls):
        a, b, c = [V(*points[j % 8], 0) for j in (2*i, 2*i+1, 2*i+2)]
        corner = Part.BezierCurve()
        corner.setPoles([b, V(*control, 0), c])
        edges.extend([Part.makeLine(a, b), corner.toShape()])
    return Part.Face(Part.Wire(edges)).extrude(V(0, 0, 80))


def clamped_knots(count, degree=3):
    knots = list(range(count-degree+1))
    return knots, [degree+1] + [1]*(len(knots)-2) + [degree+1]


def make_body():
    # Control poles, not interpolated stations: positive B-spline weights keep
    # the skin inside their envelope without the previous spline overshoot.
    # The bonnet sits just below the fenders instead of forming a deep trough.
    # Low end poles taper the bumper faces without compressing the wheel covers.
    rows = [
        # x, outer shoulder height, centre deck height
        (-99, 18, 19), (-99, 23, 24), (-87, 39, 36.5),
        (-65, 42, 38), (-38, 38, 35), (0, 35, 33),
        (38, 38, 36), (63, 42.5, 38.5), (86, 39.5, 36.5),
        (100.5, 21, 21.5), (100.5, 17, 17.5),
    ]
    fractions = [-1, -.85, -.65, -.4, 0, .4, .65, .85, 1]
    poles = []
    for x, shoulder, deck in rows:
        heights = [shoulder, shoulder, shoulder, deck, deck,
                   deck, shoulder, shoulder, shoulder]
        poles.append([V(x, 48*y, z) for y, z in zip(fractions, heights)])
    uk, um = clamped_knots(len(rows))
    vk, vm = clamped_knots(len(fractions))
    surface = Part.BSplineSurface()
    surface.buildFromPolesMultsKnots(poles, um, vm, uk, vk, False, False, 3, 3)
    raw = surface.toShape().extrude(V(0, 0, -60))
    body = raw.common(Part.makeBox(220, 110, 75, V(-110, -55, 5)))
    assert body.isValid() and len(body.Solids) == 1
    return body, surface


def end_underside_cutters():
    """Ease the underside upward only beyond the wheel/contact regions.

    Quadratic curves start tangent to the flat floor. Extrusion across the
    width keeps the rise parallel to the bed in the side-down print orientation.
    """
    cutters = []
    for start, tip, height in [(89, 100.5, 8), (-88, -99, 9)]:
        curve = Part.BezierCurve()
        a, b = V(start, -55, 5), V(tip, -55, height)
        curve.setPoles([a, V((start+tip)/2, -55, 5), b])
        low_b, low_a = V(tip, -55, 0), V(start, -55, 0)
        wire = Part.Wire([curve.toShape(), Part.makeLine(b, low_b),
                          Part.makeLine(low_b, low_a), Part.makeLine(low_a, a)])
        cutters.append(Part.Face(wire).extrude(V(0, 110, 0)))
    return Part.makeCompound(cutters)


def check_end_profiles(body, scale=1.0):
    """Measure real centreline body sections, below the separate rear wing."""
    result = {}
    for end, xs in [('front', [85, 90, 95, 100.49]),
                    ('rear', [-85, -90, -95, -98.99])]:
        samples = []
        for x in xs:
            ray = Part.makeLine(V(x*scale, 0, 0), V(x*scale, 0, 40*scale))
            edges = body.common(ray).Edges
            assert edges, (end, x, 'body section missing')
            # The front intake interrupts the section; measure the outer profile.
            low = min(edge.BoundBox.ZMin for edge in edges)
            high = max(edge.BoundBox.ZMax for edge in edges)
            samples.append({'x_mm': x*scale, 'top_z_mm': high,
                            'underside_z_mm': low, 'thickness_mm': high-low})
        thicknesses = [sample['thickness_mm'] for sample in samples]
        assert all(a > b for a, b in zip(thicknesses, thicknesses[1:])), (end, samples)
        assert 8*scale < thicknesses[-1] < 11*scale, (end, samples[-1])
        result[end] = {'centreline_sections': samples,
                       'terminal_thickness_mm': thicknesses[-1]}
    return result


def check_fairness(surface, scale=1.0, geometry_scale=1.0):
    """Reject ripples and deep bonnet valleys in the actual main CAD surface."""
    continuity = min(surface.UDegree-max(surface.getUMultiplicities()[1:-1]),
                     surface.VDegree-max(surface.getVMultiplicities()[1:-1]))
    assert continuity >= 2
    curves = []
    for v in (.1, 1, 2, 3, 4, 5, 5.9):
        points = [surface.value(i/100, v) for i in range(801)]
        for region, xmin, xmax in [('rear', -94, -35), ('bonnet', 35, 94)]:
            zs = [p.z for p in points if xmin*geometry_scale <= p.x <= xmax*geometry_scale]
            signs = [1 if b > a else -1 for a, b in zip(zs, zs[1:])
                     if abs(b-a) > 1e-4*geometry_scale]
            peaks = sum(a == 1 and b == -1 for a, b in zip(signs, signs[1:]))
            valleys = sum(a == -1 and b == 1 for a, b in zip(signs, signs[1:]))
            assert peaks <= 1 and valleys == 0, (region, v, peaks, valleys)
            curves.append({'region': region, 'surface_v': v, 'peaks': peaks, 'valleys': valleys})
    deltas = []
    for i in range(801):
        centre = surface.value(i/100, 3)
        if 35*geometry_scale <= centre.x <= 94*geometry_scale:
            deltas.append(max(surface.value(i/100, j/10).z for j in range(61))-centre.z)
    delta = max(deltas)*scale/geometry_scale
    assert delta < 4*scale, delta
    return {'interior_continuity_order': continuity,
            'max_bonnet_to_fender_height_difference_mm': delta,
            'longitudinal_sections': curves}


def check_corners(body, scale=1.0):
    checks = []
    for end, outside_x, inside_x in [('front', 97, 92), ('rear', -96, -91)]:
        for sign, side in [(-1, 'left'), (1, 'right')]:
            assert not body.isInside(V(outside_x*scale, sign*45*scale, 6*scale), 1e-6, True)
            assert body.isInside(V(inside_x*scale, sign*40*scale, 6*scale), 1e-6, True)
            checks.append({'end': end, 'side': side, 'square_corner_removed': True})
    return {'longitudinal_setback_mm': CORNER_SETBACK*scale,
            'lateral_curve_span_mm': 2*CORNER_SETBACK*scale,
            'checks': checks}
