import sqlite3
from banco import NOME_BANCO

print("Banco usado:", NOME_BANCO)

conexao = sqlite3.connect(NOME_BANCO)
total = conexao.execute("SELECT COUNT(*) FROM notas").fetchone()[0]
print("Linhas na tabela notas:", total)

for linha in conexao.execute("SELECT id, empresa, valor_total, data_emissao FROM notas"):
    print(linha)
conexao.close()