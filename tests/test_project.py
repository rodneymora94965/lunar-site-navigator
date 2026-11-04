"""Pruebas contra referencias independientes: JPL Horizons, soluciones analiticas y una segunda implementacion.

test_app_e2e.py y las pruebas de node se saltan solas si Playwright o Node no estan instalados.
"""
import re
import base64
import csv
import json
import math
import shutil
import subprocess
import sys
import zlib
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import horizon2 as hz  # noqa: E402

AU_KM = 149597870.7


@pytest.fixture(scope="module")
def data():
    return json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))


def unpack(pair, scale):
    delta = np.frombuffer(zlib.decompress(base64.b64decode(pair[1])), dtype="<i2").astype(np.int64)
    return (pair[0] + np.r_[0, np.cumsum(delta)]) / scale


def vectors(data):
    e = data["eph"]

    def vec(lat, lon, dist):
        la, lo = np.radians(lat), np.radians(lon)
        return np.c_[dist * np.cos(la) * np.cos(lo), dist * np.cos(la) * np.sin(lo), dist * np.sin(la)]

    return (vec(unpack(e["slat"], 1000), unpack(e["slon"], 1000), unpack(e["sd"], 1e5) * AU_KM),
            vec(unpack(e["elat"], 1000), unpack(e["elon"], 1000), unpack(e["ed"], 1)))


