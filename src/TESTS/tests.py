"""
Tests del estimador de pension (src/BACK/pension_colombia.py).

Ejecutar desde la raiz del repo:
    python3 -m unittest discover -s src/TESTS -p "tests.py" -v

Para los calculos se usa un salario minimo de 1.000.000 para que los
valores esperados se puedan verificar a mano.
"""

import json
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "BACK"))

import pension_colombia as pc  # noqa: E402

SMMLV = 1_000_000


def historial_constante(salario, meses, desde_año=2000):
    """Un periodo continuo de `meses` meses con el mismo salario."""
    fin = desde_año * 12 + (meses - 1)
    return [(f"{desde_año}-01", f"{fin // 12}-{fin % 12 + 1:02d}", salario)]


class TestSemanasMinimas(unittest.TestCase):
    def test_hombre_siempre_1300(self):
        for año in (2020, 2026, 2036, 2050):
            self.assertEqual(pc.semanas_minimas("hombre", año), 1300)

    def test_mujer_antes_de_2026_es_1300(self):
        self.assertEqual(pc.semanas_minimas("mujer", 2025), 1300)

    def test_mujer_baja_25_por_año_desde_2026(self):
        self.assertEqual(pc.semanas_minimas("mujer", 2026), 1250)
        self.assertEqual(pc.semanas_minimas("mujer", 2030), 1150)

    def test_mujer_no_baja_de_1000(self):
        self.assertEqual(pc.semanas_minimas("mujer", 2036), 1000)
        self.assertEqual(pc.semanas_minimas("mujer", 2045), 1000)


class TestTasaReemplazo(unittest.TestCase):
    def tasa(self, ibl_en_smmlv, semanas=1300, base=1300, solo_bloques=True):
        return pc.tasa_reemplazo(ibl_en_smmlv * SMMLV, semanas, base, SMMLV, solo_bloques)

    def test_tasa_base_segun_ibl(self):
        self.assertAlmostEqual(self.tasa(10), 60.5)   # 65,5 - 0,5 * 10

    def test_tasa_base_maximo_65(self):
        self.assertAlmostEqual(self.tasa(1), 65.0)

    def test_tasa_base_minimo_55(self):
        self.assertAlmostEqual(self.tasa(30), 55.0)

    def test_suma_1_5_por_bloque_de_50_semanas(self):
        self.assertAlmostEqual(self.tasa(10, semanas=1400), 63.5)

    def test_solo_bloques_completos(self):
        self.assertAlmostEqual(self.tasa(10, semanas=1375), 62.0)

    def test_con_fraccion_de_bloque(self):
        self.assertAlmostEqual(self.tasa(10, semanas=1375, solo_bloques=False), 62.75)

    def test_menos_semanas_que_la_base_no_resta(self):
        self.assertAlmostEqual(self.tasa(10, semanas=1200), 60.5)

    def test_tope_80(self):
        self.assertAlmostEqual(self.tasa(1, semanas=2500), 80.0)


class TestExpandirHistorial(unittest.TestCase):
    def test_expande_meses_cruzando_año(self):
        meses = pc.expandir_historial([("2020-11", "2021-02", 100)], True, {}, 2026)
        self.assertEqual(
            [(a, m) for a, m, _ in meses],
            [(2020, 11), (2020, 12), (2021, 1), (2021, 2)],
        )

    def test_ordena_cronologicamente(self):
        historial = [("2022-01", "2022-01", 2), ("2021-01", "2021-01", 1)]
        meses = pc.expandir_historial(historial, True, {}, 2026)
        self.assertEqual([s for _, _, s in meses], [1, 2])

    def test_periodo_invertido_falla(self):
        with self.assertRaises(ValueError):
            pc.expandir_historial([("2021-05", "2021-01", 100)], True, {}, 2026)

    def test_meses_repetidos_fallan(self):
        historial = [("2020-01", "2020-06", 100), ("2020-06", "2020-12", 100)]
        with self.assertRaises(ValueError):
            pc.expandir_historial(historial, True, {}, 2026)

    def test_mes_cero_falla(self):
        with self.assertRaises(ValueError):
            pc.expandir_historial([("2020-00", "2020-02", 100)], True, {}, 2026)

    def test_mes_13_falla_en_vez_de_quedarse_en_bucle(self):
        with self.assertRaises(ValueError):
            pc.expandir_historial([("2020-13", "2021-02", 100)], True, {}, 2026)
        with self.assertRaises(ValueError):
            pc.expandir_historial([("2020-01", "2020-13", 100)], True, {}, 2026)

    def test_actualiza_con_ipc(self):
        ipc = {2020: 100.0, 2026: 150.0}
        meses = pc.expandir_historial([("2020-01", "2020-01", 1000)], False, ipc, 2026)
        self.assertAlmostEqual(meses[0][2], 1500.0)

    def test_falta_ipc_falla(self):
        with self.assertRaises(ValueError):
            pc.expandir_historial([("2020-01", "2020-01", 1000)], False, {2020: 100.0}, 2026)


