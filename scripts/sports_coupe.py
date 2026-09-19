"""Fixed two-door coupe body details; dimensions are in model millimetres."""

import FreeCAD as A
import Part
import math

V = A.Vector
ROOF_HEIGHT = 54
MODEL_SCALE = .6
SEAT_BASE_Z = 14
SEAT_RECLINE_DEG = 12


def polygon(points):
    return Part.makePolygon([V(*p) for p in points + [points[0]]])


def side_prism(points, sign, inner_y=20):
    return Part.Face(polygon([(x, sign * inner_y, z) for x, z in points])).extrude(
        V(0, sign * (60-inner_y), 0))


def make_cabin():
    # Longitudinal sections have circular roof crowns: there is no flat top cap.
    # The shoulder begins at the bed plane and rises inward at 45 degrees.
    # This retains a wide roof without an unsupported upright side window.
    stations = [
        # x, lower half-width, roof-edge half-width, crown height
        (-64, 36, 27, 28), (-55, 47.5, 32, 34), (-46, 47.5, 33, 43),
        (-38, 47.5, 34, 51.5), (-30, 47.5, 34, 53.5),
        (-18, 47.5, 34, 53.95), (-7, 47.5, 34, 54), (5, 47.5, 34, 53.5),
        (15, 47.5, 33, 51.5), (27, 47.5, 32, 45), (38, 46, 31, 37),
        (48, 38, 28, 29),
    ]
    wires = []
    for x, lower, upper, top in stations:
        rise = min(3.0, (top - 26) / 3)
        left = V(x, -upper, top - rise)
        right = V(x, upper, top - rise)
        shoulder_z = top-rise-(lower-upper)
        base_z = min(20, shoulder_z-1)
        wires.append(Part.Wire([
            Part.makeLine(V(x, -lower, base_z), V(x, -lower, shoulder_z)),
            Part.makeLine(V(x, -lower, shoulder_z), left),
            Part.Arc(left, V(x, 0, top), right).toShape(),
            Part.makeLine(right, V(x, lower, shoulder_z)),
            Part.makeLine(V(x, lower, shoulder_z), V(x, lower, base_z)),
            Part.makeLine(V(x, lower, base_z), V(x, -lower, base_z)),
        ]))
    cabin = Part.makeLoft(wires, True, False, False, 3).removeSplitter()
    assert cabin.isValid() and len(cabin.Solids) == 1
    return cabin


def make_wing():
    # A swept, tapered blade with true Bezier surfaces, a rounded leading edge,
    # a rising trailing lip and printable endplates. All points stay within y=47.
    sections = []
    for y, front, chord, height in [(-47, -78, 18, 44.6), (-37, -74, 21, 43.4),
                                   (0, -73, 23, 43), (37, -74, 21, 43.4),
                                   (47, -78, 18, 44.6)]:
        top = Part.BezierCurve()
        top.setPoles([V(front, y, height), V(front-2, y, height+4),
                      V(front-chord*.65, y, height+1.4), V(front-chord, y, height+3.1)])
        bottom = Part.BezierCurve()
        bottom.setPoles([V(front-chord, y, height+1.5), V(front-chord*.6, y, height-1.3),
                         V(front-2, y, height-1.7), V(front, y, height)])
        sections.append(Part.Wire([top.toShape(),
            Part.makeLine(V(front-chord, y, height+3.1), V(front-chord, y, height+1.5)),
            bottom.toShape()]))
    blade = Part.makeLoft(sections, True, False, False, 3)
    for sign, inner in [(-1, sections[1]), (1, sections[3])]:
        # The outer face is planar and therefore provides a reliable bed contact.
        # Grow the inner side into the blade over 8 mm of span, rather than
        # starting an unsupported flat endplate on the upper printed side.
        points = [(-76, sign*45, 45), (-81, sign*45, 48),
                  (-93, sign*45, 49), (-97, sign*45, 48),
                  (-97, sign*45, 42), (-79, sign*45, 41.5)]
        outline = polygon(points)
        transition = Part.makeLoft([inner, outline], True, False, False, 3)
        blade = blade.fuse(transition).fuse(Part.Face(outline).extrude(V(0, sign*2, 0)))
    blade = blade.common(Part.makeBox(50, 94, 30, V(-110, -47, 25))).removeSplitter()
    assert blade.isValid() and len(blade.Solids) == 1
    return blade


