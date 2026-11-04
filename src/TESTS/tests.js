// Tests del calculo de la pagina web (src/FRONT/pension_calculo.js).
//
// Ejecutar desde la raiz del repo (Node 18 o superior, sin dependencias):
//     node --test src/TESTS/tests.js

const { test, describe } = require("node:test");
const assert = require("node:assert/strict");
const path = require("node:path");
const fs = require("node:fs");

const pc = require(path.join(__dirname, "..", "FRONT", "pension_calculo.js"));

const SMMLV = 1_000_000;
const cerca = (real, esperado, msg) =>
  assert.ok(Math.abs(real - esperado) < 1e-6, `${msg ?? ""} esperado ${esperado}, obtuvo ${real}`);

function parametros(extra = {}) {
  return {
    sexo: "hombre", añoNacimiento: 1966, semanasTotales: 1500, semanasCorte: 1250,
    añoPension: null, historial: [["2000-01", "2009-12", 7 * SMMLV]],
    enPesosDeHoy: true, ipc: {}, smmlv: SMMLV, mujerDesde: "1300", soloBloques: true,
    ...extra,
  };
}

describe("semanasMinimas", () => {
  test("hombre siempre 1300", () => {
    for (const año of [2020, 2026, 2036, 2050]) assert.equal(pc.semanasMinimas("hombre", año), 1300);
  });
  test("mujer antes de 2026 es 1300", () => assert.equal(pc.semanasMinimas("mujer", 2025), 1300));
  test("mujer baja 25 por año desde 2026", () => {
    assert.equal(pc.semanasMinimas("mujer", 2026), 1250);
    assert.equal(pc.semanasMinimas("mujer", 2030), 1150);
  });
  test("mujer no baja de 1000", () => {
    assert.equal(pc.semanasMinimas("mujer", 2036), 1000);
    assert.equal(pc.semanasMinimas("mujer", 2045), 1000);
  });
});

describe("tasaReemplazo", () => {
  const tasa = (ibl, semanas = 1300, soloBloques = true) =>
    pc.tasaReemplazo(ibl * SMMLV, semanas, 1300, SMMLV, soloBloques);

  test("tasa base segun IBL", () => cerca(tasa(10), 60.5));
  test("tasa base maximo 65", () => cerca(tasa(1), 65));
  test("tasa base minimo 55", () => cerca(tasa(30), 55));
  test("suma 1,5 por bloque de 50 semanas", () => cerca(tasa(10, 1400), 63.5));
  test("solo bloques completos", () => cerca(tasa(10, 1375), 62));
  test("con fraccion de bloque", () => cerca(tasa(10, 1375, false), 62.75));
  test("menos semanas que la base no resta", () => cerca(tasa(10, 1200), 60.5));
  test("tope 80", () => cerca(tasa(1, 2500), 80));
});

describe("leerMes", () => {
  test("lee AAAA-MM", () => assert.deepEqual(pc.leerMes("2020-07", "x"), [2020, 7]));
  test("ignora espacios", () => assert.deepEqual(pc.leerMes(" 2020-07 ", "x"), [2020, 7]));
  for (const malo of ["2020-00", "2020-13", "2020-7", "20-07", "", undefined, "2020/07"]) {
    test(`rechaza ${JSON.stringify(malo)}`, () => assert.throws(() => pc.leerMes(malo, "x")));
  }
});

