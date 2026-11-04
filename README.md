# Calculadora de pensión Colpensiones

[Español](#español) | [English](#english)

## Español

Calculadora web y script en Python para estimar la pensión de vejez en Colpensiones (Colombia).

> **Importante:** el resultado es una estimación, no el valor oficial que reconocería Colpensiones. Este proyecto no es asesoría legal ni financiera y no tiene relación con Colpensiones.

### Archivos

| Archivo | Uso |
| --- | --- |
| `index.html` | Calculadora web. Calcula en el navegador, sin dependencias ni backend. |
| `pension_colombia.py` | La misma calculadora para terminal, con las variables al inicio del archivo. |

Los dos archivos calculan por separado. Si cambias una regla, cámbiala en ambos.

### Cómo ejecutarlo

Requiere Python 3 para el script o para levantar la página en local.

**Página web:**

```bash
python3 -m http.server 8000
```

Luego abre `http://localhost:8000`. También puedes abrir `index.html` directamente en el navegador.

**Script:** edita las variables de la sección `DATOS DE LA PERSONA` y ejecuta:

```bash
python3 pension_colombia.py
```

Los datos que traen ambos archivos son un ejemplo inventado.

### Cómo calcula

1. Promedia los salarios de los últimos 120 meses cotizados.
2. Promedia toda la vida laboral, si la persona tiene al menos 1.250 semanas.
3. Usa el promedio mayor como IBL (ingreso base de liquidación).
4. Calcula la tasa de reemplazo:

   ```text
   s = IBL / salario mínimo
   tasa base = 65,5 - 0,5 × s, entre 55% y 65%
   tasa = tasa base + 1,5 por cada 50 semanas adicionales, hasta 80%
   ```

5. Calcula la mesada como `IBL × tasa`, entre 1 y 25 salarios mínimos.

### Parámetros

- **Salario mínimo:** trae el valor de 2026, $1.750.905. Actualízalo cada año.
- **Salarios:** por defecto se toman en pesos de hoy. Para actualizarlos con IPC, carga los índices del DANE; el ajuste es anual, no mensual.
- **Semanas adicionales en mujeres:** las fuentes no coinciden en si se cuentan desde 1.300 semanas o desde el mínimo del año. Se usa 1.300 por defecto y se muestra también la otra opción.
- **Bloques de 50 semanas:** por defecto solo suman los bloques completos, aunque se puede activar la fracción.

### Limitaciones

- Revisado en noviembre de 2026. Las reglas y fechas pueden cambiar.
- La Ley 2381 de 2024 está prevista para entrar en vigencia el 1 de abril de 2027, y su aplicación aún depende de decisiones pendientes de la Corte Constitucional.
- El cálculo principal corresponde a quienes queden en el régimen de transición: 900 semanas para hombres y 750 para mujeres, al 1 de abril de 2027.
- Para quienes queden por fuera, el IBL se limita a 2,3 salarios mínimos y no se incluye el ahorro individual. Esa parte es solo ilustrativa porque falta reglamentación.
- Se usa un tope de tasa de 80% para todos, aunque algunos casos citan un tope entre 70,5% y 80% según el ingreso. Con salarios altos, el valor reconocido podría ser menor.
- No cubre la reducción de semanas por hijos, los regímenes especiales ni las pensiones por invalidez o sobrevivencia.

### Base normativa

- Artículos 21, 33 y 34 de la Ley 100 de 1993, modificados por la Ley 797 de 2003.
- Sentencias C-197 de 2023 y C-054 de 2024 de la Corte Constitucional.
- Ley 2381 de 2024 y Sentencia C-264 de 2026.

---

## English

Web calculator and Python script for estimating an old-age pension from Colpensiones, Colombia's public pension fund.

> **Important:** the result is an estimate, not the official amount Colpensiones would grant. This project is not legal or financial advice and is not affiliated with Colpensiones.

### Files

| File | Purpose |
| --- | --- |
| `index.html` | Web calculator. It runs in the browser, with no dependencies or backend. |
| `pension_colombia.py` | The same calculator for the terminal, with its variables at the top of the file. |

The two files calculate independently. If you change a rule, change it in both. The code and interface are in Spanish.

### How to run it

Python 3 is required for the script or for serving the page locally.

**Web page:**

```bash
python3 -m http.server 8000
```

Then open `http://localhost:8000`. You can also open `index.html` directly in the browser.

**Script:** edit the variables in the `DATOS DE LA PERSONA` section and run:

```bash
python3 pension_colombia.py
```

The data included in both files is a made-up example.

### How it calculates

1. It averages the salaries from the last 120 months of contributions.
2. It averages the entire working life, if the person has at least 1,250 weeks.
3. It uses the higher average as the IBL (*ingreso base de liquidación*, the pension's base income).
4. It calculates the replacement rate:

   ```text
   s = IBL / minimum wage
   base rate = 65.5 - 0.5 × s, between 55% and 65%
   rate = base rate + 1.5 for every 50 additional weeks, up to 80%
   ```

5. It calculates the monthly pension as `IBL × rate`, between 1 and 25 minimum wages.

### Parameters

- **Minimum wage:** set to the 2026 value, COP 1,750,905. Update it every year.
- **Salaries:** treated as current pesos by default. To adjust them for inflation, load the CPI values published by DANE, Colombia's statistics agency. The adjustment is annual, not monthly.
- **Additional weeks for women:** sources disagree on whether they count from 1,300 weeks or from that year's minimum. The default is 1,300, and the other result is also shown.
- **50-week blocks:** by default only complete blocks count, but you can include partial blocks.

### Limitations

- Reviewed in November 2026. Rules and dates may change.
- Law 2381 of 2024 is scheduled to take effect on April 1, 2027, and its application still depends on pending Constitutional Court decisions.
- The main calculation applies to people who stay under the transition regime: 900 weeks for men and 750 for women as of April 1, 2027.
- For everyone else, the IBL is capped at 2.3 minimum wages and individual savings are not included. This part is only illustrative because regulations are still pending.
- The rate is capped at 80% for everyone, although some cases cite a cap between 70.5% and 80% depending on income. With high salaries, the amount granted could be lower.
- It does not cover the week reduction for children, special regimes, or disability and survivor pensions.

### Legal basis

- Articles 21, 33 and 34 of Law 100 of 1993, as amended by Law 797 of 2003.
- Constitutional Court rulings C-197 of 2023 and C-054 of 2024.
- Law 2381 of 2024 and ruling C-264 of 2026.
