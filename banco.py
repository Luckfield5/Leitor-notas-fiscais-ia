import hashlib
import sqlite3

from pathlib import Path

NOME_BANCO = Path(__file__).resolve().parent / "notas.db"


def calcular_hash(conteudo_bytes):
    return hashlib.sha256(conteudo_bytes).hexdigest()


def criar_banco():
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS notas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa TEXT NOT NULL,
            valor_total REAL NOT NULL,
            data_emissao TEXT NOT NULL,
            arquivo_origem TEXT,
            hash_arquivo TEXT,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Migração: bancos criados antes não têm a coluna hash_arquivo
    cursor.execute("PRAGMA table_info(notas)")
    colunas = [coluna[1] for coluna in cursor.fetchall()]
    if "hash_arquivo" not in colunas:
        cursor.execute("ALTER TABLE notas ADD COLUMN hash_arquivo TEXT")

    # Impede dois registros com o mesmo hash
    cursor.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS idx_notas_hash ON notas(hash_arquivo)"
    )

    conexao.commit()
    conexao.close()


def hash_ja_existe(hash_arquivo):
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT 1 FROM notas WHERE hash_arquivo = ? LIMIT 1", (hash_arquivo,)
    )
    existe = cursor.fetchone() is not None
    conexao.close()
    return existe


def nota_ja_existe(dados):
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute(
        """
        SELECT 1 FROM notas
        WHERE empresa = ? COLLATE NOCASE
          AND valor_total = ?
          AND data_emissao = ?
        LIMIT 1
        """,
        (dados["empresa"], dados["valor_total"], dados["data_emissao"]),
    )
    existe = cursor.fetchone() is not None
    conexao.close()
    return existe


def salvar_nota(dados, arquivo_origem, hash_arquivo=None):
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute(
        """
        INSERT INTO notas (empresa, valor_total, data_emissao, arquivo_origem, hash_arquivo)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            dados["empresa"],
            dados["valor_total"],
            dados["data_emissao"],
            arquivo_origem,
            hash_arquivo,
        ),
    )
    conexao.commit()
    novo_id = cursor.lastrowid
    conexao.close()
    return novo_id


def listar_notas():
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute(
        "SELECT id, empresa, valor_total, data_emissao, arquivo_origem FROM notas"
    )
    linhas = cursor.fetchall()
    conexao.close()
    return linhas
def atualizar_nota(id_nota, dados):
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute(
        """
        UPDATE notas
        SET empresa = ?, valor_total = ?, data_emissao = ?
        WHERE id = ?
        """,
        (dados["empresa"], dados["valor_total"], dados["data_emissao"], id_nota),
    )
    conexao.commit()
    conexao.close()


def excluir_nota(id_nota):
    conexao = sqlite3.connect(NOME_BANCO)
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM notas WHERE id = ?", (id_nota,))
    conexao.commit()
    conexao.close()

if __name__ == "__main__":
    criar_banco()
    print("Banco criado com sucesso!")