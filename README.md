# 📖 NT Language Lab

Comparador de traducciones del Nuevo Testamento usando IA local.

## 🎯 Descripción

Sistema de comparación lingüística entre el texto original en griego koiné y la traducción Reina-Valera 1960 del Nuevo Testamento. Utiliza RAG (Retrieval-Augmented Generation) estricto para recuperar versículos específicos y generar análisis lingüísticos usando un LLM local servido por **llama.cpp** (API HTTP tipo OpenAI), por ejemplo Phi-3 Mini Instruct en formato GGUF.

## 🏗️ Arquitectura

Ver diagramas en [ARCHITECTURE.md](ARCHITECTURE.md).

- **Frontend**: Streamlit (puerto 8501)
- **Vector Store**: ChromaDB (persistencia en volumen Docker)
- **Embeddings**: sentence-transformers (paraphrase-multilingual-MiniLM-L12-v2)
- **LLM**: Servidor llama.cpp en el host (HTTP, API compatible OpenAI), p. ej. Phi-3 Mini Instruct (GGUF). **No** se ejecuta dentro de Docker.
- **Lenguaje**: Python 3.11

## 📋 Requisitos Previos

1. **Docker y Docker Compose** instalados
2. **Servidor llama.cpp** ejecutándose en el host (puerto 8080 por defecto)
3. **Modelo GGUF** cargado en el servidor (p. ej. Phi-3 Mini Instruct)

## 📖 Instalación y Uso Completo

### Paso 1: Servidor llama.cpp en el host

El backend LLM corre **fuera de Docker**. Debes tener ya:

- **llama.cpp** compilado con servidor HTTP (o un binario que exponga la API tipo OpenAI).
- **Modelo en GGUF** descargado (p. ej. Phi-3 Mini Instruct).

Inicia el servidor manualmente en el host, por ejemplo:

```bash
# Ejemplo: servidor en el puerto 8080
./server -m /ruta/al/modelo.gguf --port 8080
```

Verificar que el servidor responde:

```bash
curl http://localhost:8080/health
# Esperado: {"status":"ok"}
```

La app asume que el endpoint de chat está en `http://host.docker.internal:8080/v1/chat/completions` (configurable con `LLM_BASE_URL` y `LLM_MODEL`).

### Paso 2: Procesar los Datos

Los datos ya están disponibles localmente. Ejecuta el script de procesamiento para generar el JSON unificado:

```bash
python3 scripts/process_data.py
```

Este script:
- Lee `data/es_rvr/es_rvr.json` (Reina-Valera 1960)
- Lee los archivos TXT de `data/greek_nt/` (griego koiné)
- Genera `data/nt_verses.json` con 7,925 versículos normalizados

**Nota**: Si ya ejecutaste este paso, puedes saltar al siguiente.

### Paso 3: Construir y Levantar los Contenedores

```bash
# Construir la imagen
docker-compose build

# Levantar el contenedor
docker-compose up -d
```

### Paso 4: Ingerir los Datos en ChromaDB

Ejecutar el script de ingesta dentro del contenedor:

```bash
docker-compose exec ntlanguagelab python scripts/ingest.py
```

Este proceso:
- Lee `data/nt_verses.json` (7,925 versículos)
- Genera embeddings con sentence-transformers
- Almacena en ChromaDB (persistente en `./chroma_db`)
- Tarda unos minutos (descarga el modelo de embeddings la primera vez)

**Nota**: La primera ejecución descargará el modelo de embeddings (~420MB). Las siguientes serán más rápidas.

### Paso 5: Acceder a la Aplicación

Abre tu navegador en:

```
http://localhost:8501
```

## 📁 Estructura del Proyecto

```
NTLanguageLab/
├── app/
│   ├── main.py              # Streamlit
│   ├── rag.py               # RAG + ChromaDB
│   └── llm_client.py        # Cliente HTTP llama.cpp (OpenAI API)
├── scripts/
│   ├── process_data.py      # RVR + griego → nt_verses.json
│   └── ingest.py            # nt_verses.json → ChromaDB
├── data/
│   ├── es_rvr/              # Reina-Valera 1960
│   ├── greek_nt/            # Griego koiné (MorphGNT)
│   └── nt_verses.json       # Generado por process_data.py
├── chroma_db/               # ChromaDB (creado al ejecutar ingest)
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── README.md
└── ARCHITECTURE.md
```

## 🔧 Configuración

### Variables de Entorno

El proyecto usa las siguientes variables (configuradas en `docker-compose.yml`):

- `LLM_BASE_URL`: URL base del servidor llama.cpp (por defecto: `http://host.docker.internal:8080`). Si está vacía o no definida, la app corre en modo solo RAG (sin comparación con IA).
- `LLM_MODEL`: Nombre del modelo en el servidor (por defecto: `Phi-3 Mini Instruct`)
- `CHROMA_DB_PATH`: Ruta donde se almacena ChromaDB (por defecto: `/app/chroma_db`)
- `DISABLE_LLM`: Si es `1`, `true` o `yes`, el LLM no se usa (modo solo RAG).

