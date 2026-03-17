import os
import sys
import importlib
from pathlib import Path

# Adiciona o diretório "pipeline" atual ao PYTHONPATH
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

# Importa as funções principais de cada script do pipeline (usando importlib pois começam com número)
mod1 = importlib.import_module("1- importador_dados_lol")
baixar_arquivo_mais_recente = mod1.baixar_arquivo_mais_recente

mod2 = importlib.import_module("2- CSV_to_SQLite_lolmatch_datamatches")
csv_to_sqlite = mod2.main

mod3 = importlib.import_module("3- criador_tabela_silver_loldatamatches")
criar_tabela_silver = mod3.criar_tabela_silver

mod4 = importlib.import_module("4- import_2025_matches_to_silver")
popular_tabela_silver = mod4.popular_tabela_silver

mod_scrape_champs = importlib.import_module("scrape_champions")
baixar_imagens_campeoes = mod_scrape_champs.scrape_champion_squares_ddragon

def executar_pipeline_completo():
    """Executa todas as etapas de ingestão e preparação de dados em sequência."""
    log = ""
    try:
        log += "⏳ Iniciando Download do CSV (Google Drive)...\n"
        baixar_arquivo_mais_recente()
        log += "✅ Download Concluído!\n\n"
        
        log += "⏳ Verificando/Baixando Imagens dos Campeões (Data Dragon)...\n"
        try:
            champs_dir = os.path.join(os.path.dirname(__file__), "..", "data", "champs")
            # a função scrape_champion_squares_ddragon já verifica se a imagem existe antes de baixar
            baixar_imagens_campeoes(champs_dir)
            log += "✅ Imagens Verificadas!\n\n"
        except Exception as img_err:
            log += f"⚠️ Erro no Download de Imagens (Ignorado para o fluxo): {img_err}\n\n"
        
        log += "⏳ Criando/Populando Tabela Bronze (SQLite)...\n"
        csv_to_sqlite()
        log += "✅ Bronze OK!\n\n"
        
        log += "⏳ Criando Estrutura da Tabela Silver...\n"
        criar_tabela_silver()
        log += "✅ Silver Estrutura OK!\n\n"
        
        log += "⏳ Inserindo Dados na Tabela Silver...\n"
        popular_tabela_silver()
        log += "✅ Silver Dados OK!\n\n"

        log += "⏳ Criando/Populando Camada Platinum...\n"
        try:
            mod6 = importlib.import_module("6- criador_tabela_platinum")
            mod6.criar_tabela_platinum()
            mod7 = importlib.import_module("7- popular_tabela_platinum")
            mod7.popular_tabela_platinum()
            log += "✅ Platinum OK!\n\n"
        except Exception as plat_err:
            log += f"⚠️ Erro na Camada Platinum (ignorado para o fluxo principal): {plat_err}\n\n"
        
        log += "🎉 PARABÉNS! Pipeline concluído com sucesso. A base de dados está atualizada e pronta para predições."
        return log
    except Exception as e:
        return f"❌ ERRO DURANTE O PIPELINE: {str(e)}\n\nVerifique os arquivos originais e a conexão de rede."
