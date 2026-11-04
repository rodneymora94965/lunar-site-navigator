import bpy, bmesh, numpy as np, math, sys, json, os
from mathutils import Vector, Euler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from horizon2 import zat

P = json.load(open(os.environ.get('ESC_PARAMS', 'params.json')))
SITE = np.array(P.get('site', [204.0, 625.0]))
HCAM = P.get('hcam', 4.5)
AZ0, FOVH = P['cam_az'], P['fov_h']
SUN_AZ, SUN_EL = P['sun_az'], P['sun_el']
EAR_AZ, EAR_EL, EAR_PH = P['earth_az'], P['earth_el'], P.get('earth_scale', 1.0)
W, H = P['res']
SAMPLES = P.get('samples', 48)
OUT = P['out']
CAM_PITCH = P.get('cam_pitch', 4.0)
R_MOON = 1737400.0

lam = math.atan2(SITE[0], SITE[1]); s, c = math.sin(lam), math.cos(lam)
z0 = float(zat(np.array([SITE[0]]), np.array([SITE[1]]))[0])

# ---------- malla radial (log) en el cono de vista ----------
span = FOVH * 0.5 + 12.0
naz = int(2 * span / 0.09)
azs = AZ0 + np.linspace(-span, span, naz)
r_min, r_max, ratio = 2.5, 150000.0, 1.014
nr = int(math.log(r_max / r_min) / math.log(ratio))
rs = r_min * ratio ** np.arange(nr)
A, Rr = np.meshgrid(np.radians(azs), rs)          # (nr, naz)
ex, ny = np.sin(A) * Rr, np.cos(A) * Rr          # local este / norte
mx = SITE[0] + np.cos(A) * Rr * s + np.sin(A) * Rr * c
my = SITE[1] + np.cos(A) * Rr * c - np.sin(A) * Rr * s
zz = zat(mx.ravel(), my.ravel()).reshape(mx.shape)
zz = np.where(np.isnan(zz), np.nanmean(zz), zz)
zl = zz - z0 - Rr ** 2 / (2 * R_MOON)
# micro-relieve ilustrativo cerca de la camara (ondas multiescala deterministas)
rng = np.random.default_rng(7)
WAVES = []
for lamb, amp in [(55, .55), (24, .30), (11, .16), (5.0, .075), (2.2, .035), (1.0, .015)]:
    for _ in range(9):
        th = rng.uniform(0, 2 * np.pi); ph = rng.uniform(0, 2 * np.pi); lm = lamb * rng.uniform(.75, 1.3)
        WAVES.append((math.cos(th) * 2 * np.pi / lm, math.sin(th) * 2 * np.pi / lm, ph, amp / 3.0))
def fbm(x, y):
    out = np.zeros_like(x, dtype=float)
    for kx, ky, ph, a in WAVES: out += a * np.sin(kx * x + ky * y + ph)
    return out
CR = []
rc = np.random.default_rng(21)
for i in range(P.get('craters', 140)):
    R = 0.8 + (rc.random() ** 3.0) * 45
    rr = 8 + rc.random() ** 1.3 * 420; aa = math.radians(AZ0 + rc.uniform(-span, span))
    CR.append((math.sin(aa) * rr, math.cos(aa) * rr, R, R * rc.uniform(.10, .18)))
def craters(x, y):
    out = np.zeros_like(x, dtype=float)
    for cx, cy, R, dep in CR:
        d = np.hypot(x - cx, y - cy) / R
        bowl = np.where(d < 1, -dep * (1 - d ** 2) ** 1.0, 0.0)
        rim = 0.22 * dep * np.exp(-((d - 1.05) / 0.22) ** 2) + 0.06 * dep * np.exp(-np.clip(d - 1.2, 0, None) / 1.4) * (d > 1.2)
        out += bowl + rim
    return out
def extra(x, y, r):
    f = np.clip(1.0 - (r - 150) / 1200.0, 0, 1) ** 1.5
    return (fbm(x, y) * P.get('micro', 1.0) + craters(x, y)) * f
zl = zl + extra(ex, ny, Rr)