class TestCalcular(unittest.TestCase):
    def calcular(self, **kw):
        datos = dict(
            sexo="hombre", año_nacimiento=1966, semanas_totales=1500,
            semanas_corte=1250, historial=historial_constante(7 * SMMLV, 120),
            smmlv=SMMLV,
        )
        datos.update(kw)
        return pc.calcular(**datos)

    def test_sexo_invalido_falla(self):
        with self.assertRaises(ValueError):
            self.calcular(sexo="otro")

    def test_año_de_pension_por_defecto_es_cuando_cumple_la_edad(self):
        r = self.calcular()
        self.assertEqual(r["año"], 2028)
        self.assertTrue(r["cumple_edad"])

    def test_caso_hombre_en_transicion(self):
        # IBL 7 SMMLV -> base 62%, +4 bloques (1500-1300) -> 68%
        r = self.calcular()
        self.assertTrue(r["transicion"])
        self.assertAlmostEqual(r["ibl"], 7 * SMMLV)
        self.assertAlmostEqual(r["tasa"], 68.0)
        self.assertAlmostEqual(r["mesada"], 4_760_000)
        self.assertIsNone(r["alterna"])

    def test_ibl_usa_el_promedio_mayor(self):
        historial = [("1990-01", "1999-12", 9 * SMMLV), ("2000-01", "2009-12", 3 * SMMLV)]
        r = self.calcular(historial=historial)
        self.assertAlmostEqual(r["ibl_10"], 3 * SMMLV)
        self.assertAlmostEqual(r["ibl_vida"], 6 * SMMLV)
        self.assertAlmostEqual(r["ibl"], 6 * SMMLV)

    def test_toda_la_vida_no_aplica_con_menos_de_1250_semanas(self):
        r = self.calcular(semanas_totales=1200)
        self.assertFalse(r["aplica_vida"])
        self.assertEqual(r["ibl_vida"], 0.0)

    def test_fuera_de_transicion_limita_ibl_a_2_3_smmlv(self):
        r = self.calcular(semanas_corte=800)
        self.assertFalse(r["transicion"])
        self.assertAlmostEqual(r["ibl"], 2.3 * SMMLV)

    def test_mesada_minima_un_smmlv(self):
        r = self.calcular(historial=historial_constante(0.5 * SMMLV, 120))
        self.assertAlmostEqual(r["mesada"], SMMLV)

    def test_mesada_maxima_25_smmlv(self):
        r = self.calcular(historial=historial_constante(50 * SMMLV, 120))
        self.assertAlmostEqual(r["mesada"], 25 * SMMLV)

    def test_mujer_muestra_resultado_alterno_desde_el_minimo(self):
        # Mujer 1970 -> 2027, minimo 1225. Desde 1300: 4 bloques; desde 1225: 5.
        r = self.calcular(sexo="mujer", año_nacimiento=1970)
        self.assertEqual(r["minimo"], 1225)
        self.assertAlmostEqual(r["tasa"], 68.0)
        self.assertEqual(r["base_alterna"], 1225)
        self.assertAlmostEqual(r["alterna"][0], 69.5)


class TestCasosCompartidos(unittest.TestCase):
    """Los mismos casos que corre tests.js. Si fallan en un lado y no en el
    otro, Python y la pagina web dejaron de calcular igual."""

    def test_casos(self):
        ruta = os.path.join(os.path.dirname(__file__), "casos_compartidos.json")
        with open(ruta, encoding="utf-8") as f:
            casos = json.load(f)["casos"]
        for caso in casos:
            with self.subTest(caso["nombre"]):
                e = caso["entrada"]
                r = pc.calcular(
                    e["sexo"], e["año_nacimiento"], e["semanas_totales"], e["semanas_corte"],
                    [tuple(p) for p in e["historial"]], e.get("año_pension"),
                    e.get("en_pesos_de_hoy", True),
                    {int(k): v for k, v in e.get("ipc", {}).items()},
                    e["smmlv"], e.get("mujer_desde", "1300"),
                )
                for clave, esperado in caso["esperado"].items():
                    real = r[clave]
                    if esperado is None:
                        self.assertIsNone(real, clave)
                    elif isinstance(esperado, dict):
                        self.assertAlmostEqual(real[0], esperado["tasa"], msg=clave)
                        self.assertAlmostEqual(real[1], esperado["mesada"], places=4, msg=clave)
                    elif isinstance(esperado, bool):
                        self.assertIs(real, esperado, clave)
                    else:
                        self.assertAlmostEqual(real, esperado, places=4, msg=clave)


if __name__ == "__main__":
    unittest.main()
