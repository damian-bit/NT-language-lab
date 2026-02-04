"""
Módulo RAG para recuperar versículos del Nuevo Testamento.
Usa ChromaDB como vector store con sentence-transformers para embeddings.
"""
import os
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from typing import Optional, List, Dict, Tuple


class NTRAG:
    """Sistema RAG para recuperar versículos del Nuevo Testamento."""
    
    _embedding_model = None  # Carga perezosa: solo se usa en ingest, no en búsqueda
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Inicializa el sistema RAG.
        
        Args:
            db_path: Ruta donde se almacena ChromaDB. Por defecto usa variable
                     de entorno o ./chroma_db
        """
        self.db_path = db_path or os.getenv('CHROMA_DB_PATH', './chroma_db')
        
        # ChromaDB se inicializa siempre (rápido)
        self.client = chromadb.PersistentClient(
            path=self.db_path,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self.collection = self.client.get_or_create_collection(
            name="nuevo_testamento",
            metadata={"description": "Versículos del Nuevo Testamento en griego y español"}
        )
    
    def _get_embedding_model(self) -> SentenceTransformer:
        """Carga el modelo de embeddings solo cuando se necesita (p. ej. en ingest)."""
        if NTRAG._embedding_model is None:
            NTRAG._embedding_model = SentenceTransformer('paraphrase-multilingual-MiniLM-L12-v2')
        return NTRAG._embedding_model
    
    def search_verse(
        self, 
        libro: str, 
        capitulo: int, 
        versiculo: int
    ) -> Optional[Dict[str, str]]:
        """
        Busca un versículo específico por libro, capítulo y versículo.
        
        Args:
            libro: Nombre del libro (ej: "Mateo", "Juan")
            capitulo: Número de capítulo
            versiculo: Número de versículo
            
        Returns:
            Diccionario con 'griego' y 'espanol' si se encuentra, None si no
        """
        # Buscar ambos idiomas usando IDs predecibles
        id_griego = f"{libro}_{capitulo}_{versiculo}_griego"
        id_espanol = f"{libro}_{capitulo}_{versiculo}_espanol"
        
        try:
            # Intentar obtener ambos documentos por ID
            results = self.collection.get(
                ids=[id_griego, id_espanol]
            )
            
            if results and len(results['ids']) >= 2:
                # Ambos documentos encontrados
                griego_idx = results['ids'].index(id_griego) if id_griego in results['ids'] else None
                espanol_idx = results['ids'].index(id_espanol) if id_espanol in results['ids'] else None
                
                texto_griego = results['documents'][griego_idx] if griego_idx is not None else ""
                texto_espanol = results['documents'][espanol_idx] if espanol_idx is not None else ""
                
                if texto_griego and texto_espanol:
                    return {
                        'griego': texto_griego,
                        'espanol': texto_espanol,
                        'libro': libro,
                        'capitulo': capitulo,
                        'versiculo': versiculo
                    }
            
            # Fallback: buscar por metadatos si no se encontró por ID
            # ChromaDB puede requerir diferentes formatos según la versión
            try:
                results = self.collection.get(
                    where={
                        "$and": [
                            {"libro": {"$eq": str(libro)}},
                            {"capitulo": {"$eq": int(capitulo)}},
                            {"versiculo": {"$eq": int(versiculo)}}
                        ]
                    }
                )
            except:
                # Formato alternativo para versiones antiguas de ChromaDB
                try:
                    results = self.collection.get(
                        where={
                            "$and": [
                                {"libro": libro},
                                {"capitulo": capitulo},
                                {"versiculo": versiculo}
                            ]
                        }
                    )
                except:
                    # Último recurso: obtener todos y filtrar
                    all_results = self.collection.get()
                    if all_results and all_results['ids']:
                        matching_ids = []
                        for idx, metadata in enumerate(all_results['metadatas']):
                            if (metadata.get('libro') == str(libro) and
                                metadata.get('capitulo') == int(capitulo) and
                                metadata.get('versiculo') == int(versiculo)):
                                matching_ids.append(all_results['ids'][idx])
                        
                        if matching_ids:
                            results = self.collection.get(ids=matching_ids)
                        else:
                            results = None
                    else:
                        results = None
            
            if results and len(results['ids']) >= 2:
                # Separar griego y español
                texto_griego = ""
                texto_espanol = ""
                
                for idx, metadata in enumerate(results['metadatas']):
                    if metadata.get('idioma') == 'griego':
                        texto_griego = results['documents'][idx]
                    elif metadata.get('idioma') == 'espanol':
                        texto_espanol = results['documents'][idx]
                
                if texto_griego and texto_espanol:
                    return {
                        'griego': texto_griego,
                        'espanol': texto_espanol,
                        'libro': libro,
                        'capitulo': capitulo,
                        'versiculo': versiculo
                    }
        except Exception as e:
            print(f"Error buscando versículo: {e}")
        
        return None

    def search_by_concept(self, query: str, top_k: int = 10) -> List[Dict]:
        """
        Busca versículos por similitud semántica a una frase o concepto.

        Args:
            query: Frase o concepto en español (ej: "amor de Dios al mundo").
            top_k: Número máximo de versículos a devolver.

        Returns:
            Lista de diccionarios con la misma estructura que search_verse
            (griego, espanol, libro, capitulo, versiculo), ordenados por relevancia.
        """
        if not query or not query.strip():
            return []
        try:
            model = self._get_embedding_model()
            query_embedding = model.encode(query.strip()).tolist()
        except Exception as e:
            print(f"Error generando embedding para búsqueda semántica: {e}")
            return []
        try:
            n_results = min(max(top_k * 2, 20), self.collection.count())
            if n_results < 1:
                return []
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                include=["metadatas"]
            )
        except Exception as e:
            print(f"Error en query ChromaDB (semántica): {e}")
            return []
        metadatas = (results.get("metadatas") or [[]])[0] or []
        seen = set()
        unique_verses = []
        for meta in metadatas:
            if not meta:
                continue
            libro = meta.get("libro")
            cap = meta.get("capitulo")
            vers = meta.get("versiculo")
            if libro is None or cap is None or vers is None:
                continue
            key = (str(libro), int(cap), int(vers))
            if key in seen:
                continue
            seen.add(key)
            unique_verses.append((str(libro), int(cap), int(vers)))
            if len(unique_verses) >= top_k:
                break
        out = []
        for libro, cap, vers in unique_verses:
            v = self.search_verse(libro, cap, vers)
            if v:
                out.append(v)
        return out

    def format_context(self, verse_data: Dict[str, str]) -> str:
        """
        Formatea los datos del versículo como contexto para el LLM.
        
        Args:
            verse_data: Diccionario con datos del versículo
            
        Returns:
            String formateado con el contexto
        """
        return f"""LIBRO: {verse_data['libro']}
