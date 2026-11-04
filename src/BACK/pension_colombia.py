"""
Estimador de pension de vejez en Colpensiones (Colombia).
Da un valor aproximado, no el valor oficial que reconoceria Colpensiones.

Uso: cambia las variables de la seccion "DATOS" y ejecuta:
    python3 pension_colombia.py

Los datos que trae son un EJEMPLO inventado. Reemplazalos por los reales.
"""

# ======================================================================
# DATOS DE LA PERSONA
# ======================================================================

SEXO = "hombre"                  # "hombre" o "mujer"
AÑO_NACIMIENTO = 1966

# Semanas totales que tendra al momento de pensionarse.
SEMANAS_TOTALES = 1500

# Semanas que tendra al 1 de abril de 2027. Definen el regimen de transicion.
SEMANAS_AL_1_ABRIL_2027 = 1250

# Año en que se pensionaria. Con None usa el año en que cumple la edad.
AÑO_PENSION = None

# Historial de cotizacion: (desde "AAAA-MM", hasta "AAAA-MM", salario mensual).
# Los periodos no se pueden cruzar. Deja por fuera los meses sin cotizar.
HISTORIAL = [
    ("1995-01", "2004-12", 3_000_000),
    ("2005-01", "2014-12", 5_000_000),
    ("2015-01", "2024-12", 7_000_000),
]

# True:  los salarios de HISTORIAL ya estan en pesos de hoy (estimacion rapida).
# False: son los salarios de cada epoca y se actualizan con IPC_INDICE.
SALARIOS_EN_PESOS_DE_HOY = True

# Indice de precios del DANE por año. Solo se usa si la variable anterior es
# False, y debe incluir cada año del historial y el año de pension.
# Ejemplo de formato: {2015: 100.0, 2016: 105.0}
IPC_INDICE = {}

# ======================================================================
# PARAMETROS LEGALES (revisalos cada año)
# ======================================================================

SALARIO_MINIMO = 1_750_905       # Salario minimo mensual de 2026

SEMANAS_MIN_HOMBRE = 1300
EDAD_HOMBRE = 62
EDAD_MUJER = 57
TRANSICION_HOMBRE = 900
TRANSICION_MUJER = 750
SEMANAS_PARA_OPCION_TODA_LA_VIDA = 1250
TOPE_PRIMA_MEDIA_SMMLV = 2.3     # Solo para quien no queda en transicion
TOPE_MESADA_SMMLV = 25

# Criterios en los que las fuentes o los fallos no coinciden:
#
# Mujeres: desde donde se cuentan las semanas adicionales.
#   "1300"   = desde 1.300 semanas (resultado mas conservador).
#   "minimo" = desde el minimo reducido de su año de pension.
# El programa muestra tambien el resultado de la otra opcion.
MUJER_ADICIONALES_DESDE = "1300"

# True:  solo suman bloques completos de 50 semanas.
# False: tambien suma la fraccion de un bloque.
SOLO_BLOQUES_COMPLETOS = True


# ======================================================================
# CALCULO
# ======================================================================

def semanas_minimas(sexo, año):
    """Semanas exigidas. Para mujeres bajan desde 2026 hasta 1.000 en 2036."""
    if sexo == "hombre" or año < 2026:
        return SEMANAS_MIN_HOMBRE
    return max(1000, 1250 - 25 * (año - 2026))


def tasa_reemplazo(ibl, semanas, semanas_base, smmlv=None, solo_bloques=None):
    """Porcentaje del IBL: base r = 65,5 - 0,5s, mas 1,5 por cada 50 semanas."""
    smmlv = SALARIO_MINIMO if smmlv is None else smmlv
    solo_bloques = SOLO_BLOQUES_COMPLETOS if solo_bloques is None else solo_bloques

    s = ibl / smmlv
    base = min(65.0, max(55.0, 65.5 - 0.5 * s))
    bloques = max(0, semanas - semanas_base) / 50
    if solo_bloques:
        bloques = int(bloques)
    return min(80.0, base + 1.5 * bloques)


def leer_mes(texto):
    """Convierte "AAAA-MM" en (año, mes). Falla si el mes no esta entre 1 y 12."""
    año, mes = map(int, texto.split("-"))
    if not 1 <= mes <= 12:
        raise ValueError(f"Mes invalido en HISTORIAL: {texto}")
    return año, mes


def expandir_historial(historial, en_pesos_de_hoy, ipc, año_final):
    """Devuelve [(año, mes, salario actualizado)] en orden cronologico."""
    meses = {}
    for desde, hasta, salario in historial:
        año, mes = leer_mes(desde)
        año_fin, mes_fin = leer_mes(hasta)
        if (año, mes) > (año_fin, mes_fin):
            raise ValueError(f"Periodo invertido: {desde} a {hasta}")
        while (año, mes) <= (año_fin, mes_fin):
            if (año, mes) in meses:
                raise ValueError(f"El mes {año}-{mes:02d} esta repetido en HISTORIAL")
            valor = salario
            if not en_pesos_de_hoy:
                if año not in ipc or año_final not in ipc:
                    raise ValueError(f"Falta IPC_INDICE para {año} o {año_final}")
                valor = salario * ipc[año_final] / ipc[año]
            meses[(año, mes)] = valor
            mes += 1
            if mes == 13:
                año, mes = año + 1, 1
    return [(a, m, meses[(a, m)]) for a, m in sorted(meses)]


def promedio(valores):
    return sum(valores) / len(valores) if valores else 0.0