verts = np.stack([ex.ravel(), ny.ravel(), zl.ravel()], 1).astype(np.float32)
idx = np.arange(nr * naz).reshape(nr, naz)
quad = np.stack([idx[:-1, :-1], idx[:-1, 1:], idx[1:, 1:], idx[1:, :-1]], -1).reshape(-1, 4)

me = bpy.data.meshes.new('terreno')
me.vertices.add(len(verts)); me.vertices.foreach_set('co', verts.ravel())
me.loops.add(len(quad) * 4); me.loops.foreach_set('vertex_index', quad.ravel().astype(np.int32))
me.polygons.add(len(quad))
me.polygons.foreach_set('loop_start', (np.arange(len(quad)) * 4).astype(np.int32))
me.polygons.foreach_set('loop_total', np.full(len(quad), 4, np.int32))
me.update(calc_edges=True)
for p in me.polygons: p.use_smooth = True if False else False
ob = bpy.data.objects.new('terreno', me)
bpy.context.scene.collection.objects.link(ob)
me.polygons.foreach_set('use_smooth', np.ones(len(quad), bool))
me.shade_smooth() if hasattr(me, 'shade_smooth') else None

# ---------- material regolito ----------
mat = bpy.data.materials.new('regolito'); mat.use_nodes = True
nt = mat.node_tree; nt.nodes.clear()
out = nt.nodes.new('ShaderNodeOutputMaterial'); bsdf = nt.nodes.new('ShaderNodeBsdfPrincipled')
bsdf.inputs['Roughness'].default_value = 1.0
for k in ('Specular IOR Level', 'Specular'):
    if k in bsdf.inputs: bsdf.inputs[k].default_value = 0.15
tc = nt.nodes.new('ShaderNodeTexCoord')
def noise(scale, detail, rough=0.6):
    n = nt.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale
    n.inputs['Detail'].default_value = detail; n.inputs['Roughness'].default_value = rough
    nt.links.new(tc.outputs['Object'], n.inputs['Vector']); return n
n_big = noise(0.05, 6); n_mid = noise(0.8, 8); n_fine = noise(14, 6, 0.7)
# albedo variable (maria/regolito gris cálido)
mix = nt.nodes.new('ShaderNodeMix'); mix.data_type = 'RGBA'
mix.inputs['A'].default_value = (0.085, 0.080, 0.075, 1); mix.inputs['B'].default_value = (0.20, 0.19, 0.175, 1)
nt.links.new(n_big.outputs['Fac'], mix.inputs['Factor'])
mul = nt.nodes.new('ShaderNodeMix'); mul.data_type = 'RGBA'; mul.blend_type = 'MULTIPLY'
mul.inputs['Factor'].default_value = 0.6
nt.links.new(mix.outputs['Result'], mul.inputs['A']); nt.links.new(n_fine.outputs['Color'], mul.inputs['B'])
mul2 = nt.nodes.new('ShaderNodeMix'); mul2.data_type = 'RGBA'; mul2.blend_type = 'MULTIPLY'; mul2.inputs['Factor'].default_value = 0.5
nt.links.new(mul.outputs['Result'], mul2.inputs['A']); nt.links.new(n_mid.outputs['Color'], mul2.inputs['B'])
gain = nt.nodes.new('ShaderNodeBrightContrast'); gain.inputs['Bright'].default_value = 0.35
nt.links.new(mul2.outputs['Result'], gain.inputs['Color'])
nt.links.new(gain.outputs['Color'], bsdf.inputs['Base Color'])
bump1 = nt.nodes.new('ShaderNodeBump'); bump1.inputs['Strength'].default_value = 0.8; bump1.inputs['Distance'].default_value = 0.05
nt.links.new(n_fine.outputs['Fac'], bump1.inputs['Height'])
bump2 = nt.nodes.new('ShaderNodeBump'); bump2.inputs['Strength'].default_value = 0.6; bump2.inputs['Distance'].default_value = 0.3
nt.links.new(n_mid.outputs['Fac'], bump2.inputs['Height']); nt.links.new(bump1.outputs['Normal'], bump2.inputs['Normal'])
nt.links.new(bump2.outputs['Normal'], bsdf.inputs['Normal'])
nt.links.new(bsdf.outputs['BSDF'], out.inputs['Surface'])
ob.data.materials.append(mat)

