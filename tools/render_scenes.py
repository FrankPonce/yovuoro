"""Isometric 3D illustrations for the story site, modelled in code and rendered in Blender Cycles.

Run headless (Blender 4.x):
  blender -b --python tools/render_scenes.py -- <site_on|site_off|stadium|ferry|town|robot|all> [preview|final]
Writes web/img/<name>.png (RGBA, transparent). Everything is built from primitives in this file:
no downloaded models. Same look as the CargoMar vehicle renders (satin paint, bevelled edges,
soft daylight), with a true isometric (orthographic, 30 deg) camera so the pieces compose.
"""
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "site", "img", "src")
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
WHICH = argv[0] if argv else "site_on"
NIGHT = False   # set per render: names ending in _night
FINAL = len(argv) > 1 and argv[1] == "final"

PAL = {"paper": "#FBF8F4", "ink": "#1D1B10", "or": "#F59B00", "navy": "#0F4B73",
       "blue": "#38BDF8", "pink": "#E6508C", "green": "#AAC800", "white": "#F4F2EE", "brand": "#4F46E5",
       "mast": "#D5D8DD", "concrete": "#D8D2C8", "grass": "#9CC46A", "dark": "#2B3038",
       "yellow": "#F2C14E", "falu": "#B9483A", "roof": "#3B4048", "pitch": "#5FAE4C",
       "water": "#9FD3E6", "glass": "#26364A"}


# ---------------------------------------------------------------- materials
def lin(hexstr):
    h = hexstr.lstrip("#")
    c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c) + (1.0,)


_MATS = {}


def mat(color, rough=0.5, emit=0.0, metal=0.0, name=None):
    key = (color, rough, emit, metal)
    if key in _MATS:
        return _MATS[key]
    m = bpy.data.materials.new(name or "m%d" % len(_MATS))
    m.use_nodes = True
    b = m.node_tree.nodes.get("Principled BSDF")
    col = lin(PAL.get(color, color))
    b.inputs["Base Color"].default_value = col
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = 0.35
    if emit:
        b.inputs["Emission Color"].default_value = col
        b.inputs["Emission Strength"].default_value = emit
    _MATS[key] = m
    return m


# ---------------------------------------------------------------- geometry helpers
def link(ob):
    bpy.context.scene.collection.objects.link(ob)
    return ob


def mesh(name, verts, faces, m=None, smooth=False):
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    me.validate()
    ob = link(bpy.data.objects.new(name, me))
    if m:
        me.materials.append(m)
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    return ob


def bevel(ob, w=0.04, seg=3):
    b = ob.modifiers.new("bevel", "BEVEL")
    b.width, b.segments, b.limit_method = w, seg, "ANGLE"
    for p in ob.data.polygons:
        p.use_smooth = True
    try:
        ob.data.set_sharp_from_angle(angle=math.radians(40))
    except Exception:
        pass
    return ob


def box(name, x0, x1, y0, y1, z0, z1, m, bv=0.04, rot_z=0.0, loc=(0, 0, 0)):
    v = [(x, y, z) for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)]
    f = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    ob = mesh(name, v, f, m)
    if bv:
        bevel(ob, bv)
    ob.rotation_euler[2] = rot_z
    ob.location = loc
    return ob


def cyl(name, r0, z0, z1, m, r1=None, seg=32, loc=(0, 0, 0), bv=0.0, sx=1.0, sy=1.0):
    r1 = r0 if r1 is None else r1
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        v += [(r0 * math.cos(a) * sx, r0 * math.sin(a) * sy, z0),
              (r1 * math.cos(a) * sx, r1 * math.sin(a) * sy, z1)]
    for i in range(seg):
        j = (i + 1) % seg
        f.append((2 * i, 2 * j, 2 * j + 1, 2 * i + 1))
    f.append(tuple(2 * i for i in reversed(range(seg))))
    f.append(tuple(2 * i + 1 for i in range(seg)))
    ob = mesh(name, v, f, m, smooth=True)
    if bv:
        bevel(ob, bv)
    ob.location = loc
    return ob


def sphere(name, r, m, loc, sz=1.0):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=r, location=loc, segments=32, ring_count=16)
    ob = bpy.context.active_object
    ob.name = name
    ob.scale[2] = sz
    ob.data.materials.append(m)
    bpy.ops.object.shade_smooth()
    return ob