describe("expandirHistorial", () => {
  test("expande meses cruzando año", () => {
    assert.deepEqual(pc.expandirHistorial([["2020-11", "2021-02", 100]], true, {}, 2026), [100, 100, 100, 100]);
  });
  test("ordena cronologicamente", () => {
    const h = [["2022-01", "2022-01", 2], ["2021-01", "2021-01", 1]];
    assert.deepEqual(pc.expandirHistorial(h, true, {}, 2026), [1, 2]);
  });
  test("periodo invertido falla", () => {
    assert.throws(() => pc.expandirHistorial([["2021-05", "2021-01", 100]], true, {}, 2026), /invertido/);
  });
  test("meses repetidos fallan", () => {
    const h = [["2020-01", "2020-06", 100], ["2020-06", "2020-12", 100]];
    assert.throws(() => pc.expandirHistorial(h, true, {}, 2026), /repetido/);
  });
  test("salario cero o vacio falla", () => {
    assert.throws(() => pc.expandirHistorial([["2020-01", "2020-01", 0]], true, {}, 2026), /salario/);
    assert.throws(() => pc.expandirHistorial([["2020-01", "2020-01", NaN]], true, {}, 2026), /salario/);
  });
  test("actualiza con IPC", () => {
    const r = pc.expandirHistorial([["2020-01", "2020-01", 1000]], false, { 2020: 100, 2026: 150 }, 2026);
    cerca(r[0], 1500);
  });
  test("falta IPC falla", () => {
    assert.throws(() => pc.expandirHistorial([["2020-01", "2020-01", 1000]], false, { 2020: 100 }, 2026), /IPC/);
  });
});

describe("formato", () => {
  test("pesos con punto de miles", () => assert.equal(pc.pesos(4760000), "$4.760.000"));
  test("pesos redondea", () => assert.equal(pc.pesos(1617.6), "$1.618"));
  test("porcentaje con coma", () => assert.equal(pc.pct(70.35), "70,35%"));
});

describe("construirAvisos", () => {
  const avisos = extra => {
    const p = parametros(extra);
    return pc.construirAvisos(pc.calcular(p), p);
  };

  test("sin avisos en un caso completo", () => {
    // 1500 semanas equivalen a 350 meses, asi que el historial debe tenerlos.
    assert.deepEqual(avisos({ historial: [["1995-01", "2024-12", 7 * SMMLV]] }), []);
  });
  test("avisa si aun no tiene la edad", () => {
    assert.ok(avisos({ añoPension: 2025 }).some(a => a.includes("Aún no tendría la edad")));
  });
  test("avisa si queda fuera de transicion", () => {
    assert.ok(avisos({ semanasCorte: 800 }).some(a => a.includes("fuera de la transición")));
  });
  test("avisa si el historial es corto", () => {
    assert.ok(avisos().some(a => a.includes("El historial tiene 120 meses")));
  });
  test("mujer muestra la opcion alterna", () => {
    const a = avisos({ sexo: "mujer", añoNacimiento: 1970 });
    assert.ok(a.some(t => t.includes("desde 1.225 semanas: tasa 69,50%, mesada $4.865.000")));
  });
});

// ---------------------------------------------------------------------------
// Casos compartidos con Python: si fallan aqui pero no en tests.py (o al
// reves), los dos calculos dejaron de coincidir.
// ---------------------------------------------------------------------------

const { casos } = JSON.parse(fs.readFileSync(path.join(__dirname, "casos_compartidos.json"), "utf8"));

const aCamel = {
  año_edad: "añoEdad", ibl_10: "ibl10", ibl_vida: "iblVida", aplica_vida: "aplicaVida",
  base_alterna: "baseAlterna", cumple_edad: "cumpleEdad", cumple_semanas: "cumpleSemanas",
};

function desdeCaso(e) {
  return parametros({
    sexo: e.sexo, añoNacimiento: e.año_nacimiento, semanasTotales: e.semanas_totales,
    semanasCorte: e.semanas_corte, historial: e.historial, smmlv: e.smmlv,
    añoPension: e.año_pension ?? null, enPesosDeHoy: e.en_pesos_de_hoy ?? true,
    ipc: e.ipc ?? {}, mujerDesde: e.mujer_desde ?? "1300",
  });
}

describe("casos compartidos", () => {
  for (const caso of casos) {
    test(caso.nombre, () => {
      const r = pc.calcular(desdeCaso(caso.entrada));
      for (const [clave, esperado] of Object.entries(caso.esperado)) {
        const real = r[aCamel[clave] ?? clave];
        if (esperado === null) assert.equal(real, null, clave);
        else if (typeof esperado === "number") cerca(real, esperado, clave);
        else if (typeof esperado === "object") {
          cerca(real.tasa, esperado.tasa, `${clave}.tasa`);
          cerca(real.mesada, esperado.mesada, `${clave}.mesada`);
        } else assert.equal(real, esperado, clave);
      }
    });
  }
});
