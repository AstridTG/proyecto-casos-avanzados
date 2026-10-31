# proyecto-casos-avanzados

> Modelo de machine learning sobre créditos de libranza (base sintética) para la iniciativa *Servicios
> Financieros 2.0* de Comfama: ayudar a las empresas, desde la autogestión, y al área de cartera a priorizar
> los créditos con mayor probabilidad de llegar a más de 30 días de mora. *(Borrador: por confirmar en
> `especificacion-proyecto.md`.)*

**App desplegada:** _enlace público de Streamlit (se completa en la clase 5)_

## Qué contiene
Estructura obligatoria del curso. Cada carpeta tiene un propósito:

| Carpeta | Contenido |
|---|---|
| `.specify/` y `.claude/` | Entorno de IA: constitución del proyecto, Spec Kit (`/speckit-…`) y subagentes |
| `specs/` | Lo que genera Spec Kit: `spec.md`, `plan.md`, `tasks.md` de cada pieza (aparece al usarlo) |
| `especificaciones/` | Guías que se llenan **antes** de programar cada etapa |
| `data/raw/` | Datos originales, intocables |
| `data/processed/` | Datos limpios generados por el código |
| `notebooks/` | Un notebook por etapa; solo orquestan |
| `src/proyecto/` | Código reutilizable (data, features, models, tracking, inference) |
| `tests/` | Pruebas con `pytest` |
| `models/` | `model.joblib` y `ficha_modelo.md` |
| `app/` | `streamlit_app.py` |
| `reports/` | Una sección por hito e `informe_tecnico.md` |
| `presentacion/` | `ejecutiva.md` (máximo 5 diapositivas) |

## Cómo ejecutarlo
```bash
uv venv --python 3.12 .venv
uv pip install --python .venv/Scripts/python.exe -r requirements.txt   # en Mac/Linux: .venv/bin/python
cp .env.example .env     # completa PROFILE o DATABRICKS_HOST y DATABRICKS_TOKEN
python scripts/check_databricks.py
pytest
streamlit run app/streamlit_app.py
```

## De dónde viene este repositorio
Nació de la rama `feature/estudiantes` del repositorio del curso (ver `LEEME-PRIMERO.md`): una persona del grupo la clonó con
`git clone --branch feature/estudiantes --single-branch …`, la apuntó a este repo con `git remote set-url origin …` y hizo `push`. Los demás integrantes
clonan **este** repositorio. Para arrancar, sigue `material-del-curso/guias/montaje-proyecto.md`.

## Equipo
| Integrante | Rol |
|---|---|
| | |

Especificación del proyecto: [`especificacion-proyecto.md`](especificacion-proyecto.md) · Especificaciones por etapa: [`especificaciones/`](especificaciones/)
