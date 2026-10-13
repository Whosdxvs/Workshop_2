# Guía Definitiva de Ejecución y Sustentación — Workshop 2
**Curso:** ETL (G01) — Universidad Autónoma de Occidente (UAO)  
**Proyecto:** Canalización Batch Confiable (Spotify + Grammy Awards) con Airflow y Great Expectations  

---

## 🎯 Resumen Rápido (En 1 Minuto)

Este sistema resuelve el taller completo integrando dos fuentes de datos heterogéneas:
1. **Spotify (CSV):** 114,000 registros con métricas de popularidad y atributos acústicos.
2. **Grammy Awards (Base de Datos Relacional):** 4,810 registros históricos que se cargan primero en una tabla operacional (`source_grammy_awards`) y se extraen vía SQL (cumpliendo el requerimiento de que la canalización no lee los Grammys directamente del CSV).

El flujo aplica **dos compuertas de validación automatizada** con **Great Expectations**:
- **Compuerta Raw:** Valida la calidad antes de transformar.
- **Compuerta Prepared:** Valida unicidad, dominios e integridad referencial antes de cargar al Data Warehouse.

El resultado final se almacena en un **Data Warehouse Dimensional (Star Schema)** en MySQL/PostgreSQL y alimenta un **Dashboard Analítico** con 3 KPIs y visualizaciones.

---

## 📋 Requisitos Previos

1. **Python 3.11+** instalado en tu sistema.
2. **MySQL 8.0+** corriendo localmente en el puerto `3306` (o Docker Desktop si deseas usar contenedores).
3. Terminal (PowerShell, CMD o Bash).

---

## 🚀 Método 1: Ejecución Local Rápida (Recomendado en Windows)

Esta es la forma más directa, rápida y confiable de correr todo el proyecto y verificar que cada componente funciona al 100%.

### Paso 1: Instalar Dependencias
Abre una terminal PowerShell en la carpeta del proyecto (`Workshop_2`) y ejecuta:
```powershell
pip install -r requirements.txt
```

---

### Paso 2: Verificar la Configuración (.env)
El archivo `.env` ya está creado y configurado para tu base de datos local:
```ini
SOURCE_DB_TYPE=mysql
SOURCE_DB_HOST=127.0.0.1
SOURCE_DB_PORT=3306
SOURCE_DB_USER=root
SOURCE_DB_PASSWORD=
SOURCE_DB_NAME=grammy_source_db

DW_DB_TYPE=mysql
DW_DB_HOST=127.0.0.1
DW_DB_PORT=3306
DW_DB_USER=root
DW_DB_PASSWORD=
DW_DB_NAME=music_dw
```
*(Si tu usuario `root` de MySQL tiene contraseña, simplemente agrégala en `SOURCE_DB_PASSWORD=` y `DW_DB_PASSWORD=`)*.

---

### Paso 3: Inicializar la Base de Datos Relacional de Origen
**¿Qué hace?**  
Crea la base de datos `grammy_source_db`, crea la tabla `source_grammy_awards`, carga el CSV original y genera la auditoría de reconciliación requerida por el profesor (`CSV = 4,810 filas, BD = 4,810 filas`).

**Comando:**
```powershell
python -m src.setup_source_db
```
**Resultado esperado:**
```text
SOURCE PREPARATION AND RECONCILIATION SUCCESSFUL
Grammy CSV Rows:      4810
Database Table Rows: 4810
```
*Evidencia generada:* [`docs/evidence/source_reconciliation.json`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/source_reconciliation.json)

---

### Paso 4: Ejecutar el Perfilamiento de Datos
**¿Qué hace?**  
Analiza completitud, duplicados, tipos y solapamiento entre fuentes. Genera gráficos estadísticos y ejecuta el notebook de Jupyter.

**Comandos:**
```powershell
python -m src.profile_data
python -m src.build_notebook
```
*Evidencias generadas:*  
- Gráficos en [`docs/evidence/profiling/`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/profiling/)  
- Notebook ejecutado listo para mostrar: [`notebooks/data_profiling.ipynb`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/notebooks/data_profiling.ipynb)

