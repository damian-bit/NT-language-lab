"""
Script para procesar los datos del Nuevo Testamento desde las fuentes originales
y generar el archivo JSON unificado para la ingesta.

Fuentes:
1. Reina-Valera 1960: /data/es_rvr/es_rvr.json
2. Griego koiné: /data/greek_nt/*.txt
"""
import json
import os
from pathlib import Path
from typing import Dict, List


# Mapeo de índices del JSON a nombres de libros del NT (índices 39-65)
NT_BOOKS_JSON_INDICES = {
    39: ("Mateo", "mt"),
    40: ("Marcos", "mk"),
    41: ("Lucas", "lk"),
    42: ("Juan", "jn"),
    43: ("Hechos", "ac"),
    44: ("Romanos", "ro"),
    45: ("1 Corintios", "1co"),
    46: ("2 Corintios", "2co"),
    47: ("Gálatas", "ga"),
    48: ("Efesios", "eph"),
    49: ("Filipenses", "php"),
    50: ("Colosenses", "col"),
    51: ("1 Tesalonicenses", "1th"),
    52: ("2 Tesalonicenses", "2th"),
    53: ("1 Timoteo", "1ti"),
    54: ("2 Timoteo", "2ti"),
    55: ("Tito", "tit"),
    56: ("Filemón", "phm"),
    57: ("Hebreos", "heb"),
    58: ("Santiago", "jas"),
    59: ("1 Pedro", "1pe"),
    60: ("2 Pedro", "2pe"),
    61: ("1 Juan", "1jn"),
    62: ("2 Juan", "2jn"),
    63: ("3 Juan", "3jn"),
    64: ("Judas", "jud"),
    65: ("Apocalipsis", "re"),
}

# Mapeo de archivos TXT a nombres de libros
GREEK_FILE_MAPPING = {
    "61-Mt-morphgnt.txt": "Mateo",
    "62-Mk-morphgnt.txt": "Marcos",
    "63-Lk-morphgnt.txt": "Lucas",
    "64-Jn-morphgnt.txt": "Juan",
    "65-Ac-morphgnt.txt": "Hechos",
    "66-Ro-morphgnt.txt": "Romanos",
    "67-1Co-morphgnt.txt": "1 Corintios",
    "68-2Co-morphgnt.txt": "2 Corintios",
    "69-Ga-morphgnt.txt": "Gálatas",
    "70-Eph-morphgnt.txt": "Efesios",
    "71-Php-morphgnt.txt": "Filipenses",
    "72-Col-morphgnt.txt": "Colosenses",
    "73-1Th-morphgnt.txt": "1 Tesalonicenses",
    "74-2Th-morphgnt.txt": "2 Tesalonicenses",
    "75-1Ti-morphgnt.txt": "1 Timoteo",
    "76-2Ti-morphgnt.txt": "2 Timoteo",
    "77-Tit-morphgnt.txt": "Tito",
    "78-Phm-morphgnt.txt": "Filemón",
    "79-Heb-morphgnt.txt": "Hebreos",
    "80-Jas-morphgnt.txt": "Santiago",
    "81-1Pe-morphgnt.txt": "1 Pedro",
    "82-2Pe-morphgnt.txt": "2 Pedro",
    "83-1Jn-morphgnt.txt": "1 Juan",
    "84-2Jn-morphgnt.txt": "2 Juan",
    "85-3Jn-morphgnt.txt": "3 Juan",
    "86-Jud-morphgnt.txt": "Judas",
    "87-Re-morphgnt.txt": "Apocalipsis",
}


def load_spanish_nt(json_path: str) -> Dict[str, Dict[int, Dict[int, str]]]:
    """Carga el Nuevo Testamento en español desde el JSON."""
    print(f"📖 Cargando Reina-Valera 1960 desde {json_path}...")
    
    with open(json_path, 'r', encoding='utf-8-sig') as f:
        bible_data = json.load(f)
    
    spanish_nt = {}
    
    for json_idx, (book_name, abbrev) in NT_BOOKS_JSON_INDICES.items():
        if json_idx < len(bible_data):
            book_data = bible_data[json_idx]
            chapters = book_data.get('chapters', [])
            
            spanish_nt[book_name] = {}
            
            for chapter_num, chapter_verses in enumerate(chapters, start=1):
                spanish_nt[book_name][chapter_num] = {}
                for verse_num, verse_text in enumerate(chapter_verses, start=1):
                    verse_text = verse_text.strip() if verse_text else ""
                    spanish_nt[book_name][chapter_num][verse_num] = verse_text
            
            print(f"  ✅ {book_name}: {len(chapters)} capítulos")
    
    return spanish_nt