CAPÍTULO: {verse_data['capitulo']}
VERSÍCULO: {verse_data['versiculo']}

TEXTO ORIGINAL (Griego Koiné):
{verse_data['griego']}

TRADUCCIÓN (Reina-Valera 1960):
{verse_data['espanol']}"""
    
    def add_verse(
        self,
        libro: str,
        capitulo: int,
        versiculo: int,
        texto_griego: str,
        texto_espanol: str
    ):
        """
        Añade un versículo a la base de datos.
        
        Args:
            libro: Nombre del libro
            capitulo: Número de capítulo
            versiculo: Número de versículo
            texto_griego: Texto en griego koiné
            texto_espanol: Texto en español (Reina-Valera 1960)
        """
        # Generar embeddings (carga el modelo solo aquí, en el script de ingesta)
        model = self._get_embedding_model()
        embedding_griego = model.encode(texto_griego).tolist()
        embedding_espanol = model.encode(texto_espanol).tolist()
        
        # IDs únicos
        id_griego = f"{libro}_{capitulo}_{versiculo}_griego"
        id_espanol = f"{libro}_{capitulo}_{versiculo}_espanol"
        
        # Metadatos (ChromaDB requiere que los números sean números, no strings)
        metadata_griego = {
            "libro": str(libro),
            "capitulo": int(capitulo),
            "versiculo": int(versiculo),
            "idioma": "griego"
        }
        
        metadata_espanol = {
            "libro": str(libro),
            "capitulo": int(capitulo),
            "versiculo": int(versiculo),
            "idioma": "espanol"
        }
        
        # Añadir a la colección
        self.collection.add(
            ids=[id_griego],
            embeddings=[embedding_griego],
            documents=[texto_griego],
            metadatas=[metadata_griego]
        )
        
        self.collection.add(
            ids=[id_espanol],
            embeddings=[embedding_espanol],
            documents=[texto_espanol],
            metadatas=[metadata_espanol]
        )