---

### Paso 5: Ejecutar las Pruebas Obligatorias de Confiabilidad (Tests A, B y C)
**¿Qué hace?**  
Este script corre automáticamente las 3 pruebas obligatorias de la Sección 7 del taller:
- **Test A (Éxito Total):** Corre extracción, validación raw, transformación, validación preparada y carga al DW con datos válidos.
- **Test B (Falla Crítica Controlada):** Inyecta datos inválidos (`danceability = 99.5`), demuestra que la compuerta raw de Great Expectations detecta el error y **bloquea inmediatamente la transformación y la carga al DW** (evitando contaminar la base de datos).
- **Test C (Reejecución Segura / Idempotencia):** Vuelve a correr la carga con el mismo lote y demuestra matemáticamente que hay **0 duplicados** (crecimiento neto = 0 en todas las tablas).

**Comando:**
```powershell
python -m src.run_mandatory_tests
```
**Resultado esperado:**
```text
>>> TEST A COMPLETED SUCCESSFULLY! All tasks succeeded.
>>> TEST B COMPLETED SUCCESSFULLY! Failure was anticipated, observable, and downstream tasks blocked.
>>> TEST C COMPLETED SUCCESSFULLY! Safe rerun verified with zero duplicate growth.
================================================================================
ALL MANDATORY RELIABILITY TESTS COMPLETED AND DOCUMENTED
================================================================================
```
*Evidencias generadas:*  
- Test A: [`docs/evidence/test_a_success/test_a_results.json`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/test_a_success/test_a_results.json)  
- Test B: [`docs/evidence/test_b_controlled_failure/controlled_failure_explanation.md`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/test_b_controlled_failure/controlled_failure_explanation.md)  
- Test C: [`docs/evidence/test_c_safe_rerun/safe_rerun_report.md`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/test_c_safe_rerun/safe_rerun_report.md)

---

### Paso 6: Generar el Dashboard y los KPIs Analíticos
**¿Qué hace?**  
Ejecuta las consultas SQL analíticas directamente sobre el Data Warehouse dimensional (`music_dw`), genera las imágenes de los gráficos y crea el dashboard interactivo en HTML.

**Comando:**
```powershell
python -m src.analytics_dashboard
```
**Resultado esperado:**
```text
================================================================================
ANALYTICAL DASHBOARD GENERATED SUCCESSFULLY
HTML Dashboard: docs\evidence\dashboard\interactive_dashboard.html
Charts Output:  docs\evidence\dashboard
================================================================================
```

---

### Paso 7: Validar el DAG de Apache Airflow
**¿Qué hace?**  
Verifica la sintaxis e integridad del DAG escrito con la TaskFlow API de Airflow 3.1.8.

**Comando:**
```powershell
python dags/reliable_music_pipeline.py
```

---

## 🌐 Cómo Ver y Mostrar el Dashboard

Para ver los resultados visuales e interactivos del proyecto:

1. Ve a la carpeta `docs/evidence/dashboard/`.
2. Haz doble clic en el archivo **[`interactive_dashboard.html`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/dashboard/interactive_dashboard.html)** para abrirlo en tu navegador web (Chrome, Edge, Opera, etc.).
3. Verás:
   - Tarjetas KPI con la popularidad de artistas élite vs emergentes y volumen de pistas.
   - **KPI 1:** Prima de popularidad de los Grammys por género musical (+25 a +40 puntos en géneros top).
   - **KPI 2:** Perfil acústico y popularidad por nivel de reconocimiento del artista.
   - **KPI 3:** Evolución taxonómica de categorías a lo largo de las eras históricas.

---

## 🐳 Método 2: Ejecución en Contenedores (Docker Compose)

Este método levanta el stack completo de **Apache Airflow 3.1.8 + MySQL + PostgreSQL** usando Docker, sin necesidad de instalar nada manualmente en tu máquina (salvo Docker Desktop).

> **Nota:** El Método 1 (local) es suficiente para demostrar el pipeline completo. Usa este método **solo si quieres mostrar Airflow corriendo**.

