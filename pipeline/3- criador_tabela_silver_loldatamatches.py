import sqlite3
import os

def criar_tabela_silver():
    """
    Cria a estrutura da tabela match_data_silver no banco de dados SQLite.
    Esta tabela representa a camada Silver (dados refinados).
    """
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_dir = os.path.join(ROOT_DIR, "data", "db")
    os.makedirs(db_dir, exist_ok=True)
    db_file = os.path.join(db_dir, "lol_datamatches.db")
    
    print("Iniciando criação da tabela Silver...")
    
    # O bloco 'with' garante o fechamento seguro da conexão mesmo em caso de erro
    try:
        with sqlite3.connect(db_file) as conexao:
            cursor = conexao.cursor()
            
            print(f"🔌 Conectado ao banco '{db_file}' com sucesso.")
            
            # Verifica se a coluna 'patch' já existe
            cursor.execute("PRAGMA table_info(match_data_silver)")
            colunas_existentes = [col[1] for col in cursor.fetchall()]
            
            if colunas_existentes and ("goldat10" not in colunas_existentes or "playername" not in colunas_existentes or "game" not in colunas_existentes):
                print("⚠️  Esquema antigo detectado (colunas de timeline ou playername ausentes). Recriando tabela Silver...")
                cursor.execute("DROP TABLE IF EXISTS match_data_silver")
                colunas_existentes = []

            print("🏗️  Criando estrutura da tabela 'match_data_silver'...")
            
            # Cria a tabela com UNIQUE constraint para upsert
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS match_data_silver (
                    gameid TEXT,
                    participantid INTEGER,
                    playername TEXT,
                    patch TEXT,
                    league TEXT,
                    split TEXT,
                    side TEXT,
                    position TEXT,
                    teamname TEXT,
                    champion TEXT,
                    result TEXT,
                    kills INTEGER,
                    deaths INTEGER,
                    assists INTEGER,
                    teamkills INTEGER,
                    teamdeaths INTEGER,
                    firstblood INTEGER,
                    firstdragon INTEGER,
                    firstherald INTEGER,
                    firstbaron INTEGER,
                    dragons INTEGER,
                    heralds INTEGER,
                    barons INTEGER,
                    gamelength REAL,
                    kpm REAL,
                    ckpm REAL,
                    totalgold INTEGER,
                    earnedgold INTEGER,
                    goldspent INTEGER,
                    total_cs INTEGER,
                    minionkills INTEGER,
                    damagetochampions INTEGER,
                    damagetakenperminute REAL,
                    towers INTEGER,
                    inhibitors INTEGER,
                    goldat10 REAL,
                    goldat15 REAL,
                    goldat20 REAL,
                    goldat25 REAL,
                    golddiffat10 REAL,
                    golddiffat15 REAL,
                    golddiffat20 REAL,
                    golddiffat25 REAL,
                    csat10 REAL,
                    csat15 REAL,
                    csat20 REAL,
                    csat25 REAL,
                    csdiffat10 REAL,
                    csdiffat15 REAL,
                    csdiffat20 REAL,
                    csdiffat25 REAL,
                    wardsplaced INTEGER,
                    wardskilled INTEGER,
                    controlwardsbought INTEGER,
                    visionscore REAL,
                    cspm REAL,
                    earnedgoldshare REAL,
                    xpat10 REAL,
                    xpat15 REAL,
                    xpat20 REAL,
                    xpat25 REAL,
                    xpdiffat10 REAL,
                    xpdiffat15 REAL,
                    xpdiffat20 REAL,
                    xpdiffat25 REAL,
                    game INTEGER,
                    UNIQUE(gameid, participantid)
                );
            ''')
            
            print("✅ Tabela 'match_data_silver' verificada/criada com sucesso.")
            
    except sqlite3.Error as e:
        print(f"❌ Erro de banco de dados ao tentar criar a tabela: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
    finally:
        print("✨ Processo de criação da tabela finalizado!")

if __name__ == "__main__":
    criar_tabela_silver()