# ---------- efemerides contra JPL Horizons (respuesta guardada en tests/fixtures) ----------
def test_ephemeris_matches_jpl_horizons(data):
    S, E = vectors(data)
    t0 = datetime(2026, 11, 1, tzinfo=timezone.utc)
    rows = list(csv.DictReader(open(ROOT / "tests" / "fixtures" / "horizons_sol_tierra.csv", encoding="utf-8")))
    assert len(rows) == 120
    checked = 0
    for r in rows:
        t = datetime.strptime(r["utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        i = int((t - t0).total_seconds() // 3600)
        if i >= len(S):  # una fecha de la muestra cae despues del final de los datos
            continue
        checked += 1
        V = (S if r["cuerpo"] == "sol" else E)[i:i + 1]
        az, el = hz.az_el(V, float(r["lat"]), float(r["lon"]))
        assert el[0] == pytest.approx(float(r["hz_el"]), abs=0.003)
        assert abs((az[0] - float(r["hz_az"]) + 180) % 360 - 180) < 0.05
    assert checked >= 110


# ---------- geometria contra soluciones analiticas ----------
def flat_terrain(extra=None):
    x = np.arange(-300000.0, 300001.0, 500.0)
    Z = np.zeros((len(x), len(x)), dtype=np.float32)
    if extra:
        extra(Z, x)
    return hz.Terrain(None, (Z, -300250.0, 300250.0, 500.0))


def test_horizon_dip_on_bare_sphere():
    h = 100.0
    rays = np.arange(10.0, 150000.0, 10.0)
    _, H = hz.horizon(flat_terrain(), 0.0, 0.0, h, naz=8, rays=rays)
    exact = -math.degrees(math.acos(hz.R / (hz.R + h)))
    assert H == pytest.approx(exact, abs=1e-3)


@pytest.mark.parametrize("site,tower", [((0.0, 20000.0), (10000.0, 20000.0)), ((20000.0, 0.0), (20000.0, -10000.0))])
def test_horizon_azimuth_points_east_of_local_north(site, tower):
    """A 10 km al este local. Norte es hacia afuera del polo sur; el este se dedujo a mano para cada caso."""

    def add(Z, x):
        ix = np.argmin(abs(x - tower[0]))
        iy = np.argmin(abs(x + tower[1]))
        Z[iy, ix] = 3000.0  # un solo pixel: el pico queda exactamente a 10 km

    rays = np.arange(100.0, 30000.0, 50.0)
    azs, H = hz.horizon(flat_terrain(add), site[0], site[1], 0.0, naz=360, rays=rays)
    assert azs[int(np.argmax(H))] == pytest.approx(90, abs=3)
    expected = math.degrees(math.atan2(3000.0 - 10000.0 ** 2 / (2 * hz.R), 10000.0))
    assert H.max() == pytest.approx(expected, abs=0.05)


def test_stereographic_matches_dem_extent():
    """El DEM polar va hasta 80S con un borde publicado de 304 km."""
    x, y = hz.xy_from_latlon(-80.0, 0.0)
    assert x == pytest.approx(0, abs=1e-6)
    assert y == pytest.approx(304000, abs=100)
    assert hz.xy_from_latlon(-90.0, 45.0) == pytest.approx((0, 0), abs=1e-6)
    lat, lon = hz.latlon_from_xy(*hz.xy_from_latlon(-89.5, -120.0))
    assert (lat, lon) == pytest.approx((-89.5, -120.0))


def test_sun_and_earth_ranges_at_pole_match_lunar_geometry(data):
    """Oblicuidad lunar de 1,54 grados e inclinacion del ecuador respecto a la orbita: valores de referencia conocidos."""
    S, E = vectors(data)
    _, se = hz.az_el(S, -90.0, 0.0)
    _, te = hz.az_el(E, -90.0, 0.0)
    assert 1.5 < se.max() < 1.7
    assert 6 < te.max() < 8.5


def test_earth_cycle_is_about_27_days(data):
    _, E = vectors(data)
    _, te = hz.az_el(E[:20000], -90.0, 0.0)
    F = np.abs(np.fft.rfft(te - te.mean()))
    f = np.fft.rfftfreq(len(te), 1 / 24.0)
    assert 1 / f[1 + int(np.argmax(F[1:]))] == pytest.approx(27.3, abs=0.6)


# ---------- integridad de datos y coherencia entre etapas ----------
def test_data_has_expected_sites_and_sizes(data):
    assert data["n"] == int(round(19 * 365.25 * 24))
    ids = {s["id"] for s in data["sites"]}
    assert {"14", "456", "1358", "964", "1417", "2298", "1643", "2238", "616", "1598", "im2", "shack", "polo"} == {s["id"] for s in data["sites"] if s["kind"] != "region"}
    for s in data["sites"]:
        assert len(base64.b64decode(s["hz"])) == 720
        assert len(s["heat"]) == len(data["offs"]) ** 2
    assert sorted(s["rank"] for s in data["sites"] if s["kind"] == "cand") == list(range(1, 11))


def test_heat_center_agrees_with_hourly_series(data):
    """La malla usa paso de 3 h y la serie paso de 1 h: dos calculos del mismo punto deben coincidir."""
    S, E = vectors(data)
    azs = np.arange(360.0)
    c = len(data["offs"]) // 2 * (len(data["offs"]) + 1)
    for s in data["sites"][:3]:
        H = np.frombuffer(base64.b64decode(s["hz"]), dtype="<i2") / 100
        sa, se = hz.az_el(S, s["lat"], s["lon"])
        ta, te = hz.az_el(E, s["lat"], s["lon"])
        assert 100 * hz.above(sa, se, azs, H).mean() == pytest.approx(s["heat"][c][0], abs=1.0)
        assert 100 * hz.above(ta, te, azs, H).mean() == pytest.approx(s["heat"][c][1], abs=1.0)


def test_build_output_is_complete(tmp_path):
    out = tmp_path / "final.html"
    subprocess.run([sys.executable, str(ROOT / "build.py"), str(out)], cwd=ROOT, check=True)
    html = out.read_text(encoding="utf-8")
    assert html.lower().startswith("<!doctype html>")
    assert 'name="viewport"' in html and 'charset="utf-8"' in html
    for token in ("__DATA__", "__APP__", "__CORE__", "__VIDEO__", "__IMG_"):
        assert token not in html


# ---------- validacion contra el producto cientifico de LROC ----------
IMG = ROOT / "auditoria" / "validacion" / "WAC_POLE_ILL_PCT_SOUTH_100M.IMG"


def read_img():
    raw = IMG.read_bytes()
    label = raw[:9712].decode("latin-1")
    assert "SAMPLE_TYPE                = PC_REAL" in label and "SCALING_FACTOR" not in label
    A = np.frombuffer(raw[-1214 * 1214 * 4:], dtype="<f4").reshape(1214, 1214).astype(float)
    A[A < -1e30] = np.nan
    return A


@pytest.mark.skipif(not IMG.exists(), reason="falta el IMG de LROC")
def test_lroc_img_is_percent_and_published_metrics_hold():
    A = read_img()
    assert np.nanmax(A) == pytest.approx(71.58, abs=0.01)
    rows = list(csv.DictReader(open(ROOT / "auditoria" / "validacion" / "validacion_config_app.csv", encoding="utf-8")))

    def metrics(kind):
        rr = [r for r in rows if r["tipo"] == kind]
        l = np.array([A[int((60700 - float(r["y_m"])) / 100), int((float(r["x_m"]) + 60700) / 100)] for r in rr])
        m = np.array([float(r["h5_punto"]) for r in rr])
        return (m - l).mean(), np.abs(m - l).mean(), np.corrcoef(m, l)[0, 1]

    assert metrics("celda") == pytest.approx((-0.3, 1.3, 0.985), abs=0.05)
    assert metrics("candidato") == pytest.approx((7.4, 7.4, 0.90), abs=0.05)


@pytest.mark.parametrize("path", ["README.md", "src/app.js"])
def test_public_text_has_no_old_lroc_reading(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    for old in ("conservadoras", "figures are conservative", "−15,8", "−15.8", "-15.8", "-15,8", "100×DN/255", "−17,0", "−17.0"):
        assert old not in text, old
    import re
    assert not re.search(r"(correlación|correlation) 0[,.]99(?!\d)", text)  # la cifra antigua; 0,994 de PGDA es valida


# ---------- el sitio 14 no se puede presentar sin su advertencia ----------
WARN14 = {"README.md": ["site 14 is fragile and not confirmed at pixel scale", "el sitio 14 es frágil y no está confirmado a escala de píxel", "geometry error", "error de geometría"],
          "src/app.js": ["Site 14 is fragile and not confirmed at pixel scale", "El sitio 14 es frágil y no está confirmado a escala de píxel", "warn14:\"Frágil y sin confirmar", "warn14:\"Fragile and not confirmed", "geometry error", "error de geometría"]}
BANNED14 = [r"(?i)site 14[^.\n]{0,80}(?<!not )(confirmed|validated) by", r"(?i)sitio 14[^.\n]{0,80}(?<!no est\u00e1 )(confirmado|validado) por", r"(?i)(site|sitio) 14 \((recommended|recomendado)\)"]


def problems_site14(path, text):
    found = [f"falta: {w}" for w in WARN14[path] if w not in text]
    import re
    found += [f"prohibido: {m.group(0)}" for b in BANNED14 for m in re.finditer(b, text)]
    return found


@pytest.mark.parametrize("path", list(WARN14))
def test_site14_is_always_presented_with_its_warning(path):
    assert problems_site14(path, (ROOT / path).read_text(encoding="utf-8")) == []


def test_site14_guard_detects_removed_warning_and_false_claims():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert problems_site14("README.md", text.replace(WARN14["README.md"][0], "site 14"))
    assert problems_site14("README.md", text + "\nSite 14 is confirmed by LROC and PGDA.\n")
    assert problems_site14("README.md", text + "\nSitio 14 (recomendado)\n")


def test_card_code_shows_warning_only_for_site14():
    app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
    assert "s.id===CONTRAST_SITE" in app and "CONTRAST_SITE='14'" in app and 'data-r="warn14"' in app


def test_pgda_published_metrics_match_output():
    import re
    txt = (ROOT / "auditoria" / "validacion" / "validacion_pgda.txt").read_text(encoding="utf-8")
    for pat in (r"Sol\s+celda\s+5 m, punto \(app\)\s+121\s+-0\.3\s+1\.6\s+0\.965\s+0\.95", r"Tierra\s+celda\s+5 m, centro \(app\)\s+121\s+-1\.3\s+3\.1\s+0\.961\s+0\.91",
                r"Sol\s+candidato\s+5 m, punto \(app\)\s+10\s+\+3\.1\s+3\.8\s+0\.946\s+1\.02", r"Tierra\s+candidato\s+5 m, centro \(app\)\s+10\s+-2\.2\s+2\.6\s+0\.994\s+0\.97"):
        assert re.search(pat, txt), pat


# ---------- la recomendacion es el 456 y su criterio esta a la vista ----------
REC_WORDS = r"(?:recommended|recomendado|recomendamos|main site|sitio principal|best of the 10|mejor de los 10)"


def recommended_ids(text):
    import re
    ids = re.findall(r"(?i)(?:site|sitio)s?\s+(\d+)\s*[^.\n|]{0,60}?" + REC_WORDS, text)
    ids += re.findall(r"(?i)" + REC_WORDS + r"[^.\n|]{0,40}?(?:site|sitio)s?\s+(\d+)", text)
    return set(ids)


@pytest.mark.parametrize("path", ["README.md", "src/app.js"])
def test_only_site_456_is_presented_as_recommended(path):
    assert recommended_ids((ROOT / path).read_text(encoding="utf-8")) <= {"456"}


def test_recommendation_guard_detects_other_sites():
    assert recommended_ids("Site 14 is the main site.") == {"14"}
    assert recommended_ids("El sitio principal es el sitio 1358.") == {"1358"}
    assert recommended_ids("Sitio 964 (recomendado)") == {"964"}
    assert recommended_ids("Site 456 is the main site.") == {"456"}


def test_app_constants_point_to_456_and_14():
    app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
    assert "MAIN_SITE='456', CONTRAST_SITE='14'" in app
    assert "sel:[MAIN_SITE,CONTRAST_SITE,'1358']" in app


CRITERION = {"es": ["Tierra de al menos 40 % en todo ±100 m", "Sol y Tierra juntos de al menos 10 % en el punto", "Acuerdo", "entre modelo, LROC y PGDA", "Rango estrecho", "Bolsón amplio", "Noche corta", "solo como desempate", "después de ver los datos"],
             "en": ["Earth of at least 40 % throughout ±100 m", "Sun and Earth together at least 10 % at the point", "Agreement", "among model, LROC and PGDA", "Narrow range", "Large pocket", "Short night", "only as a tiebreaker", "after seeing the data"]}


@pytest.mark.parametrize("path", ["README.md", "src/app.js"])
@pytest.mark.parametrize("lang", ["es", "en"])
def test_selection_criterion_appears_in_both_languages(path, lang):
    text = (ROOT / path).read_text(encoding="utf-8")
    assert [w for w in CRITERION[lang] if w not in text] == []


def test_presentation_change_did_not_touch_figures():
    """El cambio de sitio principal es de presentacion: los datos conservan su orden numerico original."""
    sites = {s["id"]: s for s in json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))["sites"]}
    assert sites["14"]["rank"] == 1 and sites["1358"]["rank"] == 2 and sites["456"]["rank"] == 3


# ---------- la imagen principal y el video de la app son los del 456 ----------
def built_html(tmp_path):
    out = tmp_path / "final.html"
    subprocess.run([sys.executable, str(ROOT / "build.py"), str(out)], cwd=ROOT, check=True)
    return out.read_text(encoding="utf-8")


def test_app_embeds_site456_hero_and_video_not_the_old_ones(tmp_path):
    html = built_html(tmp_path)
    b64 = lambda n: base64.b64encode((ROOT / "renders" / n).read_bytes()).decode()
    assert b64("hero_sitio456.jpg") in html and b64("video_sitio456_app.mp4") in html
    assert b64("hero.jpg") not in html and b64("video.mp4") not in html


def test_hero_and_video_captions_name_456_and_not_14():
    import re
    app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
    caps = re.findall(r'cap(?:Hero|Video):"((?:[^"\\]|\\.)*)"', app)
    assert len(caps) == 4
    for c in caps:
        assert re.search(r"\b456\b", c) and not re.search(r"\b14\b", c), c
    assert "del 8 jun al 7 jul de 2030" in app and "8 Jun to 7 Jul 2030" in app
    assert "21 jun 2030, 11:00 UTC" in app and "21 Jun 2030, 11:00 UTC" in app and "4,5 m" in app and "4.5 m" in app


def test_readme_uses_new_cover_and_comparison():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    assert "renders/luna_portada_v5_sitio456.png" in text and "renders/luna_comparacion_4_sitios_v2.png" in text
    assert "luna_portada_v4" not in text and "luna_comparacion_4_sitios.png" not in text
    assert "still shows site 14" not in text


NEW_RENDERS = ["hero_sitio456.jpg", "video_sitio456_app.mp4", "luna_portada_v5_sitio456.png", "luna_comparacion_4_sitios_v2.png", "luna_sitio456_linea_tiempo.mp4"]


def test_marcar_renders_does_not_write_new_renders(tmp_path):
    pytest.importorskip("PIL")
    src = (ROOT / "scripts" / "marcar_renders.py").read_text(encoding="utf-8")
    for n in ("hero.jpg", "video.mp4", "luna_portada_v4.png", "luna_comparacion_4_sitios.png"):
        assert f'"{n}"' not in src
    if not (ROOT / "auditoria" / "antes" / "renders_originales" / "14.jpg").exists():
        pytest.skip("faltan los originales")
    env = dict(__import__("os").environ, MARCAR_SALIDA=str(tmp_path))
    subprocess.run([sys.executable, str(ROOT / "scripts" / "marcar_renders.py")], check=True, env=env)
    written = {p.name for p in tmp_path.iterdir()}
    assert written and not written & set(NEW_RENDERS)


# ---------- hora y direccion de la luz: resultado real y sus limites ----------
LIGHT_LIMITS = {
    "es": ["5 fechas de 2009", "solo Site04", "No valida la predicción de 2026 a 2045", "más puntos con luz", "por debajo de 0,5"],
    "en": ["5 dates in 2009", "only Site04", "does not validate the 2026–2045 prediction", "more lit points", "below 0.5"],
}
LIGHT_FILES = {"README.md": ["es", "en"], "src/app.js": ["es", "en"], "docs/entrega/descripcion_entrega_EN.md": ["en"], "docs/entrega/guion_demo_30s.md": ["en"], "docs/entrega/guion_presentacion_3min.md": ["es"], "auditoria/validacion/prueba_fechas_lroc.md": ["es"]}
LIGHT_BANNED = [
    r"(?i)\b(times?|hours?|directions?)\b[^.\n]{0,60}\bun-?validated",
    r"(?i)\b(times?|hours?|directions?)\b[^.\n]{0,60}\bnot (yet |been )*validated",
    r"(?i)\bnot (yet |been )*validated\b[^.\n]{0,40}\b(times?|hours?|directions?|when)\b",
    r"(?i)\b(horas?|direcci[oó]n(es)?)\b[^.\n]{0,60}(no (est[aá]n? )?validad|sin validar)",
    r"(?i)sin ejecutar",
    r"(?i)faltan las im[aá]genes",
    r"(?i)todav[ií]a no lo sabemos",
]


def light_problems(text, langs):
    probs = [p for p in LIGHT_BANNED if re.search(p, text)]
    low = text.lower()
    probs += [w for la in langs for w in LIGHT_LIMITS[la] if w.lower() not in low]
    return probs


@pytest.mark.parametrize("path", list(LIGHT_FILES))
def test_light_timing_is_stated_as_tested_and_keeps_limits(path):
    assert light_problems((ROOT / path).read_text(encoding="utf-8"), LIGHT_FILES[path]) == []


def test_light_guard_detects_old_claim_and_removed_limit():
    ok = " ".join(LIGHT_LIMITS["en"])
    assert light_problems(ok, ["en"]) == []
    assert light_problems(ok + " Times and directions of light are not validated.", ["en"])
    assert light_problems(ok + " Las horas y direcciones no están validadas.", ["en"])
    assert light_problems(ok.replace("below 0.5", ""), ["en"]) == ["below 0.5"]


def test_app_keeps_limits_in_each_language_block():
    app = (ROOT / "src" / "app.js").read_text(encoding="utf-8")
    es, en = app.split('tWhen:"Date and time (UTC)"', 1)
    assert not light_problems(es, ["es"]) and not light_problems(en, ["en"])
    for num in ("+0,474", "+0,877", "+0,815", "+0,777", "+0,743", "0,737"):
        assert num in es
    for num in ("+0.474", "+0.877", "+0.815", "+0.777", "+0.743", "0.737"):
        assert num in en


def test_description_stays_within_250_words():
    assert len((ROOT / "docs/entrega/descripcion_entrega_EN.md").read_text(encoding="utf-8").split()) <= 250


def test_light_figures_match_the_real_output():
    val = ROOT / "auditoria" / "validacion"
    rows = list(csv.DictReader(open(val / "validacion_fechas_lroc.csv", encoding="utf-8")))
    assert "RESULTADO DEL CRITERIO: APRUEBA" in (val / "validacion_fechas_lroc.txt").read_text(encoding="utf-8")
    model = [r for r in rows if r["prediccion"] == "modelo"]
    ctrl = [r for r in rows if r["prediccion"] != "modelo"]
    assert len(model) == 5 and len(ctrl) == 15
    for r in rows:
        vp, vn, fp, fn = (int(r[k]) for k in ("vp", "vn", "fp", "fn"))
        assert vp + vn + fp + fn == 6400
        mcc = (vp * vn - fp * fn) / ((vp + fp) * (vp + fn) * (vn + fp) * (vn + fn)) ** 0.5
        assert abs(mcc - float(r["mcc"])) < 0.001
    assert [float(r["mcc"]) for r in model] == [0.474, 0.877, 0.815, 0.777, 0.743]
    assert abs(sum(float(r["mcc"]) for r in model) / 5 - 0.737) < 0.001
    for r in model:
        assert float(r["mcc"]) > max(float(c["mcc"]) for c in ctrl if c["producto"] == r["producto"])
    assert round(min(float(c["mcc"]) for c in ctrl), 2) == -0.30 and round(max(float(c["mcc"]) for c in ctrl), 2) == 0.36
    assert sum(int(r["vp"]) + int(r["fp"]) for r in model) == 7881
    assert sum(int(r["vp"]) + int(r["fn"]) for r in model) == 5135
    assert sum(int(r["fp"]) for r in model) == 2797 and sum(int(r["fn"]) for r in model) == 51
    assert all(int(r["vp"]) + int(r["fp"]) > int(r["vp"]) + int(r["fn"]) for r in model)


# ---------- segunda implementacion: JavaScript del navegador contra Python ----------
node = shutil.which("node")


def run_node(code):
    full = f"const C=require({json.dumps(str(ROOT / 'src' / 'core.js'))});{code}"
    return json.loads(subprocess.run([node, "-e", full], capture_output=True, text=True, check=True).stdout)


@pytest.mark.skipif(node is None, reason="node no instalado")
def test_js_az_el_matches_python_and_horizons(data):
    r = next(q for q in csv.DictReader(open(ROOT / "tests" / "fixtures" / "horizons_sol_tierra.csv", encoding="utf-8")) if q["cuerpo"] == "tierra" and q["sitio"] == "im2")
    t = datetime.strptime(r["utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
    i = int((t - datetime(2026, 11, 1, tzinfo=timezone.utc)).total_seconds() // 3600)
    e = data["eph"]
    a = [unpack(e["elat"], 1000)[i], unpack(e["elon"], 1000)[i], unpack(e["ed"], 1)[i]]
    az, el = run_node(f"const b=C.basis({r['lat']},{r['lon']});console.log(JSON.stringify(C.azEl(b,{a[0]},{a[1]},{a[2]})))")
    assert el == pytest.approx(float(r["hz_el"]), abs=0.003)
    assert az == pytest.approx(float(r["hz_az"]), abs=0.05)


@pytest.mark.skipif(node is None, reason="node no instalado")
def test_js_disc_fraction_matches_numeric_integration():
    r = 0.27
    ms = [-0.3, -0.2, -0.1, 0.0, 0.1, 0.2, 0.3]
    js = run_node(f"console.log(JSON.stringify({ms}.map(m=>C.discFraction(m,{r}))))")
    g = np.linspace(-r, r, 1601)
    X, Y = np.meshgrid(g, g)
    disc = X ** 2 + Y ** 2 <= r ** 2
    for m, v in zip(ms, js):
        assert v == pytest.approx(((Y > -m) & disc).sum() / disc.sum(), abs=0.003)


@pytest.mark.skipif(node is None, reason="node no instalado")
def test_js_power_model():
    v = run_node("console.log(JSON.stringify(C.powerW(1,1,0,2,0.25)))")
    assert v == pytest.approx(1361 * 2 * 0.25)


@pytest.mark.skipif(node is None, reason="node no instalado")
def test_js_horizon_matches_python_on_synthetic_terrain():
    n, d = 301, 500.0
    x0, y0 = -75250.0, 75250.0
    i, j = np.mgrid[0:n, 0:n]
    Z = (800 * np.sin(i / 17.0) * np.cos(j / 23.0)).astype(np.float32)
    T = hz.Terrain(None, (Z, x0, y0, d))
    x, y = 3000.0, 7000.0
    rays = np.r_[np.arange(500.0, 3000.0, 500.0), np.arange(3000.0, 70000.0, 250.0)]
    _, Hp = hz.horizon(T, x, y, 5.0, naz=72, rays=rays)
    code = ("const n=301,Z=new Float32Array(n*n);for(let i=0;i<n;i++)for(let j=0;j<n;j++)Z[i*n+j]=Math.fround(800*Math.sin(i/17)*Math.cos(j/23));"
            f"const dem={{wide:{{x0:{x0},y0:{y0},d:{d},h:n,w:n,Z}}}};console.log(JSON.stringify(Array.from(C.horizon(dem,{x},{y},5,72,70000))));")
    Hj = np.array(run_node(code))
    assert np.abs(Hj - Hp).max() < 0.05