def ring(name, r_in, r_out, z0, z1, m, seg=64, sx=1.0, sy=1.0, r_out_top=None):
    """Elliptic annulus (stadium stands); top outer radius can differ (sloped stands)."""
    rt = r_out if r_out_top is None else r_out_top
    v, f = [], []
    for i in range(seg):
        a = 2 * math.pi * i / seg
        c, s = math.cos(a), math.sin(a)
        v += [(r_in * c * sx, r_in * s * sy, z0), (r_out * c * sx, r_out * s * sy, z0),
              (rt * c * sx, rt * s * sy, z1), (r_in * c * sx, r_in * s * sy, z0 + 0.02)]
    for i in range(seg):
        j = (i + 1) % seg
        a, b = 4 * i, 4 * j
        f += [(a + 0, a + 1, b + 1, b + 0), (a + 1, a + 2, b + 2, b + 1),
              (a + 2, a + 3, b + 3, b + 2), (a + 3, a + 0, b + 0, b + 3)]
    return mesh(name, v, f, m, smooth=True)


# ---------------------------------------------------------------- scene rig
def reset(res=1600):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    _MATS.clear()
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    cp = bpy.context.preferences.addons["cycles"].preferences
    for dev in ("OPTIX", "CUDA"):
        try:
            cp.compute_device_type = dev
            cp.get_devices()
            if any(d.type == dev for d in cp.devices):
                break
        except Exception:
            continue
    for d in cp.devices:
        d.use = d.type != "CPU"
    sc.cycles.device = "GPU"
    sc.cycles.samples = 160 if FINAL else 32
    sc.cycles.use_denoising = True
    sc.render.film_transparent = True
    sc.render.resolution_x = sc.render.resolution_y = res
    sc.render.resolution_percentage = 100 if FINAL else 40
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    try:
        sc.view_settings.view_transform = "AgX"
        sc.view_settings.look = "AgX - Base Contrast"
        sc.view_settings.exposure = 0.45
    except Exception:
        pass
    w = bpy.data.worlds.new("sky")
    sc.world = w
    w.use_nodes = True
    n, l = w.node_tree.nodes, w.node_tree.links
    bg = n.get("Background")
    tc, sep = n.new("ShaderNodeTexCoord"), n.new("ShaderNodeSeparateXYZ")
    l.new(tc.outputs["Generated"], sep.inputs[0])
    mr = n.new("ShaderNodeMapRange")
    mr.inputs[1].default_value, mr.inputs[2].default_value = -1, 1
    l.new(sep.outputs["Z"], mr.inputs[0])
    ramp = n.new("ShaderNodeValToRGB")
    e = ramp.color_ramp.elements
    if NIGHT:
        e[0].position, e[0].color = 0.0, (0.02, 0.025, 0.05, 1)
        e[1].position, e[1].color = 1.0, (0.10, 0.16, 0.34, 1)
        e.new(0.5).color = (0.12, 0.15, 0.25, 1)
    else:
        e[0].position, e[0].color = 0.0, (0.45, 0.41, 0.36, 1)
        e[1].position, e[1].color = 1.0, (0.55, 0.70, 0.95, 1)
        e.new(0.5).color = (0.97, 0.96, 0.94, 1)
    l.new(mr.outputs[0], ramp.inputs[0])
    l.new(ramp.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 0.55 if NIGHT else 1.1
    return sc


def sun(direction, strength=3.6, angle=8.0):
    d = bpy.data.lights.new("sun", "SUN")
    if NIGHT:
        strength, color = strength * 0.22, (0.62, 0.74, 1.0)
    else:
        color = (1.0, 0.95, 0.88)
    d.energy, d.angle, d.color = strength, math.radians(angle), color
    ob = link(bpy.data.objects.new("sun", d))
    ob.rotation_euler = Vector(direction).normalized().to_track_quat("Z", "Y").to_euler()


def shadow_catcher(size=60, z=0.0):
    ob = box("ground", -size, size, -size, size, z - 0.02, z, None, bv=0)
    ob.is_shadow_catcher = True
    ob["nobounds"] = True


def iso_camera(margin=0.06, az=45.0, el=30.0):
    """Orthographic isometric camera framed to every mesh."""
    sc = bpy.context.scene
    cd = bpy.data.cameras.new("cam")
    cd.type = "ORTHO"
    cam = link(bpy.data.objects.new("cam", cd))
    sc.camera = cam
    dg = bpy.context.evaluated_depsgraph_get()
    pts = []
    for ob in sc.objects:
        if ob.type == "MESH" and not ob.get("nobounds"):
            ev = ob.evaluated_get(dg)
            pts += [ev.matrix_world @ Vector(c) for c in ev.bound_box]
    ctr = sum(pts, Vector()) / len(pts)
    d = Vector((math.cos(math.radians(el)) * math.cos(math.radians(az)),
                math.cos(math.radians(el)) * math.sin(math.radians(az)), math.sin(math.radians(el))))
    cam.location = ctr + d * 80
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    bpy.context.view_layer.update()
    inv = cam.matrix_world.inverted()
    qs = [inv @ p for p in pts]
    xs, ys = [q.x for q in qs], [q.y for q in qs]
    span = max(max(xs) - min(xs), max(ys) - min(ys)) / (1 - 2 * margin)
    cd.ortho_scale = span
    cd.shift_x = ((max(xs) + min(xs)) / 2) / span
    cd.shift_y = ((max(ys) + min(ys)) / 2) / span
    cd.clip_end = 400


def render(name):
    os.makedirs(OUT, exist_ok=True)
    sc = bpy.context.scene
    path = os.path.join(OUT, name + (".png" if FINAL else "-preview.png"))
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True)
    print("RENDERED", path)


