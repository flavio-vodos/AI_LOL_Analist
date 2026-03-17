import sqlite3
import glob
import os
import re

def popular_tabela_silver():
    """
    Popula a tabela match_data_silver (camada Silver) a partir da tabela
    de dados brutos (camada Bronze). Os nomes e tipos das colunas são
    tratados e ajustados durante a inserção.
    """
    print("Iniciando processo de população da tabela Silver...")
    
    # 1. Encontra qual é o ano do dataset para saber o nome da tabela Bronze
    csv_files = glob.glob(os.path.join("data", "raw", "*loesport_matchdata.csv"))
    if not csv_files:
        print("❌ Erro: Nenhum arquivo CSV encontrado em 'data/raw'. Não foi possível determinar o nome da tabela Bronze.")
        return
        
    csv_file = sorted(csv_files, reverse=True)[0]
    match = re.search(r'(\d{4})', csv_file)
    ano = match.group(1) if match else "2025"
    tabela_bronze = f"{ano}_lol_matches"
    
    ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_dir = os.path.join(ROOT_DIR, "data", "db")
    os.makedirs(db_dir, exist_ok=True)
    db_file = os.path.join(db_dir, "lol_datamatches.db")
    
    # Executa a limpeza e depois inserção
    try:
        with sqlite3.connect(db_file) as conexao:
            cursor = conexao.cursor()
            print(f"🔌 Conectado ao banco '{db_file}'.")
            
            # Carregamos com UPSERT (INSERT OR REPLACE) para lidar com duplicados
            print(f"📥 Importando/Atualizando dados da Bronze '{tabela_bronze}' para a Silver 'match_data_silver'...")
            
            cursor.execute(f'''
            INSERT OR REPLACE INTO match_data_silver (
                gameid, participantid, playername, patch, league, split, side, position, teamname, champion, result, kills,
                deaths, assists, teamkills, teamdeaths, firstblood, firstdragon,
                firstherald, firstbaron, dragons, heralds, barons, gamelength,
                kpm, ckpm, totalgold, earnedgold, goldspent, total_cs, minionkills,
                damagetochampions, damagetakenperminute, towers, inhibitors,
                goldat10, goldat15, goldat20, goldat25,
                golddiffat10, golddiffat15, golddiffat20, golddiffat25,
                csat10, csat15, csat20, csat25,
                csdiffat10, csdiffat15, csdiffat20, csdiffat25,
                wardsplaced, wardskilled, controlwardsbought, visionscore,
                cspm, earnedgoldshare,
                xpat10, xpat15, xpat20, xpat25,
                xpdiffat10, xpdiffat15, xpdiffat20, xpdiffat25,
                game
            )
            SELECT
                gameid, participantid, playername, patch, league, split, side, position, teamname, champion, result, kills,
                deaths, assists, teamkills, teamdeaths, firstblood, firstdragon,
                firstherald, firstbaron, dragons, heralds, barons, gamelength,
                "team kpm", ckpm, totalgold, earnedgold, goldspent, "total cs",
                minionkills, damagetochampions, damagetakenperminute, towers,
                inhibitors,
                goldat10, goldat15, goldat20, goldat25,
                golddiffat10, golddiffat15, golddiffat20, golddiffat25,
                csat10, csat15, csat20, csat25,
                csdiffat10, csdiffat15, csdiffat20, csdiffat25,
                wardsplaced, wardskilled, controlwardsbought, visionscore,
                cspm, earnedgoldshare,
                xpat10, xpat15, xpat20, xpat25,
                xpdiffat10, xpdiffat15, xpdiffat20, xpdiffat25,
                game
            FROM "{tabela_bronze}";
            ''')
            
            linhas_afetadas = cursor.rowcount
            conexao.commit()
            print(f"✅ Sucesso! {linhas_afetadas} registros foram importados para a camada Silver.")
            
    except sqlite3.Error as e:
        print(f"❌ Erro de banco de dados durante a importação: {e}")
    except Exception as e:
        print(f"❌ Ocorreu um erro inesperado: {e}")
    finally:
        print("✨ Processo de população finalizado!")

if __name__ == "__main__":
    popular_tabela_silver()