# ---------- rocas ----------
def make_rock(seed):
    bm = bmesh.new(); bmesh.ops.create_icosphere(bm, subdivisions=4, radius=1.0)
    rg = np.random.default_rng(seed)
    ws = [(rg.normal(size=3) * 1.7, rg.uniform(0, 6.28), a) for a in (0.22, 0.10, 0.05, 0.025) for _ in range(3)]
    sx, sy, sz = rg.uniform(.8, 1.3), rg.uniform(.7, 1.2), rg.uniform(.5, .8)
    for v in bm.verts:
        p = np.array(v.co); d = 1.0
        for k, ph, a in ws: d += a * math.sin(float(np.dot(k, p)) * (1 + 3 * a) + ph) * (3 if a < 0.06 else 1)
        v.co = Vector((v.co.x * sx, v.co.y * sy, v.co.z * sz)) * max(d, 0.5)
    m = bpy.data.meshes.new(f'rock{seed}'); bm.to_mesh(m); bm.free()
    for p in m.polygons: p.use_smooth = True
    m.materials.append(mat); return m
rock_meshes = [make_rock(i) for i in range(6)]
rg = np.random.default_rng(11)
nrock = P.get('rocks', 1400)
col = bpy.data.collections.new('rocas'); bpy.context.scene.collection.children.link(col)
for i in range(nrock):
    r = 3.5 + (rg.random() ** 2.2) * 300
    az = math.radians(AZ0 + rg.uniform(-span, span))
    rx, ry = math.sin(az) * r, math.cos(az) * r
    mxx = SITE[0] + math.cos(az) * r * s + math.sin(az) * r * c
    myy = SITE[1] + math.cos(az) * r * c - math.sin(az) * r * s
    zr = float(zat(np.array([mxx]), np.array([myy]))[0]) - z0 - r ** 2 / (2 * R_MOON)
    zr += float(extra(np.array([rx]), np.array([ry]), np.array([r]))[0])
    size = 0.06 + (rg.random() ** 3.5) * 1.5
    o = bpy.data.objects.new(f'r{i}', rock_meshes[i % 6]); o.location = (rx, ry, zr + size * 0.1)
    o.scale = (size * rg.uniform(.7, 1.4), size * rg.uniform(.7, 1.4), size * rg.uniform(.6, 1.1))
    o.rotation_euler = (0, 0, rg.uniform(0, 6.28)); col.objects.link(o)

# ---------- Sol ----------
sd = bpy.data.lights.new('sol', 'SUN'); sd.energy = P.get('sun_strength', 4.0); sd.angle = math.radians(0.533)
so = bpy.data.objects.new('sol', sd); bpy.context.scene.collection.objects.link(so)
a, e = math.radians(SUN_AZ), math.radians(SUN_EL)
to_sun = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
so.rotation_euler = (-to_sun).to_track_quat('-Z', 'Y').to_euler()

# ---------- Tierra ----------
DE = 150000.0; RE = DE * math.tan(math.radians(0.949)) * EAR_PH
ea, ee = math.radians(EAR_AZ), math.radians(EAR_EL)
epos = Vector((math.sin(ea) * math.cos(ee), math.cos(ea) * math.cos(ee), math.sin(ee))) * DE
bpy.ops.mesh.primitive_uv_sphere_add(segments=96, ring_count=64, radius=RE, location=epos)
earth = bpy.context.object; bpy.ops.object.shade_smooth()
earth.visible_shadow = False
em = bpy.data.materials.new('tierra'); em.use_nodes = True; et = em.node_tree; et.nodes.clear()
eo = et.nodes.new('ShaderNodeOutputMaterial'); eb = et.nodes.new('ShaderNodeBsdfPrincipled')
etc = et.nodes.new('ShaderNodeTexCoord')
def en(scale, det, rough=0.55):
    n = et.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = det
    n.inputs['Roughness'].default_value = rough; et.links.new(etc.outputs['Object'], n.inputs['Vector']); return n