def tile(size=4.0, h=0.35, grass=True):
    """Rounded base tile every object stands on (a small diorama island)."""
    box("tile", -size, size, -size, size, -h, 0.0, mat("concrete", 0.7), bv=0.12)
    if grass:
        box("grass", -size + 0.22, size - 0.22, -size + 0.22, size - 0.22, -0.02, 0.08,
            mat("grass", 0.8), bv=0.05)
    shadow_catcher(z=-h)


def finnish_flag(name, x, y, z_top, angle=0.0, size=0.9, pole=True, z_pole0=0.08):
    """Finnish flag (18:11, Nordic cross in #002F6C) on an optional pole, facing +x rotated by angle."""
    import math as _m
    w, h = size, size * 11 / 18
    blue, white = mat("#002F6C", 0.5), mat("#FFFFFF", 0.5)
    parts = []
    if pole:
        cyl(name + "_pole", 0.035, z_pole0, z_top + 0.1, mat("mast", 0.4, metal=0.3), seg=12, loc=(x, y, 0))
        sphere(name + "_knob", 0.06, mat("mast", 0.4, metal=0.3), (x, y, z_top + 0.12))
    # cloth in the local frame: hoist at the pole, flying along local +u
    z0 = z_top - h
    t = 0.012
    def piece(nm, u0, u1, v0, v1, m, d=0.0):
        ob = box(name + nm, u0, u1, -t - d, t + d, z0 + v0, z0 + v1, m, bv=0)
        ob.location = (x, y, 0)
        ob.rotation_euler[2] = angle
        parts.append(ob)
    piece("_cloth", 0.04, 0.04 + w, 0.0, h, white)
    cross_v = 5 / 18 * w        # vertical bar starts 5/18 from the hoist, 3/18 wide
    piece("_vbar", 0.04 + cross_v, 0.04 + cross_v + 3 / 18 * w, 0.0, h, blue, d=0.002)
    piece("_hbar", 0.04, 0.04 + w, 4 / 11 * h, 7 / 11 * h, blue, d=0.002)
    return parts


