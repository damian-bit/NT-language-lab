"""
Aplicación Streamlit para comparar traducciones del Nuevo Testamento.
"""
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importaciones
root_dir = Path(__file__).parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

import streamlit as st
from app.rag import NTRAG
from app.llm_client import LLMClient


def _llm_disabled() -> bool:
    """True si el LLM debe quedar deshabilitado (modo demo / solo RAG)."""
    raw = os.environ.get("DISABLE_LLM", "").strip().lower()
    if raw in ("1", "true", "yes", "on"):
        return True
    if not os.environ.get("LLM_BASE_URL", "").strip():
        return True
    return False


# Configuración de la página
st.set_page_config(
    page_title="NT Language Lab",
    page_icon="📖",
    layout="wide"
)

# Título principal
st.title("📖 NT Language Lab")
st.markdown("### Comparador de Traducciones del Nuevo Testamento")
st.markdown("Comparación lingüística entre el texto original en griego koiné y la traducción Reina-Valera 1960")

# Inicializar componentes (con cache)
@st.cache_resource
def init_rag():
    """Inicializa el sistema RAG."""
    return NTRAG()

@st.cache_resource
def init_llm():
    """Inicializa el cliente del LLM (llama.cpp vía HTTP)."""
    return LLMClient()

# Inicializar componentes (puede tardar la primera vez)
try:
    rag = init_rag()
except Exception as e:
    st.error(f"❌ Error inicializando RAG: {e}")
    st.stop()

if _llm_disabled():
    llm = None
else:
    try:
        llm = init_llm()
    except Exception as e:
        st.warning(f"⚠️ Error inicializando LLM: {e}")
        llm = None

# Sidebar con información
with st.sidebar:
    st.header("ℹ️ Información")
    st.markdown("""
    **Dos modos de búsqueda:**
    - **Por referencia:** libro, capítulo y versículo (ej. Juan 3:16).
    - **Por concepto:** escribe una frase (ej. *amor de Dios al mundo*) y verás versículos relacionados.
    
    En ambos casos se muestra griego koiné y Reina-Valera 1960. La comparación con IA (si está configurada) es opcional en búsqueda por concepto.
    """)
    
    st.header("🔧 Estado del Sistema")
    if llm is None:
        st.warning("**Comparación con IA:** Inactiva")
        st.caption("Modo solo RAG (LLM no disponible o deshabilitado)")
    else:
        st.success("**Comparación con IA:** Activa")
        st.caption("llama.cpp configurado")
    try:
        count = rag.collection.count()
        st.info(f"📚 Versículos indexados: {count // 2}")
    except Exception:
        st.warning("⚠️ ChromaDB no inicializado")

# Formulario principal: dos modos de búsqueda
st.header("🔍 Buscar Versículo")

tab_ref, tab_concept = st.tabs(["Por referencia", "Por concepto"])


def _show_verse_detail(verse_data, show_llm=True, auto_llm=False):
    """Muestra detalle de un versículo (textos + opcional comparación LLM)."""
    libro = verse_data["libro"]
    cap = verse_data["capitulo"]
    vers = verse_data["versiculo"]
    st.success(f"✅ {libro} {cap}:{vers}")
    st.header("📝 Textos")
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🇬🇷 Griego Koiné (Original)")
        st.markdown(f"**{libro} {cap}:{vers}**")
        st.text_area("Texto griego", value=verse_data["griego"], height=150, disabled=True, key=f"g_{libro}_{cap}_{vers}")
    with c2:
        st.subheader("🇪🇸 Reina-Valera 1960")
        st.markdown(f"**{libro} {cap}:{vers}**")
        st.text_area("Texto español", value=verse_data["espanol"], height=150, disabled=True, key=f"e_{libro}_{cap}_{vers}")
    if not show_llm:
        return
    st.header("🔬 Comparación Lingüística")
    if llm is None:
        st.warning("⚠️ El LLM no está disponible. No se puede generar la comparación lingüística.")
        st.info("💡 En la versión local con llama.cpp puedes activar la comparación con IA.")
    else:
        if auto_llm:
            with st.spinner("Generando comparación con IA..."):
                context = rag.format_context(verse_data)
                prompt = """Realiza una comparación lingüística entre el texto griego original y la traducción al español.
Analiza: 1) Palabras clave y su traducción 2) Matices de significado 3) Estructura gramatical 4) Notas gramaticales relevantes.
Mantén la respuesta concisa y enfocada en aspectos lingüísticos."""
                comparacion = llm.generate(prompt, context)
                st.markdown("### Análisis")
                st.markdown(comparacion)
        else:
            if st.button("Generar comparación con IA", key=f"gen_{libro}_{cap}_{vers}"):
                with st.spinner("Generando comparación..."):
                    context = rag.format_context(verse_data)
                    prompt = """Realiza una comparación lingüística entre el texto griego original y la traducción al español.
Analiza: 1) Palabras clave y su traducción 2) Matices de significado 3) Estructura gramatical 4) Notas gramaticales relevantes.
Mantén la respuesta concisa y enfocada en aspectos lingüísticos."""
                    comparacion = llm.generate(prompt, context)
                    st.markdown("### Análisis")
                    st.markdown(comparacion)


