# Learnify

## Descripción

Learnify es una plataforma orientada al aprendizaje colaborativo que permite a los usuarios trabajar en equipo, gestionar actividades académicas y dar seguimiento a su rendimiento. Está hecha con **Flask** (backend), **MongoDB** (base de datos) y **HTML/CSS/JavaScript** (frontend).

Este repositorio implementa un proceso de Integración Continua (CI) con **GitHub Actions**, mediante análisis de código y pruebas automatizadas.

## Requisitos previos

- Git
- Python 3.12
- Node.js 20 (solo para revisar la sintaxis del JavaScript)
- MongoDB en `localhost:27017` (solo para las pruebas de integración y funcionales)

## Preparar el entorno

### 1. Descargar el repositorio

```bash
git clone https://github.com/Nina9897/learnify-ci.git
cd learnify-ci
```

### 2. Crear y activar el entorno virtual

En Windows:

```bash
python -m venv venv
venv\Scripts\activate
```

En Linux o Mac: `source venv/bin/activate`

### 3. Instalar las dependencias de Python

```bash
pip install -r requirements.txt
```

### 4. Dependencias del frontend

Learnify usa HTML/JS plano y no tiene `package.json`, por lo que `npm install` y `npm run build` no aplican. Si en el futuro se agrega un frontend con npm, el pipeline ya está preparado para instalarlo y compilarlo.

### 5. Encender MongoDB (para integración y funcionales)

```bash
docker run -d --name mongo-learnify -p 27017:27017 mongo:7
```

## Ejecutar la aplicación

```bash
cd backend
python app.py
```

## Verificar el código y ejecutar las pruebas

Son los mismos pasos que ejecuta el pipeline.

```bash
# Análisis estático y build
ruff check backend tests
python -m compileall -q backend tests

# Pruebas unitarias (no requieren MongoDB)
python -m pytest tests

# Pruebas de integración y funcionales (requieren MongoDB)
cd backend
python -m pytest tests
```

Sin MongoDB, las pruebas de integración y funcionales se **omiten** (`skipped`). El pipeline las trata como rechazo.

## Integración continua

Archivo: `.github/workflows/ci.yml`

**Eventos que lo inician:** `push` a main, develop y ramas `feature/**`; `pull_request` hacia main y develop; y ejecución manual.

### Flujo del pipeline

```
push / pull_request
      |
      v
[1 Calidad y build]
  Ruff -> compileall -> importar Flask -> node --check (JS)
      |  (solo continúa si pasa)
      v
[2 Pruebas automatizadas]
  MongoDB temporal -> unitarias -> integración y funcionales
      |
      v
[3 Resultado del pipeline]
  APROBADO / RECHAZADO
```

### Condiciones de aprobación o rechazo

- **Aprobado:** Ruff sin errores, el código compila, el servidor se importa, el JavaScript es válido y todas las pruebas pasan.
- **Rechazado:** falla cualquiera de los pasos anteriores, o hay pruebas fallidas, con error u omitidas.

### Revisar los resultados

1. Entrar al repositorio en GitHub.
2. Abrir la pestaña **Actions**.
3. Seleccionar una ejecución de **CI Learnify**.
4. Revisar cada etapa y el resumen de pruebas y cobertura.

## Justificación de las herramientas

| Herramienta | Motivo |
|---|---|
| GitHub Actions | El repositorio ya está en GitHub; no requiere servidor externo |
| Ruff | Detecta imports y variables sin usar y errores de nombres; es muy rápido |
| `compileall` e importar `app` | Confirman que el código compila y que el servidor arranca |
| pytest y pytest-cov | Ejecutan las pruebas y generan reportes XML y cobertura |
| Servicio `mongo:7` | Base de datos real, temporal y desechable para las pruebas de integración |
| `node --check` | Valida la sintaxis del frontend sin necesitar npm |

## Evidencias

Las capturas de la ejecución del pipeline están en la carpeta `evidencias/`.

