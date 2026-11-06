# LibranzaRadar

> Prioriza a qué créditos de libranza aprobados dar revisión y seguimiento con la empresa pagadora, estimando la
> probabilidad de que caigan en más de 30 días de mora. Para el analista de crédito de una caja de compensación,
> que conserva la decisión final.

**App:** corre **en local** (`streamlit run app/streamlit_app.py`); no se publica en la nube (aprobado por el profesor el 3-nov-2026). Ver `reports/09_despliegue.md`.

**Atajo en Windows:** doble clic en `scripts/run_app.bat`. Revisa el entorno y el modelo, arranca la app solo para este computador y abre el navegador en <http://localhost:8501>.

## Resultado en una línea

Con la información disponible **al aprobar**, la base sintética casi no permite anticipar la mora: el modelo elegido
(LightGBM) ordena el riesgo apenas mejor que el azar (AUC ≈ 0,54), igual que una regla simple de "plazo corto = más
riesgo", y con su umbral casi nunca prioriza. **Recomendamos priorizar con la regla del plazo corto (plazo ≤ 6 meses).** El proyecto entrega el flujo completo (datos → modelo → seguimiento → app) y lo dice con honestidad. Cifras de
la prueba en `reports/07_validacion.md`.

## Qué contiene

| Carpeta | Contenido |
|---|---|
| `especificacion-proyecto.md`, `especificaciones/` | Caso, métrica, riesgos y especificaciones de cada etapa |
| `data/raw/` | `Base_sintetica_creditos.csv` (**no se sube**: tiene nombres y documentos sintéticos) |
| `data/processed/` | Entrenamiento y prueba generados por el notebook 03 (no se versionan) |
| `notebooks/` | 01 a 09, uno por etapa; solo orquestan |
| `src/proyecto/` | `data/` (limpieza y partición por cliente), `features/`, `models/` (torneo, métrica de negocio, Optuna), `tracking/` (MLflow), `inference/` |
| `tests/` | `pytest`: una prueba por regla de limpieza, partición, variables, métricas, inferencia, app y tracking |
| `models/` | `model.joblib` (pipeline completo), `input_schema.json` y `ficha_modelo.md` |
| `app/streamlit_app.py` | La app: pestaña **Un crédito** (formulario con explicación) y **Carga masiva** (sube un CSV/Excel con muchos créditos, en el formato del sistema de cartera o con las 12 columnas del modelo, y descarga la priorización) |
| `reports/` | Una sección por etapa e `informe_tecnico.md` |
| `presentacion/ejecutiva.md` | 5 diapositivas (Marp) |

## Cómo ejecutarlo

Requiere Python 3.12 y [uv](https://docs.astral.sh/uv/) (o `python -m venv` + `pip`).

```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # Mac/Linux: .venv/bin/python
# no hace falta .env: el seguimiento usa MLflow local
# copia Base_sintetica_creditos.csv en data/raw/
pytest -q                        # 57 pruebas (las del modelo real usan models/)
streamlit run app/streamlit_app.py
```

Para reproducir todas las decisiones desde la base cruda, ejecuta los notebooks **01 a 06** en orden (≈ 20 minutos en un portátil):

```bash
cd notebooks
for n in 01_caso_negocio 02_eda 03_preprocesamiento 04_features 05_torneo 06_optimizacion; do
  jupyter nbconvert --to notebook --execute --inplace --ExecutePreprocessor.timeout=3600 $n.ipynb
done
cd ..
git status --short reports/   # si la reproducción es exacta, las tablas y JSON de reports/ no cambian
```

En Windows (PowerShell) define antes `$env:PYTHONUTF8=1`.

**No ejecutes el notebook 07** (ni el 08 y el 09, que dependen de él): el 07 abre el conjunto de prueba y agrega
una línea a `reports/prueba_abierta.txt`. La prueba ya se abrió y sus resultados están en
`reports/07_metricas_test.json` y `reports/07_validacion.md`; volver a abrirla sería una apertura más. Para comprobar
el modelo final usa `pytest -q` y la app, que cargan `models/model.joblib` desde el repositorio.

**Windows: error al cargar LightGBM.** Si `import lightgbm` (notebooks 08 y 09, o la app) falla con
`Could not find module '...lib_lightgbm.dll' (or one of its dependencies)`, falta el **Microsoft Visual C++
2015-2022 Redistributable (x64)**, que trae `vcomp140.dll`. Instálalo con el instalador oficial
<https://aka.ms/vs/17/release/vc_redist.x64.exe>, o desde PowerShell como administrador:

```powershell
winget install Microsoft.VCRedist.2015+.x64 --source winget --accept-source-agreements --accept-package-agreements
```

Si al final pide reiniciar, puedes elegir *Close*. Comprueba con
`python -c "import lightgbm; print(lightgbm.__version__)"` (debe mostrar la versión, sin error).

### Seguimiento de experimentos (MLflow)

El proyecto usa **MLflow local** (`mlflow_local.db`), aprobado por el profesor el 3-nov-2026. `src/proyecto/tracking/mlflow_utils.py` conserva la
opción de Databricks si `.env` tiene `PROFILE` o `DATABRICKS_HOST` + `DATABRICKS_TOKEN`, pero no se usa. Para ver los experimentos locales:

```bash
mlflow ui --backend-store-uri sqlite:///mlflow_local.db
```

Experimentos: `libranzaradar-04-features`, `-05-torneo`, `-06-optimizacion` (cada ensayo de Optuna es una ejecución
anidada) y `-08-registro`. Modelo registrado: `libranzaradar_mora30`, alias `champion`.

## Equipo

| Integrante | Rol |
|---|---|
| Juan Rafael Taborda | _(completar)_ |
| Yenifer Tatiana Calle Zapata | _(completar)_ |
| Daniela Acevedo Alvares | _(completar)_ |
| Liliana Maria Garcia Builes | _(completar)_ |
| Astrid Liliana Torres Gonzalez | _(completar)_ |

Repositorio: <https://github.com/AstridTG/proyecto-casos-avanzados>

Especificación del proyecto: [`especificacion-proyecto.md`](especificacion-proyecto.md) · Informe técnico: [`reports/informe_tecnico.md`](reports/informe_tecnico.md)
