import pandas as pd
import sqlite3

# 1. Caminho do CSV
csv_file = "2025loesport_matchdata.csv"

# 2. Nome do banco de dados SQLite 
db_file = "lol_datamatches.db"

# 3. Nome da tabela que será criada no banco
tabela = "2025_lol_matches"

# 4. Lê o CSV com pandas
df = pd.read_csv(csv_file)

# 5. Conecta (ou cria) o banco SQLite
con = sqlite3.connect(db_file)

# 6. Exporta o DataFrame para o SQLite (substituindo se já existir)
df.to_sql(tabela, con, if_exists="replace", index=False)

# 7. Fecha a conexão
con.close()