### Volúmenes Docker

- `./chroma_db` → `/app/chroma_db`: Persistencia de ChromaDB
- `./data` → `/app/data`: Datos del Nuevo Testamento

## 🎮 Uso de la Aplicación

Hay **dos modos de búsqueda** (pestañas en la app):

- **Por referencia:** libro, capítulo y versículo (ej. Juan 3:16). Muestra griego + español y, si el LLM está configurado, la comparación lingüística se genera al instante.
- **Por concepto:** escribe una frase o concepto (ej. *amor de Dios al mundo*). La búsqueda semántica devuelve versículos relacionados; eliges uno para ver detalle y, opcionalmente, generar la comparación con IA.

### Ejemplo: Buscar Juan 3:16

1. **Abre la aplicación**: `http://localhost:8501`
2. **Selecciona**:
   - Libro: "Juan"
   - Capítulo: `3`
   - Versículo: `16`
3. **Haz clic** en "🔎 Buscar y Comparar"
4. **Verás**:
   - **Griego koiné**: `Οὕτως γὰρ ἠγάπησεν ὁ θεὸς τὸν κόσμον, ὥστε τὸν υἱὸν τὸν μονογενῆ ἔδωκεν...`
   - **Reina-Valera 1960**: `Porque de tal manera amó Dios al mundo, que ha dado a su Hijo unigénito...`
   - **Comparación lingüística**: Análisis detallado generado por IA

### Otros Ejemplos

- **Mateo 1:1**: Libro de la genealogía
- **Romanos 8:28**: Todas las cosas ayudan a bien
- **1 Corintios 13:4**: El amor es sufrido

## 🔍 Características

- ✅ **Dos búsquedas:** por referencia (libro/cap/vers) y por concepto (semántica).
- ✅ RAG estricto: Solo usa el versículo recuperado para la comparación
- ✅ Comparación lingüística (no teológica)
- ✅ Citas explícitas de libro, capítulo y versículo
- ✅ Identificación clara del idioma de cada texto
- ✅ Notas gramaticales cuando aplica
- ✅ Sin dependencias de APIs externas

## 🛠️ Comandos Útiles

```bash
# Ver logs del contenedor
docker-compose logs -f

# Detener el contenedor
docker-compose down

# Reconstruir después de cambios
docker-compose up --build -d

# Acceder al shell del contenedor
docker-compose exec ntlanguagelab bash

# Verificar que el servidor llama.cpp responde
curl http://localhost:8080/health
```

## 📝 Notas Importantes

1. **El servidor llama.cpp debe estar corriendo en el host** antes de usar la comparación con IA
2. **Los datos no están incluidos** - debes proporcionar tu propio archivo JSON
3. **El modelo GGUF debe estar cargado** en el servidor (p. ej. Phi-3 Mini Instruct)
4. **ChromaDB se crea automáticamente** en `./chroma_db` al ejecutar la ingesta

## 🐛 Solución de Problemas

### Error: "No se puede conectar al LLM"

- Verifica que el servidor llama.cpp esté corriendo: `curl http://localhost:8080/health`
- Comprueba `LLM_BASE_URL` y `LLM_MODEL` (variables de entorno o `docker-compose.yml`)
- En Linux, puede ser necesario ajustar `extra_hosts` en `docker-compose.yml`

### Error: "No se encontró el versículo"

- Verifica que los datos hayan sido ingeridos correctamente
- Revisa el formato del archivo JSON
- Verifica que el libro, capítulo y versículo existan en tus datos

### ChromaDB no persiste

- Verifica que el volumen `./chroma_db` tenga permisos de escritura
- Revisa los logs: `docker-compose logs ntlanguagelab`

## 🚀 Publicar el proyecto (GitHub)

1. **Crear un repositorio** en GitHub (nuevo, vacío, público o privado).
2. **No subas** `chroma_db/` ni archivos pesados: están en `.gitignore`. Los datos (`data/`) sí pueden subirse si no son enormes; si prefieres no versionarlos, añade `data/nt_verses.json` (y opcionalmente `data/es_rvr/`, `data/greek_nt/`) a `.gitignore`.
3. **En la raíz del proyecto** (donde está `docker-compose.yml`), ejecuta:
   ```bash
   git init
   git add .
   git commit -m "Initial commit: NT Language Lab"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/NTLanguageLab.git
   git push -u origin main
   ```
   (Sustituye `TU_USUARIO/NTLanguageLab` por tu usuario y nombre del repo.)
4. **Opcional:** Añade una licencia (p. ej. MIT) creando `LICENSE` y un breve `CONTRIBUTING.md` si quieres aceptar contribuciones.
5. Quien clone el repo podrá seguir el README: clonar, `docker-compose build`, `docker-compose up -d`, ejecutar ingest y usar la app. Para modo solo RAG (sin LLM), puede poner `DISABLE_LLM=1` en el entorno o en `docker-compose.yml`.

## 📄 Licencia

Este proyecto es de código abierto. Los datos del Nuevo Testamento deben obtenerse de fuentes públicas con las licencias correspondientes.