with tab_ref:
    st.markdown("Busca por **libro, capítulo y versículo**.")
    col1, col2, col3 = st.columns(3)
    with col1:
        libros_nt = [
            "Mateo", "Marcos", "Lucas", "Juan",
            "Hechos", "Romanos", "1 Corintios", "2 Corintios",
            "Gálatas", "Efesios", "Filipenses", "Colosenses",
            "1 Tesalonicenses", "2 Tesalonicenses", "1 Timoteo", "2 Timoteo",
            "Tito", "Filemón", "Hebreos", "Santiago",
            "1 Pedro", "2 Pedro", "1 Juan", "2 Juan", "3 Juan",
            "Judas", "Apocalipsis"
        ]
        libro = st.selectbox("Libro", libros_nt, key="ref_libro")
    with col2:
        capitulo = st.number_input("Capítulo", min_value=1, max_value=150, value=1, step=1, key="ref_cap")
    with col3:
        versiculo = st.number_input("Versículo", min_value=1, max_value=200, value=1, step=1, key="ref_vers")
    if st.button("🔎 Buscar y Comparar", type="primary", key="btn_ref"):
        with st.spinner("Buscando versículo..."):
            verse_data = rag.search_verse(libro, capitulo, versiculo)
            if verse_data:
                _show_verse_detail(verse_data, show_llm=True, auto_llm=True)
            else:
                st.error(f"❌ No se encontró el versículo {libro} {capitulo}:{versiculo}")
                st.info("💡 Asegúrate de que los datos hayan sido ingeridos correctamente.")

with tab_concept:
    st.markdown("Busca por **concepto o frase** (ej: *amor de Dios al mundo*). La primera vez puede tardar unos segundos en cargar el modelo.")
    concept_query = st.text_input("Escribe un concepto o frase", placeholder="ej: amor de Dios al mundo", key="concept_query")
    if st.button("🔎 Buscar por concepto", type="primary", key="btn_concept"):
        if not (concept_query and concept_query.strip()):
            st.warning("Escribe una frase o concepto para buscar.")
        else:
            with st.spinner("Buscando por concepto… La primera vez puede tardar ~1 min (carga del modelo de búsqueda semántica)."):
                verses = rag.search_by_concept(concept_query.strip(), top_k=10)
            if not verses:
                st.error("No se encontraron versículos similares.")
                st.info("Prueba otra frase o asegúrate de que la ingesta se haya ejecutado.")
            else:
                st.success(f"Se encontraron {len(verses)} versículo(s). Elige uno para ver detalle.")
                for i, v in enumerate(verses):
                    ref = f"{v['libro']} {v['capitulo']}:{v['versiculo']}"
                    preview = (v["espanol"][:60] + "...") if len(v["espanol"]) > 60 else v["espanol"]
                    with st.expander(f"**{ref}** — {preview}"):
                        _show_verse_detail(v, show_llm=True, auto_llm=False)

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: gray;'>"
    "NT Language Lab - Comparación Lingüística del Nuevo Testamento<br>"
    "llama.cpp (Phi-3 Mini) + ChromaDB + Sentence Transformers"
    "</div>",
    unsafe_allow_html=True
)