# ---------------------------------------------------------------- radio site
def build_site(on=True, brain=None):
    tile(2.6)
    box("pad", -0.9, 0.9, -0.9, 0.9, 0.08, 0.22, mat("concrete", 0.6), bv=0.05)
    # equipment cabinet with an orange stripe
    box("cab", 0.9, 1.9, -1.6, -0.9, 0.08, 1.05, mat("white", 0.45), bv=0.06)
    box("cab_stripe", 0.88, 1.92, -1.62, -0.88, 0.82, 0.9, mat("brand", 0.5), bv=0.01)
    box("cab_door", 1.9, 1.93, -1.5, -1.0, 0.2, 0.75, mat("mast", 0.5), bv=0.01)
    if brain == "dial":
        # the published method's brain: a threshold dial on the cabinet (sleep below, wake above)
        cyl("dial_base", 0.36, 1.05, 1.13, mat("white", 0.4), seg=48, loc=(1.4, -1.25, 0))
        cyl("dial_face", 0.31, 1.13, 1.16, mat("#E9ECF2", 0.35), seg=48, loc=(1.4, -1.25, 0))
        for k in range(7):                                    # tick marks
            ang = math.radians(-120 + 40 * k)
            tx, ty = 1.4 + 0.24 * math.cos(ang), -1.25 + 0.24 * math.sin(ang)
            t = box("tick%d" % k, -0.012, 0.012, -0.045, 0.045, 1.16, 1.18, mat("ink", 0.5), bv=0)
            t.location = (tx, ty, 0); t.rotation_euler[2] = ang
        ptr = box("pointer", -0.02, 0.02, 0.0, 0.22, 1.16, 1.2, mat("#DC2626", 0.4), bv=0.005)
        ptr.location = (1.4, -1.25, 0); ptr.rotation_euler[2] = math.radians(-35)
        cyl("dial_knob", 0.06, 1.16, 1.24, mat("ink", 0.4), seg=24, loc=(1.4, -1.25, 0))
    if brain == "forecast":
        # Yovahti's brain: a small screen showing a forecast band and a limit line
        box("scr_leg", 1.37, 1.43, -1.28, -1.22, 1.05, 1.3, mat("mast", 0.4), bv=0.005)
        scr = box("screen", -0.04, 0.04, -0.42, 0.42, 1.28, 1.78, mat("ink", 0.3), bv=0.03)
        scr.location = (1.4, -1.25, 0)
        for k, hgt in enumerate((0.10, 0.16, 0.13, 0.08, 0.06, 0.09, 0.2, 0.3)):
            bar = box("fc%d" % k, 0.04, 0.05, -0.36 + k * 0.095, -0.30 + k * 0.095, 1.34, 1.34 + hgt,
                      mat("#A5B4FC", 0.3, emit=4.0), bv=0)
            bar.location = (1.4, -1.25, 0)
        lim = box("limit", 0.045, 0.055, -0.38, 0.38, 1.62, 1.635, mat("#F87171", 0.3, emit=4.0), bv=0)
        lim.location = (1.4, -1.25, 0)
    # mast (tapered monopole)
    cyl("mast", 0.22, 0.22, 6.2, mat("mast", 0.4, metal=0.3), r1=0.13, seg=24)
    cyl("cap", 0.16, 6.2, 6.35, mat("white", 0.4), seg=24)
    for z in (4.0, 5.4):                                     # head-frame rings
        cyl("ring%.1f" % z, 0.75, z - 0.04, z + 0.04, mat("mast", 0.4, metal=0.4), seg=32)
    for k in range(3):                                       # three sectors, 120 deg apart
        a = math.radians(90 + 120 * k)
        cx, cy = 0.72 * math.cos(a), 0.72 * math.sin(a)
        # coverage panel (low band): tall, slim, always on
        p = box("cov%d" % k, -0.11, 0.11, -0.28, 0.28, 3.55, 4.75, mat("white", 0.45), bv=0.06)
        p.location = (cx, cy, 0); p.rotation_euler[2] = a
        # capacity panel (mid band + NR 3500 massive MIMO): square, with a status strip
        q = box("cap%d" % k, -0.14, 0.14, -0.36, 0.36, 5.0, 5.85,
                mat("navy", 0.5) if on else mat("#8E959E", 0.6), bv=0.07)
        q.location = (cx * 1.05, cy * 1.05, 0); q.rotation_euler[2] = a
        led = box("led%d" % k, 0.13, 0.18, -0.28, 0.28, 5.08, 5.24,
                  mat("blue", 0.3, emit=12.0) if on else mat("dark", 0.6), bv=0.01)
        led.location = (cx * 1.05, cy * 1.05, 0); led.rotation_euler[2] = a
    # a small tree for scale
    cyl("trunk", 0.07, 0.08, 0.6, mat("#7A5A3A", 0.8), seg=12, loc=(-1.7, 1.4, 0))
    sphere("crown", 0.42, mat("#6FA65A", 0.8), (-1.7, 1.4, 0.95), sz=1.15)