# rotar coordenadas del objeto para mostrar una cara interesante
mp = et.nodes.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = P.get('earth_rot', (0.6, 0.3, 1.1))
et.links.new(etc.outputs['Object'], mp.inputs['Vector'])
def en2(scale, det, rough=0.55):
    n = et.nodes.new('ShaderNodeTexNoise'); n.inputs['Scale'].default_value = scale; n.inputs['Detail'].default_value = det
    n.inputs['Roughness'].default_value = rough; et.links.new(mp.outputs['Vector'], n.inputs['Vector']); return n
land = en2(1.0 / RE * 2.1, 8)
cl = en2(1.0 / RE * 3.4, 9, 0.62)
rampL = et.nodes.new('ShaderNodeValToRGB'); rampL.color_ramp.elements[0].position = 0.52; rampL.color_ramp.elements[1].position = 0.54
et.links.new(land.outputs['Fac'], rampL.inputs['Fac'])
ocean = (0.02, 0.10, 0.38, 1); terr = (0.22, 0.27, 0.10, 1)
rampL.color_ramp.elements[0].color = ocean; rampL.color_ramp.elements[1].color = terr
rampC = et.nodes.new('ShaderNodeValToRGB'); rampC.color_ramp.elements[0].position = 0.50; rampC.color_ramp.elements[1].position = 0.66
rampC.color_ramp.elements[0].color = (0, 0, 0, 1); rampC.color_ramp.elements[1].color = (1, 1, 1, 1)
et.links.new(cl.outputs['Fac'], rampC.inputs['Fac'])
mixE = et.nodes.new('ShaderNodeMix'); mixE.data_type = 'RGBA'
et.links.new(rampC.outputs['Color'], mixE.inputs['Factor'])
et.links.new(rampL.outputs['Color'], mixE.inputs['A']); mixE.inputs['B'].default_value = (0.9, 0.92, 0.95, 1)
et.links.new(mixE.outputs['Result'], eb.inputs['Base Color'])
eb.inputs['Roughness'].default_value = 0.6
# halo atmosférico solo en el lado iluminado
lw = et.nodes.new('ShaderNodeLayerWeight'); lw.inputs['Blend'].default_value = 0.30
geo = et.nodes.new('ShaderNodeNewGeometry')
dot = et.nodes.new('ShaderNodeVectorMath'); dot.operation = 'DOT_PRODUCT'
dot.inputs[1].default_value = tuple(to_sun)
et.links.new(geo.outputs['Normal'], dot.inputs[0])
cl2 = et.nodes.new('ShaderNodeMath'); cl2.operation = 'MAXIMUM'; cl2.inputs[1].default_value = 0.0
et.links.new(dot.outputs['Value'], cl2.inputs[0])
mfac = et.nodes.new('ShaderNodeMath'); mfac.operation = 'MULTIPLY'
et.links.new(lw.outputs['Facing'], mfac.inputs[0]); et.links.new(cl2.outputs['Value'], mfac.inputs[1])
emis = et.nodes.new('ShaderNodeEmission'); emis.inputs['Color'].default_value = (0.25, 0.5, 1.0, 1); emis.inputs['Strength'].default_value = 1.4
mixS = et.nodes.new('ShaderNodeMixShader'); et.links.new(mfac.outputs['Value'], mixS.inputs['Fac'])
et.links.new(eb.outputs['BSDF'], mixS.inputs[1]); et.links.new(emis.outputs['Emission'], mixS.inputs[2])
et.links.new(mixS.outputs['Shader'], eo.inputs['Surface'])
earth.data.materials.append(em)

# ---------- cielo estrellado ----------
W2, H2 = 8192, 4096
img = np.zeros((H2, W2), np.float32)
rs2 = np.random.default_rng(3)
N = 9000
lon = rs2.uniform(0, 2 * np.pi, N); lat = np.arcsin(rs2.uniform(-1, 1, N))
mag = 2.0 + rs2.exponential(1.4, N); mag = np.clip(mag, 0, 7)
bri = 10 ** (-0.4 * (mag - 1.5))
px = (lon / (2 * np.pi) * W2).astype(int) % W2; py = ((0.5 - lat / np.pi) * H2).astype(int).clip(0, H2 - 1)
for x, y, b in zip(px, py, bri):
    img[y, x] += b