def load_greek_nt(greek_dir: str) -> Dict[str, Dict[int, Dict[int, str]]]:
    """Carga el Nuevo Testamento en griego desde los archivos TXT."""
    print(f"📖 Cargando textos griegos desde {greek_dir}...")
    
    greek_nt = {}
    
    for filename, book_name in GREEK_FILE_MAPPING.items():
        filepath = os.path.join(greek_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"  ⚠️ Archivo no encontrado: {filename}")
            continue
        
        greek_nt[book_name] = {}
        current_chapter = 0
        current_verse = 0
        verse_words = []
        
        with open(filepath, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                
                parts = line.split(None, 3)
                if len(parts) < 4:
                    continue
                
                code = parts[0]
                if len(code) != 6 or not code.isdigit():
                    continue
                
                book_code = int(code[0:2])
                chapter = int(code[2:4])
                verse = int(code[4:6])
                
                text_parts = parts[3].split()
                if text_parts:
                    greek_word = text_parts[0]
                else:
                    continue
                
                if chapter != current_chapter or verse != current_verse:
                    if current_chapter > 0 and current_verse > 0:
                        if current_chapter not in greek_nt[book_name]:
                            greek_nt[book_name][current_chapter] = {}
                        verse_text = " ".join(verse_words).strip()
                        greek_nt[book_name][current_chapter][current_verse] = verse_text
                    
                    current_chapter = chapter
                    current_verse = verse
                    verse_words = [greek_word]
                else:
                    verse_words.append(greek_word)
        
        if current_chapter > 0 and current_verse > 0:
            if current_chapter not in greek_nt[book_name]:
                greek_nt[book_name][current_chapter] = {}
            verse_text = " ".join(verse_words).strip()
            greek_nt[book_name][current_chapter][current_verse] = verse_text
        
        verse_count = sum(len(chapters) for chapters in greek_nt[book_name].values())
        print(f"  ✅ {book_name}: {len(greek_nt[book_name])} capítulos, {verse_count} versículos")
    
    return greek_nt


def merge_data(
    spanish_nt: Dict[str, Dict[int, Dict[int, str]]],
    greek_nt: Dict[str, Dict[int, Dict[int, str]]]
) -> List[Dict]:
    """Combina los datos en español y griego."""
    print("\n🔄 Combinando datos...")
    
    merged = []
    
    all_books = set(spanish_nt.keys()) | set(greek_nt.keys())
    
    for book_name in sorted(all_books):
        if book_name not in spanish_nt or book_name not in greek_nt:
            continue
        
        spanish_book = spanish_nt[book_name]
        greek_book = greek_nt[book_name]
        
        all_chapters = set(spanish_book.keys()) | set(greek_book.keys())
        
        for chapter in sorted(all_chapters):
            if chapter not in spanish_book or chapter not in greek_book:
                continue
            
            spanish_chapter = spanish_book[chapter]
            greek_chapter = greek_book[chapter]
            
            all_verses = set(spanish_chapter.keys()) | set(greek_chapter.keys())
            
            for verse in sorted(all_verses):
                if verse not in spanish_chapter or verse not in greek_chapter:
                    continue
                
                merged.append({
                    "libro": book_name,
                    "capitulo": chapter,
                    "versiculo": verse,
                    "griego": greek_chapter[verse],
                    "espanol": spanish_chapter[verse]
                })
    
    return merged


def main():
    """Función principal."""
    base_dir = Path(__file__).parent.parent
    json_path = base_dir / "data" / "es_rvr" / "es_rvr.json"
    greek_dir = base_dir / "data" / "greek_nt"
    output_path = base_dir / "data" / "nt_verses.json"
    
    print("=" * 60)
    print("🔄 Procesador de Datos del Nuevo Testamento")
    print("=" * 60)
    
    if not json_path.exists():
        print(f"❌ Error: No se encuentra {json_path}")
        return
    
    if not greek_dir.exists():
        print(f"❌ Error: No se encuentra {greek_dir}")
        return
    
    spanish_nt = load_spanish_nt(str(json_path))
    greek_nt = load_greek_nt(str(greek_dir))
    
    merged_data = merge_data(spanish_nt, greek_nt)
    
    print(f"\n💾 Guardando {len(merged_data)} versículos en {output_path}...")
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(merged_data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Proceso completado!")
    print(f"📊 Total de versículos procesados: {len(merged_data)}")
    
    books_count = len(set(v['libro'] for v in merged_data))
    chapters_count = len(set((v['libro'], v['capitulo']) for v in merged_data))
    print(f"📚 Libros: {books_count}, Capítulos: {chapters_count}")


if __name__ == "__main__":
    main()