# ---------------------------------------------------------------- stadium
def build_stadium():
    tile(5.6)
    sx, sy = 1.0, 0.72
    cyl("pitchbase", 3.0, 0.08, 0.14, mat("pitch", 0.85), seg=96, sx=sx * 1.12, sy=sy * 1.12)
    box("pitch", -2.3, 2.3, -1.45, 1.45, 0.14, 0.16, mat("pitch", 0.8), bv=0)
    for x in (-2.3, 0.0, 2.3):                               # white lines
        box("line%.1f" % x, x - 0.03, x + 0.03, -1.45, 1.45, 0.16, 0.17, mat("white", 0.6), bv=0)
    for y in (-1.45, 1.45):
        box("side%.1f" % y, -2.3, 2.3, y - 0.03, y + 0.03, 0.16, 0.17, mat("white", 0.6), bv=0)
    cyl("circle", 0.45, 0.16, 0.172, mat("white", 0.6), seg=48)
    cyl("circle_in", 0.40, 0.16, 0.175, mat("pitch", 0.8), seg=48)
    # stands: three tiers of seats, alternating club colours
    tiers = [(3.25, 3.75, 0.1, 0.55, "navy"), (3.75, 4.25, 0.55, 1.05, "or"),
             (4.25, 4.75, 1.05, 1.55, "navy")]
    for i, (ri, ro, z0, z1, c) in enumerate(tiers):
        ring("tier%d" % i, ri, ro, z0, z1, mat(c, 0.55), sx=sx, sy=sy)
    ring("rim", 4.75, 5.0, 0.1, 1.75, mat("white", 0.45), sx=sx, sy=sy)
    # Finnish flags at the front of the stadium
    finnish_flag("flagA", 4.9, -4.9, 2.6, angle=math.radians(90))
    finnish_flag("flagB", 4.9, 4.9, 2.6, angle=math.radians(90))
    # floodlights at the four corners
    for k in range(4):
        a = math.radians(45 + 90 * k)
        x, y = 5.15 * math.cos(a) * sx, 5.15 * math.sin(a) * sy
        cyl("pole%d" % k, 0.07, 0.08, 3.6, mat("mast", 0.4, metal=0.3), seg=12, loc=(x, y, 0))
        lamp = box("lamp%d" % k, -0.35, 0.35, -0.08, 0.08, 3.5, 3.95, mat("#FFF4D6", 0.3, emit=30.0 if NIGHT else 8.0),
                   bv=0.03)
        lamp.location = (x, y, 0); lamp.rotation_euler[2] = a + math.pi / 2


# ---------------------------------------------------------------- ferry
def build_ferry():
    L, B = 9.0, 1.6
    # water disc
    w = cyl("water", 6.4, -0.05, 0.0, mat("#7CC3DD", 0.12), seg=96, sx=1.0, sy=0.42)
    w["nobounds"] = False
    # hull: lofted box with a pointed bow
    prof = []
    for i in range(13):
        x = -L / 2 + L * i / 12
        t = max(0.0, (x - (L / 2 - 2.2)) / 2.2)
        half = B * (1 - t ** 1.6)
        prof.append((x, half))
    v, f = [], []
    for x, h in prof:
        v += [(x, -h, -0.25), (x, h, -0.25), (x, h * 1.04, 1.05), (x, -h * 1.04, 1.05)]
    for i in range(len(prof) - 1):
        a, b = 4 * i, 4 * (i + 1)
        f += [(a, b, b + 3, a + 3), (a + 1, a + 2, b + 2, b + 1), (a, a + 1, b + 1, b),
              (a + 3, b + 3, b + 2, a + 2)]
    f += [(0, 3, 2, 1)]
    hull = mesh("hull", v, f, mat("white", 0.4), smooth=False)
    bevel(hull, 0.05)
    box("boot", -L / 2 + 0.02, L / 2 - 2.2, -B - 0.03, B + 0.03, -0.25, 0.42, mat("navy", 0.5), bv=0.03)
    box("stripe", -L / 2 + 0.05, L / 2 - 2.6, -B - 0.045, B + 0.045, 0.56, 0.76, mat("or", 0.5), bv=0.01)
    # superstructure decks with window bands
    decks = [(-4.0, 2.4, 1.05, 1.75, 1.45), (-3.6, 1.9, 1.75, 2.45, 1.35), (-3.0, 1.2, 2.45, 3.1, 1.2)]
    for i, (x0, x1, z0, z1, hb) in enumerate(decks):
        box("deck%d" % i, x0, x1, -hb, hb, z0, z1, mat("white", 0.4), bv=0.08)
        box("win%d" % i, x0 + 0.15, x1 - 0.15, -hb - 0.02, hb + 0.02, z0 + 0.3, z0 + 0.48,
            mat("glass", 0.15), bv=0.01)
    box("bridge", 0.6, 1.6, -1.3, 1.3, 3.1, 3.55, mat("white", 0.4), bv=0.06)
    box("bridge_win", 1.58, 1.62, -1.1, 1.1, 3.25, 3.45, mat("glass", 0.15), bv=0.01)
    cyl("funnel", 0.42, 3.1, 4.25, mat("or", 0.45), r1=0.36, seg=24, loc=(-2.4, 0, 0), sx=1.4)
    cyl("funnel_top", 0.38, 4.25, 4.4, mat("dark", 0.5), seg=24, loc=(-2.4, 0, 0), sx=1.4)
    finnish_flag("ensign", -L / 2 + 0.25, 0.0, 2.15, angle=math.radians(180), size=0.8, z_pole0=1.05)
    cyl("radar_mast", 0.04, 3.55, 4.6, mat("mast", 0.4, metal=0.3), seg=12, loc=(1.1, 0, 0))
    finnish_flag("mastflag", 1.1, 0.0, 4.55, angle=math.radians(180), size=0.5, pole=False)
    for k, y in enumerate((-0.9, 0.9)):                      # lifeboats
        box("boat%d" % k, -1.5, 0.0, y - 0.18, y + 0.18, 2.5, 2.75, mat("or", 0.45), bv=0.08)
    sun_dummy = None  # noqa: F841
    shadow_catcher(80)


