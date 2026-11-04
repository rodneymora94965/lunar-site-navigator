"""Prueba la pagina real en un navegador. Requiere Playwright; si no esta instalado, se salta."""
import subprocess
import sys
from pathlib import Path

import pytest

pw = pytest.importorskip("playwright.sync_api")
ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def page_url(tmp_path_factory):
    out = tmp_path_factory.mktemp("b") / "final.html"
    subprocess.run([sys.executable, str(ROOT / "build.py"), str(out)], check=True)
    return out.as_uri()


@pytest.fixture(scope="module")
def browser():
    with pw.sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()


def opened(browser, url, **kw):
    ctx = browser.new_context(**kw)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(url)
    page.wait_for_selector("#app:not([hidden])", timeout=60000)
    return page, errors


def test_mobile_390_has_no_horizontal_scroll(browser, page_url):
    page, errors = opened(browser, page_url, viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, locale="es-CR")
    assert page.evaluate("[document.compatMode, innerWidth]") == ["CSS1Compat", 390]
    assert page.evaluate("document.documentElement.scrollWidth") <= 390
    assert not errors


def test_english_has_no_spanish_leak(browser, page_url):
    page, errors = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="en-US")
    page.click('.chip[data-id="456"]')
    page.click('.chip[data-id="shack"]')
    body = page.inner_text("body")
    assert page.title() == "Lunar Site Navigator"
    assert "años" not in body and "≥ 19 years" in body
    assert not errors


def test_fourth_site_does_not_replace_main(browser, page_url):
    page, _ = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    before = page.evaluate("S.sel.slice()")
    page.click('.chip[data-id="964"]')
    assert page.evaluate("S.sel.slice()") == before
    assert page.inner_text("#warn-sites") != ""


def test_table_window_matches_timeline(browser, page_url):
    page, _ = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    r = page.evaluate("(()=>{const s=S.sites[S.sel[0]],i=S.idx;let n=0;for(let k=i-240;k<i+1200;k++)n+=s.sv[k]&s.tv[k];const row=[...document.querySelectorAll('#tbl tr')].find(t=>t.innerText.startsWith('Horas con ambos'));return [n,row.children[1].innerText]})()")
    assert str(r[0]) == r[1]


def test_earth_margin_reduces_line_of_sight(browser, page_url):
    page, _ = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    a = page.evaluate("S.sites['14'].stat.earth")
    page.select_option("#margin", "5")
    assert page.evaluate("S.sites['14'].stat.earth") < a


def test_custom_coordinates_inside_and_outside_dem(browser, page_url):
    page, _ = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    page.fill("#c-lat", "-70")
    page.click("#c-add")
    assert "fuera" in page.inner_text("#warn-custom")
    page.fill("#c-lat", "-89.97832")
    page.fill("#c-lon", "18.0767")
    page.click("#c-add")
    page.wait_for_function("S.sites.c1 && S.sites.c1.heat", timeout=120000)
    # el DEM reducido debe quedar cerca del calculo con DEM completo en un punto conocido
    custom, full = page.evaluate("(()=>{prep(S.sites['14']);masks(S.sites['14']);return [S.sites.c1.stat.sun,S.sites['14'].stat.sun]})()")
    assert custom == pytest.approx(full, abs=2)


def test_language_toggle_keeps_all_sections(browser, page_url):
    page, errors = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    assert "Por qué un cambio" in page.inner_text("#why-sec")
    page.click("#lang")
    page.click("#lang")
    page.click("#lang")
    assert page.title() == "Lunar Site Navigator"
    assert "Why a small change" in page.inner_text("#why-sec")
    assert not errors


def test_site14_card_shows_warning_in_both_languages(browser, page_url):
    page, errors = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    assert "Frágil y sin confirmar a escala de píxel" in page.inner_text('.card:has(h3:text-is("Sitio 14")) [data-r="warn14"]')
    page.click("#lang")
    assert "Fragile and not confirmed at pixel scale" in page.inner_text('.card:has(h3:text-is("Site 14")) [data-r="warn14"]')
    assert page.locator('.card:has(h3:text-is("Site 456")) [data-r="warn14"]').count() == 0
    assert not errors