def calcular(sexo, año_nacimiento, semanas_totales, semanas_corte, historial,
             año_pension=None, en_pesos_de_hoy=True, ipc=None, smmlv=None,
             mujer_desde="1300"):
    if sexo not in ("hombre", "mujer"):
        raise ValueError('SEXO debe ser "hombre" o "mujer"')
    smmlv = SALARIO_MINIMO if smmlv is None else smmlv

    edad = EDAD_HOMBRE if sexo == "hombre" else EDAD_MUJER
    año_edad = año_nacimiento + edad
    año = año_pension if año_pension is not None else año_edad
    minimo = semanas_minimas(sexo, año)

    umbral = TRANSICION_HOMBRE if sexo == "hombre" else TRANSICION_MUJER
    transicion = semanas_corte >= umbral

    meses = expandir_historial(historial, en_pesos_de_hoy, ipc or {}, año)
    salarios = [m[2] for m in meses]
    ibl_10 = promedio(salarios[-120:])
    aplica_vida = semanas_totales >= SEMANAS_PARA_OPCION_TODA_LA_VIDA
    ibl_vida = promedio(salarios) if aplica_vida else 0.0
    ibl = max(ibl_10, ibl_vida)

    if not transicion:
        ibl = min(ibl, TOPE_PRIMA_MEDIA_SMMLV * smmlv)

    def mesada_para(semanas_base):
        tasa = tasa_reemplazo(ibl, semanas_totales, semanas_base, smmlv)
        valor = min(TOPE_MESADA_SMMLV * smmlv, max(smmlv, ibl * tasa / 100))
        return tasa, valor

    if sexo == "hombre":
        base, base_alterna = SEMANAS_MIN_HOMBRE, None
    elif mujer_desde == "minimo":
        base, base_alterna = minimo, SEMANAS_MIN_HOMBRE
    else:
        base, base_alterna = SEMANAS_MIN_HOMBRE, minimo

    tasa, mesada = mesada_para(base)
    alterna = mesada_para(base_alterna) if base_alterna else None

    return {
        "año": año, "edad": edad, "año_edad": año_edad, "minimo": minimo,
        "cumple_edad": año >= año_edad,
        "cumple_semanas": semanas_totales >= minimo,
        "transicion": transicion, "umbral": umbral,
        "meses": len(meses), "ibl_10": ibl_10, "ibl_vida": ibl_vida,
        "aplica_vida": aplica_vida, "ibl": ibl, "tasa": tasa, "mesada": mesada,
        "alterna": alterna, "base_alterna": base_alterna,
    }


def pesos(valor):
    return "$" + f"{valor:,.0f}".replace(",", ".")


def imprimir(r, semanas):
    print("ESTIMACION DE PENSION EN COLPENSIONES")
    print("-" * 44)
    print(f"Año de pension:          {r['año']}")
    print(f"Semanas:                  {semanas:,} (minimo {r['minimo']:,})".replace(",", "."))
    print(f"Regimen de transicion:    {'Si' if r['transicion'] else 'No'}")
    print(f"IBL ultimos 10 años:     {pesos(r['ibl_10'])}")
    if r["aplica_vida"]:
        print(f"IBL toda la vida:         {pesos(r['ibl_vida'])}")
    else:
        print("IBL toda la vida:         no aplica, faltan semanas")
    print(f"IBL usado:                {pesos(r['ibl'])}")
    print(f"Tasa de reemplazo:        {r['tasa']:.2f}%")
    print(f"MESADA ESTIMADA:          {pesos(r['mesada'])}")

    avisos = []
    if not r["cumple_edad"]:
        avisos.append(f"Aun no tendria la edad: cumple {r['edad']} en {r['año_edad']}.")
    if not r["cumple_semanas"]:
        avisos.append(f"No alcanza las semanas minimas de {r['año']}, asi que el "
                      "resultado solo aplicaria si llega a completarlas.")
    if not r["transicion"]:
        avisos.append(f"Con menos de {r['umbral']} semanas al corte queda fuera de la "
                      f"transicion. El IBL se limito a {TOPE_PRIMA_MEDIA_SMMLV} salarios "
                      "minimos y falta sumar el ahorro individual, si lo tiene. Esta "
                      "parte es ilustrativa porque aun falta reglamentacion.")
    if r["alterna"]:
        tasa, mesada = r["alterna"]
        desde = f"{r['base_alterna']:,}".replace(",", ".")
        avisos.append(f"Contando adicionales desde {desde} semanas: "
                      f"tasa {tasa:.2f}%, mesada {pesos(mesada)}.")
    meses_equivalentes = semanas * 7 / 30
    if r["meses"] < meses_equivalentes * 0.9:
        avisos.append(f"HISTORIAL tiene {r['meses']} meses, pero las semanas equivalen a "
                      f"unos {meses_equivalentes:.0f}. Completa el historial si puedes.")

    if avisos:
        print("\nAvisos:")
        for aviso in avisos:
            print(f"- {aviso}")


if __name__ == "__main__":
    resultado = calcular(
        SEXO, AÑO_NACIMIENTO, SEMANAS_TOTALES, SEMANAS_AL_1_ABRIL_2027,
        HISTORIAL, AÑO_PENSION, SALARIOS_EN_PESOS_DE_HOY, IPC_INDICE,
        mujer_desde=MUJER_ADICIONALES_DESDE,
    )
    imprimir(resultado, SEMANAS_TOTALES)
