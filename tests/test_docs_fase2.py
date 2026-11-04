"""El README declara las funciones nuevas y lo que sigue truncado."""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
README = (ROOT / "README.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("text", [
    "Same site on two dates", "Mismo sitio en dos fechas", "Play button", "Botón de reproducir", "hourly CSV export of model outputs", "exportación CSV por hora de las salidas del modelo",
    "Window calendar", "Calendario de ventanas", "leaves out temperature, dust and landing risks", "no incluye temperatura, polvo ni riesgos de aterrizaje",
    "horizon of a custom site is still truncated outward", "horizonte de un sitio propio sigue truncado hacia afuera", "not a new validation of IM-2", "No es una validación nueva de IM-2",
])
def test_readme_states_scope_and_limits(text):
    assert text in README


def test_readme_no_longer_says_all_sites_are_truncated_at_the_dem_edge():
    assert "Within 200 km of the DEM edge the horizon is truncated." not in README


def test_axe_tool_is_declared_and_not_embedded_in_the_app():
    assert "axe-core 4.10.2" in (ROOT / "docs" / "SOURCES.md").read_text(encoding="utf-8")
    assert "__AXE__" not in (ROOT / "src" / "template.html").read_text(encoding="utf-8")


def test_demo_video_is_documented_and_the_old_one_is_kept():
    g = (ROOT / "docs" / "entrega" / "guion_demo_30s.md").read_text(encoding="utf-8")
    assert "renders/demo_30s_v2_lunar_site_navigator.mp4" in g and "earlier version, kept as a backup" in g
    assert (ROOT / "renders" / "demo_30s_v2_lunar_site_navigator.mp4").exists() and (ROOT / "renders" / "demo_30s_lunar_site_navigator.mp4").exists()
    words = sum(len(l.split("|")[3].split()) for l in g.splitlines() if l.startswith("| 0:"))
    assert words == 91


def test_three_minute_script_fits_at_150_words_per_minute():
    import re
    t = (ROOT / "docs" / "entrega" / "guion_presentacion_3min.md").read_text(encoding="utf-8").split("## Las 3 preguntas")[0]
    assert len(re.sub(r"\*\[.*?\]\*|^#.*$|\*\*Borrador\.\*\*", "", t, flags=re.M).split()) <= 450
