"""Puntos de region: fuera del ranking, con fuente y sin presentarse como seleccion oficial."""
import csv
import json
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
REG = ROOT / "auditoria" / "regiones"
NAMES = ["Peak near Cabeus B", "Haworth", "Malapert Massif", "Mons Mouton Plateau", "Mons Mouton", "Nobile Rim 1", "Nobile Rim 2", "de Gerlache Rim 2", "Slater Plain"]
NO_COVER = {"rpcb", "rmmp", "rnr2"}


@pytest.fixture(scope="module")
def data():
    return json.loads((ROOT / "data" / "data.json").read_text(encoding="utf-8"))


def regs(data):
    return [s for s in data["sites"] if s["kind"] == "region"]


def test_nine_regions_with_published_sites_from_the_rule():
    rows = list(csv.DictReader(open(REG / "puntos_representativos.csv", encoding="utf-8")))
    assert [r["region"] for r in rows] == NAMES
    for r in rows:
        assert r["sitio_publicado"] and float(r["dist_centro_km"]) <= float(r["radio_grupo_km"])


def test_regions_stay_out_of_the_ranking_and_declare_terrain(data):
    rg = regs(data)
    assert len(rg) == 9
    for s in rg:
        assert "rank" not in s and s["res"] in ("80 m", "80 m + 120 m") and s["pub"] and s["spread"] > 0
        assert "representative point" in s["en"] and "punto representativo" in s["es"]


def test_original_sites_keep_their_ranking(data):
    assert sorted(s["rank"] for s in data["sites"] if s["kind"] == "cand") == list(range(1, 11))


def test_validation_is_stated_only_where_a_map_covers_the_point(data):
    for s in regs(data):
        if s["id"] in NO_COVER:
            assert s["val"] == {}
        else:
            assert "pgda_sol" in s["val"]
        assert ("lroc" in s["val"]) == (s["id"] == "rdgr2")
    d = next(s for s in regs(data) if s["id"] == "rdgr2")["val"]
    assert (d["lroc"], d["modelo_sol_2010"], d["pgda_sol"]) == (15.9, 56.5, 54.9)


@pytest.mark.parametrize("path", ["README.md", "src/app.js", "docs/entrega/descripcion_entrega_EN.md", "docs/entrega/guion_presentacion_3min.md", "auditoria/validacion/RESUMEN_VALIDACION.md"])
def test_regions_are_not_called_artemis_sites_or_official(path):
    text = (ROOT / path).read_text(encoding="utf-8")
    for bad in (r"(?i)artemis iii (landing )?sites?", r"(?i)sitios? (de )?artemis iii", r"(?i)official (nasa )?selection", r"(?i)selecci[oó]n oficial"):
        assert not re.search(bad, text), bad


def test_readme_table_matches_the_validation_file_and_declares_gaps():
    text = (ROOT / "README.md").read_text(encoding="utf-8")
    for r in csv.DictReader(open(REG / "validacion_regiones.csv", encoding="utf-8")):
        if r["pgda_sol"]:
            assert f"{r['pgda_sol']} / {r['pgda_tierra']} %" in text
    for phrase in ("not NASA selections", "No son selecciones de la NASA", "have no comparison at all", "no tienen ninguna comparación", "15.9 % against the model's 56.5 %", "15,9 % frente a 56,5 %", "Inferred names", "Nombres deducidos"):
        assert phrase in text


def test_description_declares_unranked_points():
    assert "stay unranked" in (ROOT / "docs/entrega/descripcion_entrega_EN.md").read_text(encoding="utf-8")