def test_default_order_recommendation_and_contrast(browser, page_url):
    page, errors = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    assert page.evaluate("S.sel.slice()") == ["456", "14", "1358"]
    assert page.locator(".card h3").all_inner_texts() == ["Sitio 456", "Sitio 14", "Sitio 1358"]
    assert [h.strip() for h in page.locator("#tbl thead th").all_inner_texts()][1:] == ["SITIO 456", "SITIO 14", "SITIO 1358"]
    assert page.locator(".badge.top").count() == 1
    assert "Mejor de los 10" in page.inner_text('.card:has(h3:text-is("Sitio 456")) .badge.top')
    assert "Contraste" in page.inner_text('.card:has(h3:text-is("Sitio 14")) .badge')
    assert page.locator(".chip").first.get_attribute("data-id") == "456"
    assert page.evaluate("[S.heatId, S.planSite]") == ["456", "456"]
    assert not errors


def test_criterion_is_visible_in_both_languages(browser, page_url):
    page, _ = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    es = page.inner_text("#eleccion")
    assert "Tierra de al menos 40 %" in es and "solo como desempate" in es and "33 a 58 %" in es
    page.click("#lang")
    en = page.inner_text("#eleccion")
    assert "Earth of at least 40 %" in en and "only as a tiebreaker" in en and "33 to 58 %" in en


def test_hero_and_video_captions_on_page_are_site456(browser, page_url):
    import re
    page, errors = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    for lang_step in (False, True):
        if lang_step:
            page.click("#lang")
        for sel in ("#cap-hero", "#cap-video"):
            t = page.inner_text(sel)
            assert re.search(r"\b456\b", t) and not re.search(r"\b14\b", t), t
        assert "456" in page.get_attribute("#hero", "alt")
    assert "Illustrative render" in page.inner_text("#hero-mark")
    assert page.evaluate("document.querySelector('#hero').naturalWidth") == 1600
    assert page.evaluate("new Promise(r=>{const v=document.querySelector('video');if(v.readyState>=1)r(v.videoWidth);else v.onloadedmetadata=()=>r(v.videoWidth);v.onerror=()=>r(-1);})") in (960, -1)
    assert not errors


def test_validation_section_shows_light_result_and_limits(browser, page_url):
    page, errors = opened(browser, page_url, viewport={"width": 1366, "height": 900}, locale="es-CR")
    want = {"es": ["0,737", "5 fechas de 2009", "solo Site04", "No valida la predicción de 2026 a 2045", "más puntos con luz", "por debajo de 0,5"],
            "en": ["0.737", "5 dates in 2009", "only Site04", "does not validate the 2026–2045 prediction", "more lit points", "below 0.5"]}
    es = page.text_content("#valid") + page.text_content("#limits")
    page.click("#lang")
    en = page.text_content("#valid") + page.text_content("#limits")
    for w in want["es"]:
        assert w in es, w
    for w in want["en"]:
        assert w in en, w
    assert "no validadas" not in es and "not validated" not in en
    assert not errors


# ---------- fase 2: dos fechas, reproducir, enlace, CSV y accesibilidad ----------
DESK = dict(viewport={"width": 1366, "height": 900}, locale="es-CR")


def set_date(page, sel, value):
    page.fill(sel, value)
    page.dispatch_event(sel, "change")


def ds_col(page, col):
    return page.eval_on_selector_all(f'#ds-tbl td[data-ds="{col}"]', "e=>e.map(x=>x.textContent)")


