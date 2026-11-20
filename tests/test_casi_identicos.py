"""Tests del filtro del experimento de pares casi idénticos (experimentos/casi_identicos/lista.py)."""

import importlib.util
from pathlib import Path

import pandas as pd

RUTA = Path(__file__).resolve().parents[1] / "experimentos" / "casi_identicos" / "lista.py"
_spec = importlib.util.spec_from_file_location("lista_casi_identicos", RUTA)
lista = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lista)


def par(a, b, **kw):
    base = dict(appid_a=a, appid_b=b, mismo_dev=0.0, dev_sim=0.2, tfidf_cos=0.1, emb_cos=0.1, phash_sim=0.5,
                titulo_sim=0.2, largo_a=500, largo_b=500, resenas_a=10, resenas_b=10)
    base.update(kw)
    return base


def test_filtra_mismo_estudio_textos_cortos_y_pares_sin_material_igual():
    p = pd.DataFrame([
        par(1, 2, phash_sim=0.95),                          # imagen igual: entra
        par(3, 4, tfidf_cos=0.95, emb_cos=0.95),            # texto igual: entra
        par(5, 6, phash_sim=0.95, mismo_dev=1.0),           # mismo estudio: fuera
        par(7, 8, phash_sim=0.95, dev_sim=0.9),             # estudios de nombre casi igual: fuera
        par(9, 10, tfidf_cos=0.95, emb_cos=0.95, largo_a=100),   # descripción corta: fuera
        par(11, 12),                                        # nada casi idéntico: fuera
    ])
    d = lista.filtrar(p)
    assert sorted(map(tuple, d[["appid_a", "appid_b"]].to_numpy())) == [(1, 2), (3, 4)]


def test_agrupa_por_titulo_y_pone_primero_lo_mas_fuerte():
    p = pd.DataFrame([
        par(1, 2, phash_sim=0.95, titulo_sim=0.9),                              # misma obra
        par(3, 4, phash_sim=0.95, titulo_sim=0.7),                              # serie
        par(5, 6, tfidf_cos=0.95, emb_cos=0.95),                                # mirar: solo texto
        par(7, 8, phash_sim=0.95, tfidf_cos=0.95, emb_cos=0.95),                # mirar: texto e imagen
    ])
    d = lista.filtrar(p)
    assert list(d.grupo) == [lista.MIRAR, lista.MIRAR, lista.SERIE, lista.MISMA_OBRA]
    assert (d.appid_a.iloc[0], d.appid_a.iloc[1]) == (7, 5)
    assert "misma imagen y el mismo texto" in lista.motivo(lista.MIRAR, True, True)


def test_cada_juego_aparece_en_dos_pares_como_maximo():
    p = pd.DataFrame([par(1, b, phash_sim=0.95) for b in range(2, 7)])
    d = lista.filtrar(p)
    assert len(d) == lista.MAX_POR_JUEGO
