"""
Script para ingerir datos del Nuevo Testamento en ChromaDB.
Lee archivos JSON con los versículos en griego y español.
"""
import json
import os
import sys
from pathlib import Path

# Añadir el directorio raíz al path para importar módulos
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.rag import NTRAG


def load_verses_from_json(json_path: str) -> list:
    """
    Carga versículos desde un archivo JSON.
    
    Formato esperado:
    [
        {
            "libro": "Mateo",
            "capitulo": 1,
            "versiculo": 1,
            "griego": "Βίβλος γενέσεως...",
            "espanol": "Libro de la genealogía..."
        },
        ...
    ]
    
    Args:
        json_path: Ruta al archivo JSON
        
    Returns:
        Lista de diccionarios con los versículos
    """
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def ingest_data(data_path: str = "./data/nt_verses.json"):
    """
    Ingiere datos del Nuevo Testamento en ChromaDB.
    
    Args:
        data_path: Ruta al archivo JSON con los versículos
    """
    print("🚀 Iniciando ingesta de datos del Nuevo Testamento...")
    
    # Verificar que existe el archivo
    if not os.path.exists(data_path):
        print(f"❌ Error: No se encuentra el archivo {data_path}")
        print("💡 Crea un archivo JSON con el formato:")
        print("""
[
    {
        "libro": "Mateo",
        "capitulo": 1,
        "versiculo": 1,
        "griego": "Texto en griego koiné...",
        "espanol": "Texto en Reina-Valera 1960..."
    }
]
        """)
        return
    
    # Inicializar RAG
    print("📚 Inicializando ChromaDB...")
    rag = NTRAG()
    
    # Cargar datos
    print(f"📖 Cargando datos desde {data_path}...")
    verses = load_verses_from_json(data_path)
    
    print(f"✅ Cargados {len(verses)} versículos")
    
    # Ingerir versículos
    print("💾 Ingeriendo versículos en ChromaDB...")
    for i, verse in enumerate(verses, 1):
        try:
            # Asegurar que capitulo y versiculo sean enteros
            capitulo = int(verse['capitulo'])
            versiculo = int(verse['versiculo'])
            
            rag.add_verse(
                libro=str(verse['libro']),
                capitulo=capitulo,
                versiculo=versiculo,
                texto_griego=str(verse['griego']),
                texto_espanol=str(verse['espanol'])
            )
            
            if i % 100 == 0:
                print(f"  Procesados {i}/{len(verses)} versículos...")
        except KeyError as e:
            print(f"⚠️ Error: Falta campo requerido en versículo {i}: {e}")
        except ValueError as e:
            print(f"⚠️ Error: Tipo de dato inválido en versículo {i}: {e}")
        except Exception as e:
            print(f"⚠️ Error procesando {verse.get('libro', '?')} {verse.get('capitulo', '?')}:{verse.get('versiculo', '?')}: {e}")
    
    # Verificar ingesta
    count = rag.collection.count()
    print(f"\n✅ Ingesta completada!")
    print(f"📊 Total de documentos en ChromaDB: {count}")
    print(f"📖 Versículos únicos: {count // 2}")


if __name__ == "__main__":
    # Permitir especificar ruta como argumento
    data_path = sys.argv[1] if len(sys.argv) > 1 else "./data/nt_verses.json"
    ingest_data(data_path)