def test_same_site_two_dates_matches_the_card_and_changes_with_the_date(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    assert page.input_value("#ds-site") == "456"
    assert page.input_value("#ds-a") == "2030-06-21T11:00"
    a, b = ds_col(page, "a"), ds_col(page, "b")
    card = page.locator(".card").first
    assert a[1] == card.locator('[data-r="n1"]').inner_text() and a[2] == card.locator('[data-r="n5"]').inner_text()
    assert a[6] == card.locator('[data-r="n2"]').inner_text() and a[7] == card.locator('[data-r="n8"]').inner_text()
    assert a != b and len(a) == 13
    set_date(page, "#ds-b", "2030-06-21T11:00")
    assert ds_col(page, "a") == ds_col(page, "b")
    set_date(page, "#ds-b", "2099-01-01T00:00")
    assert page.input_value("#ds-b").startswith("2045-10-3")
    page.select_option("#ds-site", "14")
    assert "sin confirmar a escala de píxel" in page.inner_text("#ds-meta")
    page.click("#lang")
    assert "Same site, two dates" in page.inner_text("#t-dates")
    assert "not confirmed at pixel scale" in page.inner_text("#ds-meta")
    assert not errors


def test_date_window_percentages_match_an_independent_count(browser, page_url):
    page, _ = opened(browser, page_url, **DESK)
    want = page.evaluate("(()=>{const s=S.sites['456'],a=S.dsA;let n=0,e=0;for(let i=a;i<a+720;i++){n+=s.sv[i];e+=s.tv[i];}return [Math.round(100*n/720),Math.round(100*e/720)];})()")
    a = ds_col(page, "a")
    assert a[9] == f"{want[0]} %" and a[10] == f"{want[1]} %"


def test_play_advances_pauses_and_stops_at_the_end(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    idx = lambda: int(page.input_value("#slider"))
    start = idx()
    page.click("#play")
    assert page.get_attribute("#play", "aria-pressed") == "true"
    page.wait_for_function(f"+document.querySelector('#slider').value>={start + 18}", timeout=15000)
    page.click("#play")
    assert "Reproducir" in page.inner_text("#play")
    stopped = idx()
    assert (stopped - start) % 6 == 0
    page.wait_for_timeout(500)
    assert idx() == stopped
    page.click("#play")
    page.wait_for_function(f"+document.querySelector('#slider').value>{stopped}", timeout=15000)
    page.evaluate("(()=>{const s=document.querySelector('#slider');s.value=1000;s.dispatchEvent(new Event('input'));})()")
    assert page.get_attribute("#play", "aria-pressed") == "false"
    assert idx() == 1000
    last = int(page.get_attribute("#slider", "max"))
    page.evaluate(f"setIdx({last - 8})")
    page.click("#play")
    page.wait_for_function("document.querySelector('#play').getAttribute('aria-pressed')==='false'", timeout=15000)
    assert idx() == last
    assert not errors


def test_share_link_restores_the_scenario_and_ignores_bad_values(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    page.click('.chip[data-id="1358"]')
    page.click('.chip[data-id="964"]')
    page.select_option("#margin", "3")
    page.dispatch_event("#margin", "change")
    page.fill("#p-area", "2.5")
    page.fill("#p-eff", "20")
    page.select_option("#ds-site", "14")
    set_date(page, "#dt", "2031-03-04T05:00")
    set_date(page, "#ds-a", "2032-01-02T03:00")
    page.click("#share")
    page.wait_for_function("document.querySelector('#share-msg').textContent!==''")
    url = page.input_value("#share-url")
    assert "#s=456,14,964" in url and "t=2031-03-04T05" in url
    other, err2 = opened(browser, url, **DESK)
    other.wait_for_function("document.querySelector('#dt').value==='2031-03-04T05:00'")
    assert other.evaluate("S.sel") == ["456", "14", "964"]
    assert other.evaluate("[S.margin,S.area,S.eff,S.dsSite]") == [3, 2.5, 0.2, "14"]
    assert other.input_value("#ds-a") == "2032-01-02T03:00"
    assert other.locator(".card").count() == 3
    assert other.locator(".card").first.locator('[data-r="n1"]').inner_text() != ""
    base = url.split("#")[0]
    bad, err3 = opened(browser, base + "#s=nada,456&t=basura&m=9&a=-1&e=500&ds=nada&da=x", **DESK)
    assert bad.evaluate("S.sel") == ["456"]
    assert bad.evaluate("[S.margin,S.area,S.eff,S.dsSite]") == [0, 1, 0.3, "456"]
    assert not errors and not err2 and not err3


def test_share_link_restores_custom_coordinates(browser, page_url):
    page, errors = opened(browser, page_url.split("#")[0] + "#s=456,c:-85.5:40&t=2030-01-01T00", **DESK)
    page.wait_for_function("S.sel.length===2&&S.sel[1].startsWith('c')", timeout=60000)
    assert page.evaluate("[S.sites[S.sel[1]].lat,S.sites[S.sel[1]].lon]") == [-85.5, 40]
    page.wait_for_function("document.querySelector('#dt').value==='2030-01-01T00:00'")
    page.click("#share")
    page.wait_for_function("document.querySelector('#share-url').value!==''")
    assert "c:-85.5:40" in page.input_value("#share-url")
    assert not errors


def test_csv_export_has_expected_rows_and_matches_the_app(browser, page_url):
    import csv as _csv
    import io
    ctx = browser.new_context(accept_downloads=True, **DESK)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(page_url)
    page.wait_for_selector("#app:not([hidden])", timeout=60000)
    page.fill("#csv-days", "2")
    with page.expect_download() as d:
        page.click("#csv")
    assert d.value.suggested_filename == "lunar_site_navigator_20300621T11_2d.csv"
    text = open(d.value.path(), encoding="utf-8").read()
    head = [x for x in text.splitlines() if x.startswith("#")]
    assert "Model output, not measurements" in head[0] and "not a communications link" in head[2]
    assert "# 456: terrain 5 m + 80 m" in head
    rows = list(_csv.DictReader(io.StringIO("\n".join(x for x in text.splitlines() if not x.startswith("#")))))
    assert len(rows) == 3 * 2 * 24
    assert [r["site_id"] for r in rows[::48]] == ["456", "14", "1358"]
    r = rows[0]
    assert r["utc"] == "2030-06-21T11:00Z"
    card = page.locator(".card").first
    fmt = lambda v: ("+" if v >= 0 else "−") + f"{abs(v):.2f}°"
    assert fmt(float(r["sun_elevation_deg"])) == card.locator('[data-r="n1"]').inner_text()
    assert fmt(float(r["earth_margin_deg"])) == card.locator('[data-r="n8"]').inner_text()
    assert (r["sun_visible"] == "1") == (float(r["sun_margin_deg"]) > 0)
    assert (r["earth_line_of_sight"] == "1") == (float(r["earth_margin_deg"]) > 0)
    assert r["site_name"] == "Site 456"
    assert float(r["power_w"]) == pytest.approx(page.evaluate("S.sites['456'].pw[S.idx]*S.area*S.eff"), abs=0.01)
    page.evaluate(f"setIdx({page.evaluate('N')}-3)")
    with page.expect_download() as d2:
        page.click("#csv")
    n = [x for x in open(d2.value.path(), encoding="utf-8").read().splitlines() if not x.startswith("#")]
    assert len(n) == 1 + 3 * 3
    assert not errors


AXE = Path(__file__).parent / "fixtures" / "axe-4.10.2.min.js"


@pytest.mark.parametrize("scheme", ["light", "dark"])
@pytest.mark.parametrize("mobile", [False, True])
@pytest.mark.parametrize("english", [False, True])
def test_page_has_no_accessibility_violations(browser, page_url, scheme, mobile, english):
    kw = dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True) if mobile else dict(viewport={"width": 1366, "height": 900})
    page, errors = opened(browser, page_url, locale="es-CR", color_scheme=scheme, **kw)
    if english:
        page.click("#lang")
    page.click("#share")
    page.wait_for_function("document.querySelector('#share-msg').textContent!==''")
    page.add_script_tag(content=AXE.read_text(encoding="utf-8"))
    found = page.evaluate("axe.run(document,{runOnly:['wcag2a','wcag2aa']}).then(r=>r.violations.map(v=>[v.id,v.nodes.map(n=>n.target.join(' '))]))")
    assert found == []
    assert page.evaluate("document.documentElement.scrollWidth") <= page.evaluate("innerWidth")
    assert not errors


def test_new_controls_have_visible_labels_in_both_languages(browser, page_url):
    page, _ = opened(browser, page_url, **DESK)
    assert page.inner_text("#share") == "Copiar enlace" and page.inner_text("#csv") == "Exportar CSV"
    assert "salidas del modelo" in page.inner_text("#hint-csv")
    page.click("#lang")
    assert page.inner_text("#share") == "Copy link" and page.inner_text("#csv") == "Export CSV"
    assert "model outputs, not measurements" in page.inner_text("#hint-csv")


# ---------- fase 3: puntos de region ----------
def test_region_group_is_separate_and_warns_when_mixing_resolutions(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    assert "fuera del ranking" in page.inner_text("#chips") and "no es una selección de la NASA" in page.inner_text("#chips")
    assert page.inner_text("#warn-mix") == ""
    assert page.locator("#tbl td.best").count() > 0
    page.click('.chip[data-id="1358"]')
    page.click('.chip[data-id="rdgr2"]')
    assert "mezcla resoluciones" in page.inner_text("#warn-mix")
    assert page.locator("#tbl td.best").count() == 0
    card = page.locator(".card").nth(2)
    note = card.inner_text()
    assert "Wueller et al. 2026" in note and "No es una selección de la NASA" in note and "fuera del ranking" in note
    assert "15,9 %" in note and "56,5 %" in note and "sin causa demostrada" in note and "solo cubre Site04" in note
    assert "Artemis" not in note
    page.click("#lang")
    assert "mixes resolutions" in page.inner_text("#warn-mix")
    assert "not a NASA selection" in page.locator(".card").nth(2).inner_text()
    assert not errors


def test_region_without_coverage_says_it_is_not_validated(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    page.click('.chip[data-id="1358"]')
    page.click('.chip[data-id="rpcb"]')
    assert "no están validadas" in page.locator(".card").nth(2).inner_text()
    page.select_option("#ds-site", "rpcb")
    assert "no están validadas" in page.inner_text("#ds-meta")
    page.select_option("#h-site", "rpcb")
    assert page.inner_text("#h-note") != ""
    assert not errors


# ---------- fase 4: respuesta rapida y calendario ----------
def test_first_screen_answers_with_the_same_state_as_the_card(browser, page_url):
    page, errors = opened(browser, page_url, viewport={"width": 390, "height": 664}, is_mobile=True, has_touch=True, locale="es-CR")
    t = page.locator("#ans-text").bounding_box()
    assert t["y"] + t["height"] <= 664
    card = page.locator(".card").first
    assert page.inner_text("#ans-sv") == card.locator('[data-r="sv"]').inner_text()
    assert page.inner_text("#ans-sd") == card.locator('[data-r="sd"]').inner_text()
    assert page.inner_text("#ans-td") == card.locator('[data-r="td"]').inner_text()
    assert page.inner_text("#ans-text").startswith("Hay Sol para generar energía y línea de vista")
    assert "no certifica" in page.inner_text("#ans-note")
    assert not errors


def test_answer_text_follows_date_and_site_warning(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    for t in ("2030-07-06T11:00",):
        set_date(page, "#dt", t)
    assert page.inner_text("#ans-text").startswith("No hay Sol ni línea de vista")
    want = page.evaluate("(()=>fmt(nextBoth(S.sites['456'],S.idx)))()")
    assert want in page.inner_text("#ans-text")
    page.select_option("#ans-site", "14")
    assert "sin confirmar a escala de píxel" in page.inner_text("#ans-warn")
    page.select_option("#ans-site", "rpcb")
    assert "no están validadas" in page.inner_text("#ans-warn")
    page.click("#lang")
    assert "not validated" in page.inner_text("#ans-warn")
    assert not errors


def test_calendar_cell_matches_planner_and_independent_count(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    res = page.evaluate("""(()=>{const s=S.sites['456'],out=[];
      for(const [y,d,n] of [[2030,171,14],[2027,0,1],[2044,365,28],[2036,59,7]]){const a=calStart(y,d);let k=0;for(let i=a;i<a+n*24;i++)k+=(s.sv[i]&&s.tv[i])?1:0;const m=mission(s,a,n*24);out.push([calVal(s,a,n,0),100*k/(n*24),m.both,calVal(s,a,n,1),m.sun,calVal(s,a,n,2),m.los]);}return out;})()""")
    for row in res:
        assert row[0] == pytest.approx(row[1]) and row[0] == pytest.approx(row[2])
        assert row[3] == pytest.approx(row[4]) and row[5] == pytest.approx(row[6])
    assert "Llegada 2030-06-21, 14 días" in page.inner_text("#cal-read")
    assert not errors


def test_calendar_click_keys_margin_use_and_max_value(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    cv = page.locator("#cal-cv")
    cv.scroll_into_view_if_needed()
    b = cv.bounding_box()
    g = page.evaluate("document.querySelector('#cal-cv')._g")
    page.mouse.click(b["x"] + g["pl"] + g["w"] * 182.5 / 365, b["y"] + g["pt"] + g["h"] * 14.5 / 28)
    pick = page.evaluate("[S.cal.day,S.cal.len]")
    assert pick == [182, 14]
    assert "Llegada 2030-07-02, 14 días" in page.inner_text("#cal-read")
    cv.focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowUp")
    assert page.evaluate("[S.cal.day,S.cal.len]") == [183, 15]
    bv = page.evaluate("(()=>{const s=S.sites['456'];let b=-1,bd=0;for(let d=0;d<365;d++){const v=calVal(s,calStart(2030,d),15,0);if(v>b+1e-9){b=v;bd=d;}}return [fmt(calStart(2030,bd)).slice(0,10),Math.round(b)];})()")
    assert f"llegada {bv[0]}, {bv[1]} %" in page.inner_text("#cal-max")
    before = page.inner_text("#cal-read")
    page.select_option("#margin", "5")
    page.dispatch_event("#margin", "change")
    assert page.inner_text("#cal-read") != before
    page.click("#cal-use")
    assert page.input_value("#dt") == "2030-07-03T00:00"
    assert not errors


def test_calendar_warns_on_fragile_and_unvalidated_sites_and_never_says_best(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    page.select_option("#cal-site", "14")
    assert "sin confirmar a escala de píxel" in page.inner_text("#cal-warn")
    page.select_option("#cal-site", "rnr2")
    assert "no están validadas" in page.inner_text("#cal-warn") and "80 m + 120 m" in page.inner_text("#cal-meta")
    text = page.inner_text("#calendar").lower()
    assert "mejor" not in text and "recomend" not in text and "temperatura, polvo" in text
    page.click("#lang")
    text = page.inner_text("#calendar").lower()
    assert "best" not in text and "recommend" not in text and "temperature, dust" in text
    assert not errors


def test_share_link_keeps_answer_site_and_calendar(browser, page_url):
    page, errors = opened(browser, page_url, **DESK)
    page.select_option("#ans-site", "1358")
    page.select_option("#cal-site", "964")
    page.select_option("#cal-year", "2035")
    page.select_option("#cal-met", "1")
    page.click("#share")
    page.wait_for_function("document.querySelector('#share-url').value!==''")
    other, err = opened(browser, page.input_value("#share-url"), **DESK)
    other.wait_for_function("S.ansSite==='1358'")
    assert other.evaluate("[S.ansSite,S.calSite,S.cal.year,S.cal.met]") == ["1358", "964", 2035, 1]
    assert other.input_value("#cal-year") == "2035" and other.input_value("#cal-met") == "1"
    bad, err2 = opened(browser, page.input_value("#share-url").split("#")[0] + "#cy=1999&cm=7&cl=99&cd=-3&cs=nada", **DESK)
    assert bad.evaluate("[S.calSite,S.cal.year,S.cal.met,S.cal.day,S.cal.len]") == ["456", 2030, 0, 171, 14]
    assert not errors and not err and not err2
