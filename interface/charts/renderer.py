"""
charts/renderer.py — Facade Pattern: orquestra todos os módulos e gera o HTML final.
Esta é a única função pública do pacote: generate_charts().
"""

from .html_helpers import INSIGHTS_CSS
from .data_provider import get_team_stats, get_gold_team_stats, get_gold_player_stats, get_platinum_champion_stats, get_global_baseline_stats
from .educational import gen_educational_sections
from .chart_generators import (
    gen_winrate_chart, gen_recent_form,
    gen_bloodiness_pace, gen_economy_cards,
    gen_first_objectives_egr, gen_mlr_proxy,
    gen_total_abates, gen_kills_por_time,
    gen_handicap, gen_duracao,
    gen_dragons, gen_torres, gen_baroes,
    gen_timeline_chart, gen_radar_dna,
    gen_timeline_chart, gen_radar_dna,
    gen_gold_team_summary, gen_gold_player_table
)
from .ev_finder import gen_betting_recommendations


def generate_charts(team1, team2, patches=None, odds_data=None, champs_t1=None, champs_t2=None):
    """
    API pública — gera o HTML completo do Advanced Analytics.
    
    Args:
        team1: Nome do time 1
        team2: Nome do time 2
        patches: Lista de patches para filtrar (opcional)
        odds_data: Dados de odds externas (reservado para uso futuro)
        champs_t1: Dict com os campeões selecionados para t1 (keys: Top, Jungle, Mid, ADC, Sup)
        champs_t2: Dict com os campeões selecionados para t2 (keys: Top, Jungle, Mid, ADC, Sup)
    
    Returns:
        String HTML completa com todos os gráficos, análises e recomendações.
    """
    stats1 = get_team_stats(team1, patches)
    stats2 = get_team_stats(team2, patches)
    
    # Busca dados da camada Gold (apenas índices gerais, sem filtro de patch por enquanto)
    gold_t1 = get_gold_team_stats(team1)
    gold_t2 = get_gold_team_stats(team2)
    gold_p1 = get_gold_player_stats(team1)
    gold_p2 = get_gold_player_stats(team2)
    
    # Busca dados da camada Platinum (Draft/Campeões)
    plat1, plat2 = {}, {}
    if champs_t1:
        for role, champ in champs_t1.items():
            if champ:
                plat1[champ] = get_platinum_champion_stats(team1, champ)
                
    if champs_t2:
        for role, champ in champs_t2.items():
            if champ:
                plat2[champ] = get_platinum_champion_stats(team2, champ)

    if not stats1 or not stats2:
        return f"<div style='text-align:center;padding:40px;color:#f87171;'><h3>⚠️ Dados insuficientes</h3></div>"

    global_baseline = get_global_baseline_stats(patches)
    
    def calc_multipliers(plat_data):
        if not plat_data or not global_baseline:
            return None
        factors = {"kills": [], "dragons": [], "towers": [], "barons": [], "duration": [], 
                   "firstblood": [], "firstdragon": [], "firstherald": []}
        
        for champ, data in plat_data.items():
            w_stats = data.get("world_stats")
            if w_stats:
                v = w_stats.get("avg_teamkills"); b = global_baseline.get("avg_teamkills")
                if v and b: factors["kills"].append(v / b)

                v = w_stats.get("firstblood_rate"); b = global_baseline.get("avg_team_firstblood")
                if v and b: factors["firstblood"].append(v / b)
                
                v = w_stats.get("avg_team_firstdragon"); b = global_baseline.get("avg_team_firstdragon")
                if v and b: factors["firstdragon"].append(v / b)
                
                v = w_stats.get("avg_team_firstherald"); b = global_baseline.get("avg_team_firstherald")
                if v and b: factors["firstherald"].append(v / b)
                
                v = w_stats.get("avg_team_dragons"); b = global_baseline.get("avg_team_dragons")
                if v and b: factors["dragons"].append(v / b)
                
                v = w_stats.get("avg_team_towers"); b = global_baseline.get("avg_team_towers")
                if v and b: factors["towers"].append(v / b)
                
                v = w_stats.get("avg_team_barons"); b = global_baseline.get("avg_team_barons")
                if v and b: factors["barons"].append(v / b)
                
                v = w_stats.get("avg_gamelength"); b = global_baseline.get("avg_gamelength")
                if v and b: factors["duration"].append(v / b)
                
        multipliers = {}
        for key, f_list in factors.items():
            multipliers[key] = sum(f_list) / len(f_list) if f_list else 1.0
        return multipliers

    mult_t1 = calc_multipliers(plat1)
    mult_t2 = calc_multipliers(plat2)

    patch_label = ", ".join(patches) if patches and "Todos" not in patches else "Todos os patches"

    # Layout constants
    CARD = 'style="background:#1e293b;border-radius:12px;padding:16px;border:1px solid #334155;overflow:hidden;"'
    SECTION = 'style="margin-bottom:24px;"'
    TITLE = 'style="color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #3b82f6;"'
    TITLE2 = 'style="color:#e2e8f0;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #a78bfa;"'
    TITLE3 = 'style="color:#eab308;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #eab308;"'

    html = INSIGHTS_CSS + '<div class="insights-container">'

    # Header
    html += f'''
    <div style="text-align:center;padding:30px 20px;background:linear-gradient(135deg,#0f172a 0%,#1e293b 50%,#0f172a 100%);border-radius:16px;margin-bottom:24px;border:1px solid rgba(59,130,246,0.3);">
        <h2 style="margin:0 0 8px 0;font-size:1.5rem;color:#60a5fa;">📊 Advanced Analytics — Powered by Oracle's Elixir</h2>
        <div style="display:inline-flex;align-items:center;gap:12px;background:rgba(30,41,59,0.8);padding:8px 24px;border-radius:50px;border:1px solid rgba(59,130,246,0.2);">
            <span style="color:#60a5fa;font-weight:700;font-size:1.1rem;">{team1}</span>
            <span style="color:#eab308;font-weight:800;font-size:0.9rem;">VS</span>
            <span style="color:#f87171;font-weight:700;font-size:1.1rem;">{team2}</span>
        </div>
        <div style="color:#94a3b8;font-size:0.8rem;margin-top:10px;">📅 Filtro: {patch_label} | Data Pool: {stats1["total_games"]} jogos ({team1}) / {stats2["total_games"]} ({team2})</div>
    </div>
    '''

    # Glossário
    html += gen_educational_sections()

    # Modelos Oracle's Elixir (EGR e MLR)
    html += f'<div {SECTION}><div {TITLE3}>🧠 Meta-Modelos Estruturais (EGR e MLR)</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:20px;">'
    html += gen_first_objectives_egr(stats1, stats2, team1, team2)
    html += gen_mlr_proxy(stats1, stats2, team1, team2)
    html += '</div></div>'

    # Radar & Identity
    html += f'<div {SECTION}><div {TITLE}>🕸️ Identidade Tática (Team DNA)</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{gen_radar_dna(stats1, stats2, team1, team2)}</div>'
    html += '</div></div>'

    # Timeline (Gold/CS/XP)
    html += f'<div {SECTION}><div {TITLE3}>📈 Timeline de Vantagens (10 a 25 min)</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{gen_timeline_chart(stats1, stats2, team1, team2, mult_t1, mult_t2)}</div>'
    html += '</div></div>'


    # Economia, Dano e Sangria
    html += f'<div {SECTION}><div {TITLE3}>💥 Advanced Pacing & Economy Context</div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(450px,1fr));gap:20px;">'
    html += gen_economy_cards(stats1, stats2, team1, team2, gold_t1, gold_t2)
    html += gen_bloodiness_pace(stats1, stats2, team1, team2)
    html += '</div></div>'

    # Win Rate & Momentum
    html += f'<div {SECTION}><div {TITLE}>🏆 Win Rate & Momentum</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{gen_winrate_chart(stats1, stats2, team1, team2)}</div>'
    html += gen_recent_form(stats1, stats2, team1, team2)
    html += '</div></div>'

    # Distribuições de Abates
    html += f'<div {SECTION}><div {TITLE2}>⚔️ Distribuições de Abates (Combate Extremo)</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{gen_total_abates(stats1, stats2, team1, team2, mult_t1, mult_t2)}</div>'
    html += f'<div {CARD}>{gen_kills_por_time(stats1, stats2, team1, team2, mult_t1, mult_t2)}</div>'
    html += f'<div {CARD}>{gen_handicap(stats1, stats2, team1, team2, mult_t1, mult_t2)}</div>'
    html += '</div></div>'

    # Distribuições de Objetivos (Dragões, Torres, Barões)
    TITLE4 = 'style="color:#f97316;font-size:1.1rem;font-weight:600;margin-bottom:12px;padding-left:12px;border-left:3px solid #f97316;"'
    html += f'<div {SECTION}><div {TITLE4}>🐉 Distribuições de Objetivos (Dragões, Torres, Barões)</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{gen_dragons(stats1, stats2, team1, team2, mult_t1, mult_t2)}</div>'
    html += f'<div {CARD}>{gen_torres(stats1, stats2, team1, team2, mult_t1, mult_t2)}</div>'
    html += f'<div {CARD}>{gen_baroes(stats1, stats2, team1, team2, mult_t1, mult_t2)}</div>'
    html += '</div></div>'

    # Duração
    html += f'<div {SECTION}><div {TITLE2}>⏱ Duração do Jogo (AGT)</div><div style="display:grid;grid-template-columns:1fr;gap:20px;">'
    html += f'<div {CARD}>{gen_duracao(stats1, stats2, team1, team2, mult_t1, mult_t2)}</div>'
    html += '</div></div>'

    # Expected Value Finder
    html += f'''
    <div style="text-align:center;padding:20px;margin:30px 0 24px 0;background:linear-gradient(135deg,#052e16 0%,#14532d 50%,#052e16 100%);border-radius:16px;border:1px solid rgba(34,197,94,0.3);">
        <h2 style="margin:0;font-size:1.3rem;color:#4ade80;">🎯 Expected Value Finder (Odd Mining)</h2>
        <p style="margin:4px 0 0 0;color:#94a3b8;font-size:0.85rem;">Algoritmo de varredura buscando Edges Estatísticos baseados nos Modelos do Elixir</p>
    </div>
    '''
    html += f'<div {SECTION}>{gen_betting_recommendations(stats1, stats2, team1, team2, mult_t1, mult_t2)}</div>'

    # Footer
    html += f'<div style="text-align:center;color:#64748b;font-size:0.75rem;margin-top:20px;padding:12px;">Camada Silver Analytics | Desenvolvido com Metodologia do Oracle\'s Elixir</div></div>'
    return html
