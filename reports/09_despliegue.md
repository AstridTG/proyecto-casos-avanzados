# Despliegue de la app

> La app se ejecuta **en local**; no se publica en la nube. Lo marcado _(completar)_ lo llena el grupo en la clase 5
> (viernes 6 de noviembre).

## 1. Dónde corre y estado

| Dato | Valor |
|---|---|
| Dónde corre | **En local**, en el computador de la demo: `streamlit run app/streamlit_app.py` → <http://localhost:8501> |
| Por qué en local | Decisión del grupo del 3-nov-2026, **aprobada por el profesor**: la app y el seguimiento de experimentos (MLflow) quedan en local. No se publica en Streamlit Community Cloud ni se usa Databricks |
| Repo, rama y archivo principal | <https://github.com/AstridTG/proyecto-casos-avanzados> · `main` · `app/streamlit_app.py` |
| Versión de Python | ☒ 3.12  ☐ otra |
| ¿Se comprobó en el computador de la demo? | ☐ sí  ☐ no _(completar)_ |

### Pasos para correr la app (≈ 5 minutos la primera vez)

1. Clonar el repo y crear el entorno con Python 3.12: `uv venv --python 3.12 .venv` y `uv pip install --python .venv/Scripts/python.exe -r requirements.txt` (Mac/Linux: `.venv/bin/python`).
2. Comprobar que `models/model.joblib` y `models/input_schema.json` estén en el repo: la app no necesita la base cruda ni volver a entrenar.
3. En Windows, definir `$env:PYTHONUTF8=1`.
4. `.venv/Scripts/streamlit run app/streamlit_app.py` y abrir <http://localhost:8501>.
5. Hacer las 5 pruebas de la sección 3. Para la carga masiva hace falta `Base_sintetica_creditos.csv`, que no está en el repo.

## 2. Decisiones de despliegue y su motivo

| Decisión | Motivo |
|---|---|
| La app corre **en local** y no se publica | Aprobado por el profesor (3-nov-2026). Además, la base es sintética y la app es una demostración académica; publicarla no aporta a la decisión del caso |
| La app carga `models/model.joblib` desde el repo y **no consulta Databricks** | No necesita credenciales ni conexión, y funciona igual en cualquier computador con el entorno instalado |
| Versiones fijadas en `requirements.txt` (Python 3.12) | El modelo se entrenó con scikit-learn 1.9.1 y LightGBM 4.7.0: otra versión puede no cargar el `joblib` o predecir distinto |
| Qué NO se subió al repo (y por qué) | `data/raw/` (base con nombres y documentos sintéticos), `data/processed/`, `.env` (credenciales), `mlflow_local.db` y `models/final_pipeline.joblib` (se regeneran) |
| El formulario valida rangos posibles y acepta "No sé" | Un dato imposible se rechaza con un mensaje claro; un dato desconocido lo imputa el pipeline |
| Aviso de uso responsable visible | La app apoya la priorización; no aprueba ni niega créditos |

## 3. Pruebas en local

Resultados repetidos el 3-nov-2026 con el modelo LightGBM vigente, llamando a las mismas funciones de `src/proyecto/inference/` que usa la app. En el computador de la demo se repiten y se completa la última columna.

| Caso | Datos usados | Resultado esperado | Resultado (3-nov) | Resultado en el computador de la demo |
|---|---|---|---|---|
| Normal | Ejemplo "Crédito típico (36 meses)" | Seguimiento normal | 🟢 Seguimiento normal, 15,7 % (0,99 × el promedio) | _(completar)_ |
| Límite (cambia la decisión) | Ejemplo "Plazo corto (6 meses)" | Priorizar | ⚠️ **🟢 Seguimiento normal**, 22,2 % (1,41 × el promedio). Con el umbral vigente (30,1 %) este ejemplo ya no cambia la decisión | _(completar)_ |
| Inválido | Plazo = −5 | Rechazo con mensaje | "Revisa los datos: Plazo (meses): debe estar entre 1 y 360" | _(completar)_ |
| Con un campo en «No sé» | Tasa y ciudad en "No sé" | Responde igual | Responde (el pipeline imputa) | _(completar)_ |
| Carga masiva | `Base_sintetica_creditos.csv` (60.000 créditos, formato del sistema) | Califica, excluye reestructurados, permite descargar | 56.381 calificados, **47 a priorizar (0,08 %)**, 3.619 excluidos; ~2 s. Probabilidad máxima del archivo: 37,2 % | _(completar)_ |

- **⚠️ Consecuencia del umbral vigente:** la app casi nunca sugiere priorizar (47 de 56.381 créditos del archivo). Por eso la app muestra un aviso que recomienda la regla del plazo corto (plazo ≤ 6 meses). El grupo decidió no cambiar la lógica de decisión para el H2 (opción A). Para mostrar en vivo un caso que cambie la decisión hace falta un ejemplo con probabilidad ≥ 30,1 %, que es muy poco común.

## 4. Problemas encontrados y plan B

- **Errores al correrla:** _(completar si aparecen)_. Los más comunes: versión de Python distinta de 3.12 (falla al instalar o al cargar el modelo), `PYTHONUTF8` sin definir en Windows y el error de LightGBM en Windows (solución en el README).
- **Plan B:** captura de pantalla con fecha → `presentacion/captura_app.png` _(completar)_, y tener la app ya abierta en el navegador antes de empezar la presentación.

## 5. Ensayo cronometrado (clase 5)

| Parte | Tiempo previsto | Tiempo real |
|---|---|---|
| Caso de negocio | 2 min | _(completar)_ |
| App (demo en vivo) | 4 min | _(completar)_ |
| Resultados | 3 min | _(completar)_ |
| Cierre | 1 min | _(completar)_ |
| **Total** | **10 min** | _(completar)_ |

- ¿Se pasó de 10 minutos? _(completar)_
- Retroalimentación recibida y corrección que hicimos: _(completar)_
- Quién habla de qué y quién responde las preguntas técnicas: _(completar)_