---

### Prerrequisito: Instalar Docker Desktop

1. Descarga e instala **Docker Desktop** desde: [https://www.docker.com/products/docker-desktop](https://www.docker.com/products/docker-desktop)
2. Una vez instalado, ábrelo y espera a que el ícono de la ballena en la barra de tareas quede en verde (**"Engine running"**).
3. Verifica que funciona abriendo una terminal y ejecutando:
   ```powershell
   docker --version
   ```
   Deberías ver algo como: `Docker version 27.x.x, build ...`

---

### ¿Dónde se escriben los comandos?

Todos los comandos Docker se ejecutan en una terminal **PowerShell** o **CMD**, **dentro de la carpeta del proyecto**:

```powershell
cd "C:\Users\josed\OneDrive\Desktop\Workshop_2"
```

---

### Comandos Docker para este proyecto

#### 🟢 Levantar todos los servicios (primer arranque — tarda ~5 min)
```powershell
docker compose up --build -d
```
- `--build`: construye la imagen personalizada de Airflow con las dependencias del proyecto.
- `-d`: corre en segundo plano (*detached mode*).

#### 🔍 Ver si los contenedores están corriendo
```powershell
docker compose ps
```

#### 📋 Ver logs en tiempo real
```powershell
docker compose logs -f
```
*(Presiona `Ctrl+C` para salir sin apagar los contenedores)*

#### 🔄 Reiniciar un servicio específico
```powershell
docker compose restart airflow-webserver
```

#### 🔴 Apagar todos los servicios
```powershell
docker compose down
```

#### 🗑️ Apagar y borrar todos los datos (reset completo)
```powershell
docker compose down -v
```

---

### Servicios que levanta Docker

| Contenedor | Qué es | Puerto local |
|:---|:---|:---|
| `airflow-postgres` | BD interna de metadatos de Airflow | interno |
| `source-mysql` | MySQL con datos Grammy Awards | `3307` |
| `dw-postgres` | PostgreSQL Data Warehouse (`music_dw`) | `5433` |
| `airflow-webserver` | Interfaz web de Airflow | `8080` |
| `airflow-scheduler` | Motor que ejecuta las tareas | interno |

---

### Acceder a Airflow

Una vez levantado, abre en tu navegador:

- **URL:** [http://localhost:8080](http://localhost:8080)
- **Usuario:** `airflow`
- **Contraseña:** `airflow`

En la interfaz gráfica de Airflow:
1. Busca el DAG `reliable_music_pipeline`.
2. Actívalo con el toggle de la izquierda.
3. Haz clic en ▶️ **Trigger DAG** para ejecutarlo manualmente.
4. Observa en la vista *Graph View* o *Grid View* la ejecución paralela de ambas ramas, su convergencia y la carga final al Data Warehouse.

---

## 🎓 Guía para la Defensa / Preguntas Típicas del Profesor

Si el profesor o evaluador te hace preguntas técnicas, aquí tienes las respuestas exactas:

### 1. ¿Cómo demuestran que los Grammys no se leen directamente del CSV?
> **Respuesta:** *"Durante la etapa de preparación de fuentes (`src/setup_source_db.py`), el CSV se cargó en la base de datos relacional MySQL en la tabla `source_grammy_awards` y se validó la reconciliación exacta de 4,810 registros (evidenciado en `docs/evidence/source_reconciliation.json`). En el pipeline operacional (`src/extract.py`), la tarea `extract_grammys` extrae los datos ejecutando una consulta SQL `SELECT ... FROM source_grammy_awards`, no abriendo el CSV."*

---

### 2. ¿Cómo manejan la política de reintentos (Retries)? ¿Por qué no pusieron retries=3 en todo?
> **Respuesta:** *"Poner retries=3 en todo es una mala práctica de ingeniería porque una regla estricta de calidad o un error de esquema es determinístico: volverlo a correr con el mismo dato erróneo va a fallar exactamente igual. Por eso aplicamos reintentos selectivos:
> - **Fallas Operacionales Transitorias (conexión a la BD caída, timeout de red):** Se configuran con `retries = 2 a 3` y backoff exponencial porque pueden resolverse solas.
> - **Fallas Determinísticas de Datos / Validación (Great Expectations):** Se configuran con `retries = 0`. La compuerta se detiene inmediatamente y emite un reporte auditable para no desperdiciar cómputo."*

---

### 3. ¿Cómo funciona la compuerta de falla controlada (Test B)?
> **Respuesta:** *"En el Test B inyectamos un lote corrupto con `danceability = 99.5`, lo cual viola la regla física de que los atributos de audio deben estar entre 0.0 y 1.0 (`RULE-RAW-SPOTIFY-02`). La compuerta raw de Great Expectations detecta la anomalía, levanta una excepción `QualityGateFailureError` y detiene el flujo. Las tareas de transformación y carga quedan en estado **BLOQUEADO**, garantizando que ningún registro corrupto llegue al Data Warehouse."*

---

### 4. ¿Cómo garantizan que si reejecutan el pipeline no se duplican los datos (Test C / Idempotencia)?
> **Respuesta:** *"Implementamos una estrategia de recarga transaccional atómica e idempotente (`src/load.py`). Antes de insertar, el cargador ejecuta un vaciado dentro de una transacción ACID (`with engine.begin():`). Al reejecutar el pipeline con el mismo lote, auditamos las filas antes y después: el crecimiento neto de todas las tablas fue exactamente **0 duplicados**, y los promedios de popularidad y atributos acústicos se mantuvieron matemáticamente idénticos (evidenciado en `docs/evidence/test_c_safe_rerun/safe_rerun_report.md`)."*

---

### 5. ¿Cómo pasaron los datos entre tareas en Airflow?
> **Respuesta:** *"Cumpliendo con las mejores prácticas de Airflow, no pasamos DataFrames pesados a través de XCom ni de la base de datos de metadatos de Airflow. Las tareas intercambian referencias ligeras (diccionarios con rutas a los archivos en staging, IDs de lote y conteos de registros). Esto desacopla el orquestador del almacenamiento y permite alta escalabilidad."*

---

### 6. ¿Cómo resolvieron la armonización de artistas y categorías?
> **Respuesta:** *"Encontramos dos desafíos principales durante el perfilamiento:
> 1. En los Grammys, 1,840 filas tenían el artista nulo porque correspondían a categorías de compositores (ej. Canción del Año). La lógica en `src/transform.py` extrajo el artista del campo `workers` y `nominee`.
> 2. Variaciones de acentos y mayúsculas (`André Previn` vs `Andre Previn`, o categorías con `OR` vs `Or`). Se aplicó normalización Unicode NFD para armonizar los nombres a una sola entidad canónica en `dim_artist` con claves subrogadas (`artist_id`)."*

---

## 📂 Índice de Archivos Clave del Proyecto

| Componente | Archivo Principal |
| :--- | :--- |
| **Documentación Formal Completa** | [`README.md`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/README.md) |
| **DAG de Apache Airflow** | [`dags/reliable_music_pipeline.py`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/dags/reliable_music_pipeline.py) |
| **DDL del Data Warehouse (Star Schema)** | [`sql/dw_schema.sql`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/sql/dw_schema.sql) |
| **Consultas SQL de los 3 KPIs** | [`sql/kpi_queries.sql`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/sql/kpi_queries.sql) |
| **Notebook de Perfilamiento** | [`notebooks/data_profiling.ipynb`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/notebooks/data_profiling.ipynb) |
| **Dashboard Ejecutivo Interactivo** | [`docs/evidence/dashboard/interactive_dashboard.html`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence/dashboard/interactive_dashboard.html) |
| **Registro Completo de Evidencias** | [`docs/evidence_register.md`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/evidence_register.md) |
| **Matriz de Trazabilidad** | [`docs/traceability_matrix.md`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/traceability_matrix.md) |
| **Política de Reintentos y Fallas** | [`docs/failure_policy.md`](file:///c:/Users/josed/OneDrive/Desktop/Workshop_2/docs/failure_policy.md) |
