# Despliegue de la app

> Se completa en la clase 5 (viernes 6 de noviembre), después de desplegar. Lo marcado _(completar)_ lo llena el grupo.

## 1. Enlace y estado

| Dato | Valor |
|---|---|
| Enlace público de la app | _(completar)_ |
| Plataforma | Streamlit Community Cloud |
| Repo, rama y archivo principal | _(usuario/repo)_ · `main` · `app/streamlit_app.py` |
| Versión de Python elegida | ☒ 3.12  ☐ otra |
| ¿Se comprobó en una **ventana privada**? | ☐ sí  ☐ no _(completar)_ |
| ¿Se desplegó? | ☐ sí  ☐ no _(completar)_ |

### Pasos para desplegar (≈ 10 minutos)

1. Subir el repo a GitHub como **público** (sin `data/raw/`, `.env` ni `mlflow_local.db`: ya están en `.gitignore`). Comprobar que `models/model.joblib` y `models/input_schema.json` **sí** estén subidos.
2. Entrar a <https://share.streamlit.io> con la cuenta de GitHub → **Create app** → *Deploy a public app from GitHub*.
3. Repositorio: el del grupo · Rama: `main` · Archivo: `app/streamlit_app.py`.
4. **Advanced settings → Python 3.12.** No hace falta ningún *secret*: la app no consulta Databricks.
5. **Deploy.** La primera instalación tarda unos minutos (lee `requirements.txt` de la raíz).
6. Abrir el enlace en una ventana privada y hacer las 4 pruebas de la sección 3.

## 2. Decisiones de despliegue y su motivo

| Decisión | Motivo |
|---|---|
| La app carga `models/model.joblib` desde el repo y **no consulta Databricks** | No se ponen credenciales en la nube y la app no depende de la cuota de Databricks Free Edition |
| Versiones fijadas en `requirements.txt` (Python 3.12) | El modelo se entrenó con scikit-learn 1.9.1 y LightGBM 4.7.0: otra versión puede no cargar el `joblib` o predecir distinto |
| Qué NO se subió al repo (y por qué) | `data/raw/` (base con nombres y documentos sintéticos), `data/processed/`, `.env` (credenciales), `mlflow_local.db` y `models/final_pipeline.joblib` (se regeneran) |
| El formulario valida rangos posibles y acepta "No sé" | Un dato imposible se rechaza con un mensaje claro; un dato desconocido lo imputa el pipeline |
| Aviso de uso responsable visible | La app apoya la priorización; no aprueba ni niega créditos |

## 3. Pruebas del enlace público

Resultados de la prueba **en local** (repetidos el 3-nov-2026 con el modelo LightGBM vigente, llamando a las mismas funciones de `src/proyecto/inference/` que usa la app). En el enlace público se repiten y se completa la última columna.

| Caso | Datos usados | Resultado esperado | Resultado en local | Resultado en el enlace |
|---|---|---|---|---|
| Normal | Ejemplo "Crédito típico (36 meses)" | Seguimiento normal | 🟢 Seguimiento normal, 15,7 % (0,99 × el promedio) | _(completar)_ |
| Límite (cambia la decisión) | Ejemplo "Plazo corto (6 meses)" | Priorizar | ⚠️ **🟢 Seguimiento normal**, 22,2 % (1,41 × el promedio). Con el umbral vigente (30,1 %) este ejemplo ya no cambia la decisión | _(completar)_ |
| Inválido | Plazo = −5 | Rechazo con mensaje | "Revisa los datos: Plazo (meses): debe estar entre 1 y 360" | _(completar)_ |
| Con un campo en «No sé» | Tasa y ciudad en "No sé" | Responde igual | Responde (el pipeline imputa) | _(completar)_ |
| Carga masiva | `Base_sintetica_creditos.csv` (60.000 créditos, formato del sistema) | Califica, excluye reestructurados, permite descargar | 56.381 calificados, **47 a priorizar (0,08 %)**, 3.619 excluidos; ~2 s. Probabilidad máxima del archivo: 37,2 % | _(completar)_ |

- **⚠️ Consecuencia del umbral vigente:** la app casi nunca sugiere priorizar (47 de 56.381 créditos del archivo). Por eso la app muestra un aviso que recomienda la regla del plazo corto (plazo ≤ 6 meses). El grupo decidió no cambiar la lógica de decisión para el H2 (opción A). Para mostrar en vivo un caso que cambie la decisión hace falta un ejemplo con probabilidad ≥ 30,1 %, que es muy poco común.

## 4. Problemas encontrados y plan B

- **Errores de despliegue:** _(completar si aparecen)_. Los más comunes: versión de Python distinta de 3.12 (falla al instalar o al cargar el modelo) y `models/model.joblib` sin subir.
- **Plan B:** captura de pantalla con fecha y repo → `presentacion/captura_app.png` _(completar)_; app en local → `streamlit run app/streamlit_app.py`.

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
