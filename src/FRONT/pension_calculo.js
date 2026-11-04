// Calculo de la pension, sin DOM. Lo usa pension_colombia.html y los tests de Node.
// Si cambias una regla aqui, cambiala tambien en src/BACK/pension_colombia.py.
const SEMANAS_MIN_HOMBRE = 1300, EDAD_HOMBRE = 62, EDAD_MUJER = 57;
const TRANSICION_HOMBRE = 900, TRANSICION_MUJER = 750;
const SEMANAS_OPCION_VIDA = 1250, TOPE_PRIMA_MEDIA_SMMLV = 2.3, TOPE_MESADA_SMMLV = 25;

function semanasMinimas(sexo, año) {
  if (sexo === "hombre" || año < 2026) return SEMANAS_MIN_HOMBRE;
  return Math.max(1000, 1250 - 25 * (año - 2026));
}

function tasaReemplazo(ibl, semanas, base, smmlv, soloBloques) {
  const s = ibl / smmlv;
  const tasaBase = Math.min(65, Math.max(55, 65.5 - 0.5 * s));
  let bloques = Math.max(0, semanas - base) / 50;
  if (soloBloques) bloques = Math.trunc(bloques);
  return Math.min(80, tasaBase + 1.5 * bloques);
}

function leerMes(texto, nombre) {
  const m = /^(\d{4})-(\d{2})$/.exec((texto || "").trim());
  if (!m || +m[2] < 1 || +m[2] > 12) throw new Error(`Revisa la fecha de ${nombre}: usa el formato AAAA-MM.`);
  return [+m[1], +m[2]];
}

function expandirHistorial(historial, enPesosDeHoy, ipc, añoFinal) {
  const meses = new Map();
  for (const [desde, hasta, salario] of historial) {
    let [a, m] = leerMes(desde, "inicio del período");
    const [aFin, mFin] = leerMes(hasta, "fin del período");
    if (!(salario > 0)) throw new Error(`Escribe un salario mayor que cero para el período ${desde}.`);
    if (a * 12 + m > aFin * 12 + mFin) throw new Error(`El período ${desde} a ${hasta} está invertido.`);
    while (a * 12 + m <= aFin * 12 + mFin) {
      const clave = a * 12 + m;
      if (meses.has(clave)) throw new Error(`El mes ${a}-${String(m).padStart(2, "0")} está repetido en el historial.`);
      let valor = salario;
      if (!enPesosDeHoy) {
        if (!(a in ipc) || !(añoFinal in ipc)) throw new Error(`Falta el IPC de ${a} o de ${añoFinal}.`);
        valor = salario * ipc[añoFinal] / ipc[a];
      }
      meses.set(clave, valor);
      if (++m === 13) { a++; m = 1; }
    }
  }
  return [...meses.keys()].sort((x, y) => x - y).map(k => meses.get(k));
}

const promedio = v => v.length ? v.reduce((x, y) => x + y, 0) / v.length : 0;

function calcular(p) {
  const edad = p.sexo === "hombre" ? EDAD_HOMBRE : EDAD_MUJER;
  const añoEdad = p.añoNacimiento + edad;
  const año = p.añoPension ?? añoEdad;
  const minimo = semanasMinimas(p.sexo, año);
  const umbral = p.sexo === "hombre" ? TRANSICION_HOMBRE : TRANSICION_MUJER;
  const transicion = p.semanasCorte >= umbral;

  const salarios = expandirHistorial(p.historial, p.enPesosDeHoy, p.ipc, año);
  const ibl10 = promedio(salarios.slice(-120));
  const aplicaVida = p.semanasTotales >= SEMANAS_OPCION_VIDA;
  const iblVida = aplicaVida ? promedio(salarios) : 0;
  let ibl = Math.max(ibl10, iblVida);
  if (!transicion) ibl = Math.min(ibl, TOPE_PRIMA_MEDIA_SMMLV * p.smmlv);

  const mesadaPara = base => {
    const tasa = tasaReemplazo(ibl, p.semanasTotales, base, p.smmlv, p.soloBloques);
    return { tasa, mesada: Math.min(TOPE_MESADA_SMMLV * p.smmlv, Math.max(p.smmlv, ibl * tasa / 100)) };
  };

  let base = SEMANAS_MIN_HOMBRE, baseAlterna = null;
  if (p.sexo === "mujer") {
    if (p.mujerDesde === "minimo") { base = minimo; baseAlterna = SEMANAS_MIN_HOMBRE; }
    else baseAlterna = minimo;
  }
  const principal = mesadaPara(base);
  return {
    año, edad, añoEdad, minimo, umbral, transicion, ibl10, iblVida, aplicaVida, ibl,
    meses: salarios.length, tasa: principal.tasa, mesada: principal.mesada, baseAlterna,
    alterna: baseAlterna ? mesadaPara(baseAlterna) : null,
    cumpleEdad: año >= añoEdad, cumpleSemanas: p.semanasTotales >= minimo,
  };
}

const miles = n => String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g, ".");
const pesos = n => "$" + miles(n);
const pct = n => n.toFixed(2).replace(".", ",") + "%";

function construirAvisos(r, p) {
  const avisos = [];
  if (!r.cumpleEdad) avisos.push(`Aún no tendría la edad: cumple ${r.edad} años en ${r.añoEdad}.`);
  if (!r.cumpleSemanas) avisos.push(`No alcanza las ${miles(r.minimo)} semanas mínimas de ${r.año}. El resultado solo aplicaría si llega a completarlas.`);
  if (!r.transicion) avisos.push(`Con menos de ${r.umbral} semanas al corte queda fuera de la transición. El IBL se limitó a 2,3 salarios mínimos y falta sumar el ahorro individual, si lo tiene. Esta parte es ilustrativa porque aún falta reglamentación.`);
  if (r.alterna) avisos.push(`Contando adicionales desde ${miles(r.baseAlterna)} semanas: tasa ${pct(r.alterna.tasa)}, mesada ${pesos(r.alterna.mesada)}.`);
  const equivalentes = p.semanasTotales * 7 / 30;
  if (r.meses < equivalentes * 0.9) avisos.push(`El historial tiene ${r.meses} meses, pero las semanas equivalen a unos ${Math.round(equivalentes)}. Completa el historial si puedes.`);
  return avisos;
}

if (typeof module !== "undefined") {
  module.exports = {
    SEMANAS_MIN_HOMBRE, EDAD_HOMBRE, EDAD_MUJER, TRANSICION_HOMBRE, TRANSICION_MUJER,
    SEMANAS_OPCION_VIDA, TOPE_PRIMA_MEDIA_SMMLV, TOPE_MESADA_SMMLV,
    semanasMinimas, tasaReemplazo, leerMes, expandirHistorial, promedio, calcular,
    miles, pesos, pct, construirAvisos,
  };
}