from scipy.ndimage import gaussian_filter
img = gaussian_filter(img, 0.8) * 9
# banda de vía láctea tenue
yy, xx = np.mgrid[0:H2, 0:W2]
band = np.exp(-(((yy - H2 / 2 - 260 * np.sin(xx / W2 * 2 * np.pi)) / 130.0) ** 2)) * 0.0035
nz = gaussian_filter(rs2.random((H2, W2)).astype(np.float32), 12); nz = (nz - nz.min()) / (nz.max() - nz.min())
img += band * (0.4 + nz)
rgb = np.stack([img * 1.0, img * 0.97, img * 1.05, np.ones_like(img)], -1)[::-1]
bi = bpy.data.images.new('estrellas', W2, H2, float_buffer=True); bi.pixels.foreach_set(rgb.ravel().astype(np.float32)); bi.update()
w = bpy.data.worlds.new('w'); bpy.context.scene.world = w; w.use_nodes = True
wn = w.node_tree; wn.nodes.clear()
wo = wn.nodes.new('ShaderNodeOutputWorld'); bg = wn.nodes.new('ShaderNodeBackground'); te = wn.nodes.new('ShaderNodeTexEnvironment')
te.image = bi; bg.inputs['Strength'].default_value = P.get('star_strength', 1.0)
wn.links.new(te.outputs['Color'], bg.inputs['Color']); wn.links.new(bg.outputs['Background'], wo.inputs['Surface'])

# ---------- cámara ----------
cd = bpy.data.cameras.new('cam'); cd.sensor_width = 36.0
cd.lens = 18.0 / math.tan(math.radians(FOVH / 2))
co = bpy.data.objects.new('cam', cd); bpy.context.scene.collection.objects.link(co)
co.location = (0, 0, HCAM)
ca = math.radians(AZ0)
co.rotation_euler = (math.radians(90 + CAM_PITCH), 0, -ca)   # mira al azimut, pitch hacia arriba
bpy.context.scene.camera = co
cd.dof.use_dof = False; cd.clip_start = 0.05; cd.clip_end = 1.0e6

# ---------- render ----------
sc = bpy.context.scene
sc.render.engine = 'CYCLES'; sc.cycles.device = 'CPU'; sc.cycles.samples = SAMPLES
sc.cycles.use_denoising = True
try: sc.cycles.denoiser = 'OPENIMAGEDENOISE'
except Exception: pass
sc.cycles.max_bounces = 3; sc.cycles.diffuse_bounces = 2; sc.cycles.glossy_bounces = 1
sc.render.resolution_x, sc.render.resolution_y = W, H; sc.render.resolution_percentage = 100
sc.view_settings.view_transform = P.get('view', 'Filmic') if P.get('view') in ('Standard', 'Filmic', 'AgX') else 'Standard'
sc.view_settings.exposure = P.get('exposure', 0.0)
sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'PNG'
if 'frames' in P:
    os.makedirs(P['frames_dir'], exist_ok=True)
    for k, fr in enumerate(P['frames']):
        fp = os.path.join(P['frames_dir'], 'f%03d.png' % k)
        if os.path.exists(fp): continue
        a, e = math.radians(fr['sun_az']), math.radians(fr['sun_el'])
        v = Vector((math.sin(a) * math.cos(e), math.cos(a) * math.cos(e), math.sin(e)))
        so.rotation_euler = (-v).to_track_quat('-Z', 'Y').to_euler()
        dot.inputs[1].default_value = tuple(v)
        ea, ee = math.radians(fr['earth_az']), math.radians(fr['earth_el'])
        earth.location = Vector((math.sin(ea) * math.cos(ee), math.cos(ea) * math.cos(ee), math.sin(ee))) * DE
        sc.render.filepath = fp
        bpy.ops.render.render(write_still=True)
        print('FRAME', k, flush=True)
    print('ALLOK')
else:
    sc.render.filepath = OUT
    bpy.ops.render.render(write_still=True)
    print('OK', OUT)