def detail_body(body):
    skin = body.copy()
    glass_floors = []
    detail_floors = []
    details = []
    glass_cuts = {}

    def recess(name, footprint, inward, glass=False):
        nonlocal body
        print('Cutting ' + name, flush=True)
        shifted = skin.copy()
        shifted.translate(V(*inward))
        floor = shifted.common(footprint)
        removed = skin.common(footprint).cut(shifted)
        assert removed.Volume > .1, (name, removed.Volume)
        body = body.cut(removed).removeSplitter()
        assert body.isValid() and len(body.Solids) == 1, name
        (glass_floors if glass else detail_floors).append(floor)
        if glass:
            glass_cuts[name] = removed
        details.append({'name': name, 'removed_volume_mm3': removed.Volume})

    # Projection cutters follow the actual curved skin instead of flat decals.
    for sign, side in [(-1, 'left'), (1, 'right')]:
        window = [(-33, 38), (-32.5, 47.5), (-28, 49.5), (10, 49.5),
                  (24, 44), (33, 38)]
        recess(side + '_door_window', side_prism(window, sign,32.5),
               (0, -sign * .8, 0), glass=True)
        quarter = [(-46, 38), (-43, 42), (-38, 48), (-35.5, 48), (-35.5, 38)]
        recess(side + '_quarter_window', side_prism(quarter, sign,32.5),
               (0, -sign * .8, 0), glass=True)

    for name, x, direction in [('windscreen', 12, -1), ('rear_window', -63, 1)]:
        points = [(-31, 36.5), (-30, 49.5), (30, 49.5), (31, 36.5)]
        tool = Part.Face(polygon([(x, y, z) for y, z in points])).extrude(V(34, 0, 0))
        recess(name, tool, (direction * .8, 0, 0), glass=True)

    door = [(-34, 35), (-34, 19), (-29, 11.5), (25, 11.5),
            (34, 18), (34, 32), (30, 35)]
    groove_width = .9
    for sign, side in [(-1, 'left'), (1, 'right')]:
        strokes = []
        for a, b in zip(door, door[1:] + door[:1]):
            dx, dz = b[0] - a[0], b[1] - a[1]
            length = (dx * dx + dz * dz) ** .5
            nx, nz = -dz / length * groove_width / 2, dx / length * groove_width / 2
            strokes.append(side_prism([
                (a[0] + nx, a[1] + nz), (b[0] + nx, b[1] + nz),
                (b[0] - nx, b[1] - nz), (a[0] - nx, a[1] - nz)
            ], sign))
            strokes.append(Part.makeCylinder(groove_width / 2, 40,
                                             V(a[0], sign * 20, a[1]), V(0, sign, 0)))
        tool = strokes[0].multiFuse(strokes[1:]).removeSplitter()
        recess(side + '_door_seam', tool, (0, -sign * .8, 0))

        # A recessed grip leaves a raised central handle, integral with the door.
        outer = side_prism([(-28, 28), (-26.8, 27), (-17, 27),
                            (-15.8, 28), (-15.8, 30), (-28, 30)], sign)
        grip = side_prism([(-26.5, 28.1), (-17.3, 28.1),
                          (-17.3, 29.2), (-26.5, 29.2)], sign)
        recess(side + '_door_handle', outer.cut(grip), (0, -sign * 1.2, 0))

    pillars = []
    for side in ('left', 'right'):
        for pillar, first, second in [
                ('A', 'windscreen', side + '_door_window'),
                ('B', side + '_door_window', side + '_quarter_window'),
                ('C', 'rear_window', side + '_quarter_window')]:
            gap = glass_cuts[first].distToShape(glass_cuts[second])[0]
            assert gap > 1, (side, pillar, 'window_recess_gap', gap)
            pillars.append({'side': side, 'pillar': pillar,
                            'minimum_window_recess_separation_mm': gap})
    return body, glass_floors, detail_floors, details, pillars


