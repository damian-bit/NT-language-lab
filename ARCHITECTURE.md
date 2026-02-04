# Arquitectura NT Language Lab

## Vista del sistema

```mermaid
flowchart TB
    subgraph HOST["Host"]
        LLM["llama.cpp\n:8080\nPhi-3 GGUF"]
    end

    subgraph DOCKER["Contenedor"]
        UI["Streamlit\nmain.py :8501"]
        RAG["NTRAG\nrag.py"]
        HTTP["LLMClient\nllm_client.py"]
        DB[(ChromaDB)]
    end

    subgraph VOL["Volúmenes"]
        DATA["data/"]
        CHROMA["chroma_db/"]
    end

    User -->|localhost:8501| UI
    UI --> RAG
    UI --> HTTP
    RAG --> DB
    HTTP -->|/v1/chat/completions| LLM
    DB <-.-> CHROMA
    RAG <-.- DATA
```

- **Host**: llama.cpp sirve el modelo GGUF (puerto 8080, API OpenAI). No corre en Docker.
- **Contenedor**: Streamlit (UI), NTRAG (búsqueda por referencia y por concepto/semántica), LLMClient (HTTP al LLM), ChromaDB (lectura en runtime).
- **Volúmenes**: `data/` (fuentes + nt_verses.json), `chroma_db/` (persistencia).

---

## Flujo de uso

**Por referencia:** Usuario elige libro/cap/vers → `search_verse()` → ChromaDB get(ids) → un versículo → (opcional) LLM comparación.

**Por concepto:** Usuario escribe frase → `search_by_concept()` (embedding + ChromaDB query por similitud) → lista de versículos → usuario elige uno → mismo detalle y opcional LLM.

```mermaid
sequenceDiagram
    actor U as Usuario
    participant UI as Streamlit
    participant RAG as NTRAG
    participant DB as ChromaDB
    participant LLM as LLMClient
    participant SVC as llama.cpp

    U->>UI: Libro, cap, vers O frase concepto
    alt Por referencia
        UI->>RAG: search_verse(libro, cap, vers)
        RAG->>DB: get(ids)
    else Por concepto
        UI->>RAG: search_by_concept(query)
        RAG->>RAG: embed(query)
        RAG->>DB: query(embedding)
        DB-->>RAG: ids + metadatas
        RAG->>DB: get(ids) por cada versículo
    end
    DB-->>RAG: griego, español
    RAG-->>UI: verse_data (o lista)
    UI->>LLM: generate(prompt, context) [opcional]
    LLM->>SVC: POST /v1/chat/completions
    SVC-->>LLM: análisis
    UI-->>U: textos + análisis
```

---

## Pipeline de datos (una vez)

```mermaid
flowchart LR
    RVR["es_rvr.json"] --> P["process_data.py"]
    G["greek_nt/*.txt"] --> P
    P --> J["nt_verses.json"]
    J --> I["ingest.py"]
    I -->|embeddings + add_verse| DB[(ChromaDB)]
```

- **process_data.py**: Normaliza RVR + griego → `nt_verses.json`.
- **ingest.py**: Carga NTRAG (modelo de embeddings), lee `nt_verses.json`, escribe en ChromaDB. La app no ejecuta estos scripts.

---

## Stack

| Capa      | Tecnología                    |
|-----------|-------------------------------|
| UI        | Streamlit                     |
| Búsqueda  | ChromaDB (por ID y por similitud) |
| Embeddings| sentence-transformers (ingest + búsqueda por concepto) |
| LLM       | llama.cpp (host, :8080)       |
| Datos     | JSON → nt_verses.json         |