# ---------------------------------------------------------------- town block
import random as _rnd
_WIN = _rnd.Random(7)


def window_mat():
    if NIGHT and _WIN.random() < 0.78:
        return mat("#FFC56B", 0.4, emit=7.0)
    return mat("glass", 0.2)


def house(name, x, y, w, d, h, wall, rot=0.0):
    box(name, x - w / 2, x + w / 2, y - d / 2, y + d / 2, 0.08, h, mat(wall, 0.6), bv=0.04)
    rh = 0.55 * w
    v = [(x - w / 2 - 0.08, y - d / 2 - 0.08, h), (x + w / 2 + 0.08, y - d / 2 - 0.08, h),
         (x + w / 2 + 0.08, y + d / 2 + 0.08, h), (x - w / 2 - 0.08, y + d / 2 + 0.08, h),
         (x, y - d / 2 - 0.08, h + rh), (x, y + d / 2 + 0.08, h + rh)]
    f = [(0, 1, 4), (3, 5, 2), (0, 4, 5, 3), (1, 2, 5, 4), (0, 3, 2, 1)]
    bevel(mesh(name + "_roof", v, f, mat("roof", 0.6)), 0.03, 2)
    for k in range(int(w // 0.6)):                           # windows, front face
        wx = x - w / 2 + 0.35 + k * 0.6
        if wx + 0.18 < x + w / 2:
            box("%s_w%d" % (name, k), wx - 0.12, wx + 0.12, y - d / 2 - 0.02, y - d / 2 + 0.01,
                h * 0.45, h * 0.45 + 0.3, window_mat(), bv=0.0)
    for k in range(int(d // 0.6)):                           # windows, side facing the camera
        wy = y - d / 2 + 0.35 + k * 0.6
        if wy + 0.18 < y + d / 2:
            box("%s_s%d" % (name, k), x + w / 2 - 0.01, x + w / 2 + 0.02, wy - 0.12, wy + 0.12,
                h * 0.45, h * 0.45 + 0.3, window_mat(), bv=0.0)
    box(name + "_door", x + w / 2 - 0.01, x + w / 2 + 0.03, y - 0.15, y + 0.15, 0.08, 0.55,
        mat("navy", 0.5), bv=0.0)


def build_town():
    tile(5.4)
    for x0, x1, y0, y1 in ((-5.0, 5.0, -0.35, 0.35), (-0.35, 0.35, -5.0, 5.0)):      # streets
        box("street", x0, x1, y0, y1, 0.0, 0.1, mat("#9AA0A8", 0.8), bv=0)
    houses = [(-3.6, -3.4, 1.5, 1.3, 1.1, "yellow"), (-1.6, -3.3, 1.3, 1.2, 1.0, "falu"),
              (-3.5, -1.6, 1.3, 1.2, 1.3, "white"), (-1.6, -1.6, 1.4, 1.2, 1.0, "yellow"),
              (1.6, -3.4, 1.4, 1.3, 1.2, "white"), (3.6, -3.3, 1.4, 1.2, 1.0, "falu"),
              (-3.6, 1.6, 1.4, 1.3, 1.0, "falu"), (-1.6, 3.4, 1.3, 1.2, 1.2, "yellow"),
              (3.6, 3.5, 1.3, 1.2, 1.0, "yellow")]
    for k, (x, y, w, d, h, c) in enumerate(houses):
        house("h%d" % k, x, y, w, d, h, c)
    # a small block of flats (three storeys, flat roof)
    box("flats", 1.0, 3.4, 1.0, 2.6, 0.08, 2.6, mat("#E7E2D8", 0.6), bv=0.05)
    box("flats_roof", 0.95, 3.45, 0.95, 2.65, 2.6, 2.7, mat("roof", 0.6), bv=0.03)
    for fl in range(3):
        for k in range(4):
            wx = 1.3 + k * 0.6
            box("fw%d%d" % (fl, k), wx - 0.14, wx + 0.14, 0.98, 1.01, 0.45 + fl * 0.75, 0.8 + fl * 0.75,
                window_mat(), bv=0)
        for k in range(3):
            wy = 1.3 + k * 0.5
            box("fs%d%d" % (fl, k), 3.39, 3.42, wy - 0.12, wy + 0.12, 0.45 + fl * 0.75, 0.8 + fl * 0.75,
                window_mat(), bv=0)
    trees = [(-4.7, -4.7), (-0.9, -4.6), (4.7, -1.8), (4.6, 1.4), (-4.7, 4.6), (-0.9, 4.7),
             (0.9, 4.6), (-2.6, 0.9), (2.7, -1.3), (-4.6, -0.9)]
    for k, (x, y) in enumerate(trees):
        cyl("t%d" % k, 0.06, 0.08, 0.5, mat("#7A5A3A", 0.8), seg=10, loc=(x, y, 0))
        sphere("c%d" % k, 0.34, mat("#6FA65A", 0.8), (x, y, 0.8), sz=1.2)
    for k, (x, y) in enumerate([(0.55, -2.5), (-0.55, 2.5), (2.5, 0.55), (-2.5, -0.55)]):   # lamps
        cyl("lp%d" % k, 0.035, 0.08, 1.2, mat("dark", 0.5), seg=10, loc=(x, y, 0))
        sphere("lb%d" % k, 0.09, mat("#FFE2A8", 0.3, emit=10.0 if NIGHT else 0.0), (x, y, 1.25))


# ---------------------------------------------------------------- agent robot
def build_robot():
    body = sphere("body", 1.0, mat("white", 0.35), (0, 0, 1.25), sz=1.05)
    body.scale[0] = 1.05
    head = box("head", -0.85, 0.85, -0.7, 0.7, 2.25, 3.35, mat("white", 0.35), bv=0.32)
    box("face", 0.6, 0.88, -0.55, 0.55, 2.4, 3.2, mat("ink", 0.2), bv=0.12)
    for y in (-0.25, 0.25):
        box("eye%.2f" % y, 0.86, 0.9, y - 0.09, y + 0.09, 2.85, 3.0, mat("blue", 0.3, emit=5.0), bv=0.03)
    box("smile", 0.86, 0.9, -0.18, 0.18, 2.6, 2.66, mat("blue", 0.3, emit=5.0), bv=0.02)
    cyl("antenna", 0.04, 3.35, 3.85, mat("mast", 0.4), seg=12)
    sphere("tip", 0.12, mat("brand", 0.4, emit=1.2), (0, 0, 3.92))
    box("badge", 0.98, 1.06, -0.3, 0.3, 1.2, 1.6, mat("brand", 0.45), bv=0.05)
    for y in (-1.15, 1.15):
        sphere("arm%.1f" % y, 0.28, mat("brand", 0.5), (0.1, y, 1.35), sz=1.4)
    for y in (-0.45, 0.45):
        cyl("leg%.1f" % y, 0.22, 0.0, 0.35, mat("brand", 0.5), seg=20, loc=(0, y, 0))
    shadow_catcher()


# ---------------------------------------------------------------- Night Shift: baseband with a GPU
SLICE_RAN, SLICE_LENT = "#6366F1", "#22C55E"


def fan(name, y, z, x, r=0.2, m=None):
    """A GPU fan on the card front (axis along +x): hub, blades ring, guard."""
    parts = []
    for nm, rr, d, mm in (("_ring", r, 0.03, mat("dark", 0.5)), ("_hub", r * 0.35, 0.05, mat("#3A404A", 0.4))):
        ob = cyl(name + nm, rr, -d, d, mm, seg=40)
        ob.location = (x, y, z); ob.rotation_euler = (0, math.pi / 2, 0)
        parts.append(ob)
    for k in range(7):
        bl = box(name + "_bl%d" % k, -0.006, 0.006, -r * 0.9, -r * 0.36, -0.035, 0.035, mat("#20252C", 0.5), bv=0)
        bl.location = (x + 0.02, y, z); bl.rotation_euler = (math.radians(360 / 7 * k), 0, 0)
    return parts


def build_baseband(ran=6):
    """Close-up: the site's equipment cabinet, door open, a baseband unit and a GPU card.

    The GPU's front carries 8 slice lights: indigo = used by the radio, green = lent out."""
    tile(1.9)
    W, cab = mat("white", 0.45), mat("#E9EBEE", 0.5)
    box("cab_back", -0.85, -0.7, -1.05, 1.05, 0.08, 2.75, W, bv=0.04)
    box("cab_side_l", -0.85, 0.85, -1.05, -0.92, 0.08, 2.75, W, bv=0.04)
    box("cab_side_r", -0.85, 0.85, 0.92, 1.05, 0.08, 2.75, W, bv=0.04)
    box("cab_top", -0.9, 0.9, -1.1, 1.1, 2.75, 2.92, W, bv=0.05)
    box("cab_stripe", -0.92, 0.92, -1.12, 1.12, 2.56, 2.66, mat("brand", 0.5), bv=0.01)
    box("cab_floor", -0.85, 0.85, -1.05, 1.05, 0.08, 0.2, W, bv=0.03)
    box("cab_inside", -0.71, -0.69, -0.92, 0.92, 0.2, 2.75, mat("#2B3038", 0.7), bv=0)
    for y in (-0.86, 0.86):                                        # rack rails
        box("rail%.2f" % y, -0.6, 0.78, y - 0.03, y + 0.03, 0.2, 2.72, mat("mast", 0.4, metal=0.5), bv=0.005)
    # door swung open toward the viewer's left
    box("door", 0.85, 2.3, -1.12, -1.06, 0.2, 2.62, cab, bv=0.03)
    box("door_handle", 1.6, 1.9, -1.15, -1.12, 1.35, 1.45, mat("dark", 0.4), bv=0.01)
    # GPU card at the bottom (most visible): dark shroud, two fans, 8 slice lights below the fans
    box("gpu", -0.62, 0.8, -0.82, 0.82, 0.3, 1.2, mat("#1B1F26", 0.35, metal=0.2), bv=0.04)
    box("gpu_pcb", -0.62, 0.74, -0.84, 0.84, 1.2, 1.24, mat("#15803D", 0.5), bv=0.01)
    fan("fanA", -0.4, 0.86, 0.82)
    fan("fanB", 0.4, 0.86, 0.82)
    for k in range(8):
        col = SLICE_RAN if k < ran else SLICE_LENT
        box("slice%d" % k, 0.8, 0.85, -0.76 + k * 0.193, -0.6 + k * 0.193, 0.38, 0.56, mat(col, 0.3, emit=3.2), bv=0.006)
    # baseband unit (the radio's own computer)
    box("bbu", -0.62, 0.8, -0.82, 0.82, 1.4, 1.84, mat("navy", 0.45), bv=0.03)
    for k in range(4):
        box("port%d" % k, 0.8, 0.83, -0.65 + k * 0.18, -0.55 + k * 0.18, 1.54, 1.64, mat("#0B1220", 0.5), bv=0)
    box("bbu_led", 0.8, 0.83, 0.35, 0.7, 1.7, 1.74, mat("blue", 0.3, emit=6.0), bv=0)
    # power unit (top)
    box("psu", -0.62, 0.8, -0.82, 0.82, 2.0, 2.4, mat("#B8BEC6", 0.5), bv=0.03)
    for k in range(6):
        box("vent%d" % k, 0.8, 0.82, -0.6 + k * 0.22, -0.48 + k * 0.22, 2.1, 2.3, mat("dark", 0.6), bv=0)
    # cables up to the mast
    cyl("cable", 0.05, 2.9, 3.4, mat("dark", 0.6), seg=12, loc=(-0.4, 0.6, 0))


def build_site_lend():
    """The site at night: capacity radios asleep, the cabinet's GPU glowing green (lent)."""
    build_site(False)
    box("gpu_glow", 1.9, 1.95, -1.5, -1.0, 0.25, 0.7, mat("#22C55E", 0.3, emit=14.0), bv=0.01)
    box("gpu_glow2", 0.88, 1.92, -1.62, -0.88, 0.82, 0.9, mat("#22C55E", 0.4, emit=6.0), bv=0.01)


BUILDERS = {"site_on": lambda: build_site(True), "site_off": lambda: build_site(False),
            "site_dial": lambda: build_site(True, "dial"),
            "site_forecast": lambda: build_site(True, "forecast"),
            "stadium": build_stadium, "ferry": build_ferry, "town": build_town,
            "robot": build_robot, "bb_radio": lambda: build_baseband(6),
            "bb_lent": lambda: build_baseband(2), "site_lend": build_site_lend}


def main():
    global NIGHT
    names = list(BUILDERS) if WHICH == "all" else WHICH.split(",")
    for nm in names:
        NIGHT = nm.endswith("_night")
        _WIN.seed(7)
        reset()
        BUILDERS[nm.removesuffix("_night")]()
        sun((-0.45, -0.25, 0.9)) if nm != "robot" else sun((-0.15, -0.25, 0.96), strength=3.2, angle=22.0)
        iso_camera(margin=0.12 if nm == "robot" else 0.06)
        render(nm)


main()