def face_groups(body, glass_floors, detail_floors):
    print('Classifying recessed faces', flush=True)
    groups = {'glass': [], 'details': []}
    for index, face in enumerate(body.Faces):
        u, v = face.Surface.parameter(face.CenterOfMass)
        sample = Part.Vertex(face.valueAt(u, v))
        for name, floors in [('glass', glass_floors), ('details', detail_floors)]:
            if any(floor.distToShape(sample)[0] < .005 for floor in floors):
                groups[name].append(index)
                break
    assert len(groups['glass']) >= 4, groups
    assert groups['details'], groups
    return groups


def occupant_envelopes(scale=1.0):
    """Concept packaging references only; these are not exported interior parts."""
    envelopes = []
    for side, centre_y in [('left', -15), ('right', 15)]:
        boxes = [
            # x, z, length, width, height: cushion, torso, head, thighs, lower legs
            (-22, SEAT_BASE_Z, 24, 27, 5), (-25, SEAT_BASE_Z + 5, 16, 26, 22),
            (-25, SEAT_BASE_Z + 27, 12, 12, 11),
            (0, SEAT_BASE_Z, 22, 22, 8), (18, 8, 18, 18, 10),
        ]
        shapes = [Part.makeBox(length * scale, width * scale, height * scale,
                               V(x * scale, (centre_y - width / 2) * scale, z * scale))
                  for x, z, length, width, height in boxes]
        # Keep the reference occupant dimensions; lower the seat and recline the upper body.
        for upper_body in shapes[1:3]:
            upper_body.rotate(V(-15 * scale, centre_y * scale, (SEAT_BASE_Z + 5) * scale),
                              V(0, 1, 0), -SEAT_RECLINE_DEG)
        envelopes.append((side, shapes[0].multiFuse(shapes[1:]).removeSplitter()))
    return envelopes


def check_packaging(body, scale=1.0):
    checks = []
    envelopes = occupant_envelopes(scale)
    for side, envelope in envelopes:
        outside = envelope.cut(body).Volume
        assert outside < .01, (side, 'occupant_envelope_outside_body_mm3', outside)
        checks.append({'side': side, 'outside_exterior_volume_mm3': outside})
    return {'purpose': 'concept exterior proportions, not an ergonomic certification',
            'seat_centres_y_mm': [-15 * scale, 15 * scale],
            'seat_cushion_width_mm': 27 * scale, 'centre_gap_mm': 3 * scale,
            'seat_cushion_base_z_mm': SEAT_BASE_Z * scale,
            'upper_body_recline_deg': SEAT_RECLINE_DEG,
            'head_envelope_top_z_mm': max(s.BoundBox.ZMax for _, s in envelopes),
            'checks': checks}


def check_cabin_surface(body, scale=1.0):
    heights = []
    for y in (0, 10, 20, 30, 35):
        ray = Part.makeLine(V(-7*scale, y*scale, 25*scale),
                            V(-7*scale, y*scale, 60*scale))
        heights.append(max(v.Point.z for v in body.common(ray).Vertexes))
    assert all(a > b for a, b in zip(heights, heights[1:])), heights
    assert heights[0] - heights[-1] > 2*scale, heights
    widths = []
    for z in (40, 48):
        ray = Part.makeLine(V(-7*scale, -60*scale, z*scale),
                            V(-7*scale, 60*scale, z*scale))
        ys = [v.Point.y for v in body.common(ray).Vertexes]
        widths.append(max(ys)-min(ys))
    lean = math.degrees(math.atan((widths[0]-widths[1])/(16*scale)))
    assert widths[1] > 70*scale and 43 < lean < 47, (widths, lean)
    sill_ray = Part.makeLine(V(-7*scale, -60*scale, 38.001*scale),
                             V(-7*scale, 0, 38.001*scale))
    sill_y = min(v.Point.y for v in body.common(sill_ray).Vertexes)
    sill_bed_height = sill_y + 47*scale
    assert 0 < sill_bed_height < .6, sill_bed_height
    return {'section_x_mm': -7*scale, 'roof_height_samples_mm': heights,
            'roof_lateral_sample_y_mm': [y*scale for y in (0, 10, 20, 30, 35)],
            'upper_glazing_width_mm': widths[1], 'side_glass_lean_from_vertical_deg': lean,
            'side_window_sill_above_print_bed_mm': sill_bed_height}
