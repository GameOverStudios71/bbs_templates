import os
import sqlite3
from pathlib import Path
from typing import Optional, Dict, List, Tuple

# Configurações
DATABASE_PATH = 'presets.db'
EXAMPLES_DIR = 'examples'

def init_database() -> sqlite3.Connection:
    """Inicializa o banco de dados e retorna a conexão."""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS presets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER,
        name TEXT NOT NULL,
        description TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(category_id, name),
        FOREIGN KEY (category_id) REFERENCES categories (id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS files (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        preset_id INTEGER,
        file_type TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(preset_id, file_type),
        FOREIGN KEY (preset_id) REFERENCES presets (id)
    )
    ''')
    
    # Índices para melhorar a performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_presets_category ON presets(category_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_files_preset ON files(preset_id)')
    
    conn.commit()
    return conn

def get_or_create_category(cursor: sqlite3.Cursor, name: str) -> int:
    """Obtém ou cria uma categoria e retorna o ID."""
    cursor.execute('SELECT id FROM categories WHERE name = ?', (name,))
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
    return cursor.lastrowid

def get_or_create_preset(cursor: sqlite3.Cursor, category_id: int, name: str) -> int:
    """Obtém ou cria um preset e retorna o ID."""
    cursor.execute(
        'SELECT id FROM presets WHERE category_id = ? AND name = ?',
        (category_id, name)
    )
    result = cursor.fetchone()
    
    if result:
        return result[0]
    
    cursor.execute(
        'INSERT INTO presets (category_id, name) VALUES (?, ?)',
        (category_id, name)
    )
    return cursor.lastrowid

def update_or_create_file(cursor: sqlite3.Cursor, preset_id: int, file_type: str, content: str) -> None:
    """Atualiza ou cria um arquivo para o preset."""
    cursor.execute(
        'SELECT id FROM files WHERE preset_id = ? AND file_type = ?',
        (preset_id, file_type)
    )
    
    if cursor.fetchone():
        cursor.execute(
            '''
            UPDATE files 
            SET content = ?, updated_at = CURRENT_TIMESTAMP 
            WHERE preset_id = ? AND file_type = ?
            ''',
            (content, preset_id, file_type)
        )
    else:
        cursor.execute(
            'INSERT INTO files (preset_id, file_type, content) VALUES (?, ?, ?)',
            (preset_id, file_type, content)
        )

def process_dist_directory(cursor: sqlite3.Cursor, preset_id: int, category_name: str, preset_name: str, dir_path: str) -> None:
    """Processa os arquivos em um diretório dist."""
    try:
        for file_name in os.listdir(dir_path):
            file_path = os.path.join(dir_path, file_name)
            if not os.path.isfile(file_path):
                continue
            
            # Determina o tipo do arquivo
            if file_name.endswith('.html'):
                file_type = 'html'
            elif file_name.endswith('.css'):
                file_type = 'css'
            elif file_name.endswith('.js'):
                file_type = 'js'
            else:
                continue  # Ignora outros tipos de arquivo
            
            # Lê o conteúdo do arquivo
            try:
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    content = f.read()
                
                update_or_create_file(cursor, preset_id, file_type, content)
                print(f"Processado: {category_name}/{preset_name}/{file_name}")
            except Exception as e:
                print(f"Erro ao processar {file_path}: {str(e)}")
    except Exception as e:
        print(f"Erro ao listar diretório {dir_path}: {str(e)}")

def process_directory(base_dir: str) -> None:
    """Processa o diretório de exemplos e importa para o banco de dados."""
    conn = init_database()
    cursor = conn.cursor()
    
    try:
        # Percorre cada categoria (primeiro nível)
        for category_name in os.listdir(base_dir):
            category_path = os.path.join(base_dir, category_name)
            if not os.path.isdir(category_path) or category_name.startswith('.'):
                continue
                
            category_id = get_or_create_category(cursor, category_name)
            
            # Para cada item dentro da categoria
            for item_name in os.listdir(category_path):
                item_path = os.path.join(category_path, item_name)
                
                # Se for um diretório, trata como um preset
                if os.path.isdir(item_path):
                    # Verifica se é um diretório de preset válido (não é 'dist' nem 'src')
                    if item_name not in ['dist', 'src']:
                        process_preset(cursor, category_id, category_name, item_name, item_path)
                    
        conn.commit()
        print("\nImportação concluída com sucesso!")
        
    except Exception as e:
        conn.rollback()
        print(f"Erro durante a importação: {str(e)}")
    finally:
        conn.close()

def process_preset(cursor: sqlite3.Cursor, category_id: int, category_name: str, preset_name: str, preset_path: str) -> None:
    """Processa um único preset."""
    # Verifica se existe um diretório 'dist' dentro do preset
    dist_path = os.path.join(preset_path, 'dist')
    if os.path.exists(dist_path) and os.path.isdir(dist_path):
        preset_id = get_or_create_preset(cursor, category_id, preset_name)
        process_dist_directory(cursor, preset_id, category_name, preset_name, dist_path)
    else:
        print(f"Aviso: Diretório 'dist' não encontrado em {preset_path}")

if __name__ == "__main__":
    if not os.path.exists(EXAMPLES_DIR):
        print(f"Erro: Diretório '{EXAMPLES_DIR}' não encontrado.")
    else:
        print("Iniciando importação de presets...\n")
        process_directory(EXAMPLES_DIR)
