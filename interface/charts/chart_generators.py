"""
charts/chart_generators.py — Strategy Pattern: cada gráfico é uma função independente.
Todas as funções recebem (s1, s2, t1, t2) e retornam HTML string.
"""

from collections import Counter
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from .html_helpers import (
    base_layout, fig_to_html, int_list, float_list,
    calc_stats, stats_html, odd_badge, explain, data_comment, bet_line,
)


# ============================================================================
# Win Rate & Momentum
# ============================================================================

def gen_winrate_chart(s1, s2, t1, t2):
    """Gauge duplo de Win Rate."""
    fig = make_subplots(rows=1, cols=2, specs=[[{"type": "indicator"}, {"type": "indicator"}]])
    for col, (s, t, color, bar_color) in enumerate([
        (s1, t1, "#3b82f6", "#2563eb"), (s2, t2, "#ef4444", "#dc2626")
    ], 1):
        fig.add_trace(go.Indicator(
            mode="gauge+number+delta", value=s["win_rate"],
            number=dict(suffix="%", font=dict(size=36, color=color)),
            gauge=dict(axis=dict(range=[0, 100], tickcolor="#94a3b8"), bar=dict(color=bar_color),
                       bgcolor="#0f172a", bordercolor="#334155",
                       steps=[dict(range=[0, 40], color="rgba(239, 68, 68, 0.1)"),
                              dict(range=[40, 60], color="rgba(234, 179, 8, 0.1)"),
                              dict(range=[60, 100], color="rgba(34, 197, 94, 0.1)")]),
            delta=dict(reference=50, suffix="%", font=dict(size=14)),
        ), row=1, col=col)
    fig.update_layout(**base_layout("🏆 Taxa de Vitória (Win Rate)", height=300))
    fig.update_layout(annotations=[
        dict(text=t1, x=0.2, y=1.1, xref="paper", yref="paper", showarrow=False, font=dict(size=15, color="#3b82f6", weight="bold")),
        dict(text=t2, x=0.8, y=1.1, xref="paper", yref="paper", showarrow=False, font=dict(size=15, color="#ef4444", weight="bold")),
    ])
    # Data-based comments
    wr1, wr2 = s1["win_rate"], s2["win_rate"]
    comments = []
    diff = abs(wr1 - wr2)
    fav, dog = (t1, t2) if wr1 > wr2 else (t2, t1)
    fav_wr, dog_wr = max(wr1, wr2), min(wr1, wr2)
    if diff > 20:
        comments.append(f'🏆 <b>Domínio claro:</b> {fav} tem {fav_wr:.0f}% de WR vs {dog_wr:.0f}% de {dog} — uma diferença de <b>{diff:.0f}%</b>. Odds pré-jogo provavelmente já refletem isso; procure valor em mercados de handicap ou props.')
    elif diff > 10:
        comments.append(f'📊 <b>Vantagem moderada:</b> {fav} lidera com {fav_wr:.0f}% vs {dog_wr:.0f}%. A diferença de {diff:.0f}% sugere que {fav} é favorito mas não dominante. Verifique se as odds oferecem valor para o underdog.')
    else:
        comments.append(f'⚖️ <b>Duelo equilibrado:</b> WR próximos ({wr1:.0f}% vs {wr2:.0f}%). Neste cenário, fatores como draft, forma recente e EGR/MLR serão decisivos. Odds tendem a ser mais justas — busque edge em mercados secundários.')
    if fav_wr > 65:
        comments.append(f'💰 {fav} com WR acima de 65% é um time de <b>tier superior</b>. Odds de ML podem estar comprimidas — considere <b>Handicap -1.5 ou -2.5</b> para melhor valor.')
    if dog_wr < 35:
        comments.append(f'⚠️ {dog} com WR abaixo de 35% está em dificuldade. Apostar neste time como ML é arriscado, mas <b>Handicap +5.5 kills</b> pode oferecer proteção.')
    return fig_to_html(fig) + data_comment(comments)


def gen_recent_form(s1, s2, t1, t2):
    """Forma recente (últimos 10 jogos) em bloquinhos W/L."""
    html = '<div class="chart-card">'
    html += '<h3 style="color:#f8fafc;margin:0 0 20px 0;font-size:1.1rem;font-weight:700;">📈 Forma Recente (Últimos 10 Jogos)</h3>'
    for team_name, stats, color, bg_color in [(t1, s1, "#3b82f6", "rgba(59, 130, 246, 0.1)"), (t2, s2, "#ef4444", "rgba(239, 68, 68, 0.1)")]:
        results = stats.get("recent_results", [])
        recent_wr = sum(1 for r in results if r == '1') / len(results) * 100 if results else 0
        html += f'<div style="margin-bottom:20px; padding: 12px; background: {bg_color}; border-radius: 12px; border: 1px solid rgba(255,255,255,0.05);">'
        html += f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">'
        html += f'<span style="color:{color};font-weight:800;font-size:1rem;">{team_name}</span>'
        html += f'<span style="color:#cbd5e1;font-size:0.85rem;font-weight:600;">Win Rate Recente: <b style="color:{color}">{recent_wr:.0f}%</b></span>'
        html += '</div>'
        html += '<div style="display:flex;gap:6px;">'
        for r in results:
            if r == '1':
                html += '<div style="width:34px;height:34px;border-radius:8px;background:#10b981;display:flex;align-items:center;justify-content:center;font-weight:800;color:white;font-size:0.85rem;box-shadow: 0 2px 4px rgba(0,0,0,0.2);">W</div>'
            else:
                html += '<div style="width:34px;height:34px;border-radius:8px;background:#ef4444;display:flex;align-items:center;justify-content:center;font-weight:800;color:white;font-size:0.85rem;box-shadow: 0 2px 4px rgba(0,0,0,0.2);">L</div>'
        html += '</div></div>'
    html += explain("Sequências longas de vitórias indicam momento favorável emocionalmente (<i>Momentum</i>).")
    # Data-based comments
    comments = []
    for team_name, stats, color in [(t1, s1, "#3b82f6"), (t2, s2, "#ef4444")]:
        results = stats.get("recent_results", [])
        if not results:
            continue
        recent_wr = sum(1 for r in results if r == '1') / len(results) * 100
        # Detect streaks
        streak_type, streak_count = None, 0
        for r in reversed(results):
            if streak_type is None:
                streak_type = r
                streak_count = 1
            elif r == streak_type:
                streak_count += 1
            else:
                break
        if streak_count >= 4 and streak_type == '1':
            comments.append(f'🔥 <b>{team_name} em sequência de {streak_count} vitórias!</b> Momentum forte — odds pré-jogo podem estar comprimidas. Se apostar neste time, busque mercados alternativos (Over kills, First Blood) para melhor valor.')
        elif streak_count >= 3 and streak_type == '0':
            comments.append(f'📉 <b>{team_name} em sequência de {streak_count} derrotas.</b> Momento negativo pode afetar moral. Odds podem estar infladas — verifique se há valor como underdog, mas com cautela.')
        if recent_wr >= 80:
            comments.append(f'⭐ {team_name} com <b>{recent_wr:.0f}% WR recente</b> (últimos 10 jogos). Desempenho excepcional no período recente favorece apostas de confiança.')
        elif recent_wr <= 20:
            comments.append(f'⚠️ {team_name} com apenas <b>{recent_wr:.0f}% WR recente</b>. Time em crise — risco elevado para ML, mas potencial valor em Handicap positivo.')
    html += data_comment(comments)
    html += '</div>'
    return html


# ============================================================================
# Pacing & Economy
# ============================================================================

def gen_bloodiness_pace(s1, s2, t1, t2):
    """Gráfico de Ritmo de Jogo: CKPM e KPM."""
    html = '<div class="chart-card">'
    html += '<h3 style="color:#f8fafc;margin:0 0 20px 0;font-size:1.1rem;font-weight:700;">🩸 Ritmo de Jogo (Pace & Bloodiness)</h3>'

    for name, key, is_combined in [("CKPM (Combined Kills/Min)", "ckpm_history", True), ("KPM (Team Kills/Min)", "kpm_history", False)]:
        html += f'<div style="margin-bottom:24px;">'
        html += f'<div style="color:#94a3b8;font-weight:700;font-size:0.8rem;margin-bottom:12px;text-transform:uppercase;letter-spacing:1px;">{name}</div>'
        for stats, team, color in [(s1, t1, "#3b82f6" if not is_combined else "#8b5cf6"),
                                   (s2, t2, "#ef4444" if not is_combined else "#ec4899")]:
            data = float_list(stats.get(key, []))
            if not data:
                continue
            avg_val = sum(data) / len(data)
            max_scale = 1.2 if is_combined else 0.6
            width_pct = min(100, (avg_val / max_scale) * 100)
            html += f'<div style="margin-bottom:12px;">'
            html += f'<div style="display:flex;justify-content:space-between;margin-bottom:6px;font-size:0.85rem;">'
            html += f'<span style="color:{color};font-weight:700;">{team}</span>'
            html += f'<span style="color:#f8fafc;font-weight:800;">{avg_val:.2f} <small style="font-weight:400;color:#64748b;">abates/min</small></span>'
            html += '</div>'
            html += f'<div style="background:#0f172a;border-radius:6px;height:12px;overflow:hidden;border:1px solid rgba(255,255,255,0.05);">'
            html += f'<div style="width:{width_pct:.0f}%;height:100%;background:linear-gradient(90deg, {color}88, {color});border-radius:6px;box-shadow: 0 0 10px {color}33;"></div></div>'
            html += '</div>'
        html += '</div>'
    html += explain("<b>CKPM</b> indica o ritmo global da partida. CKPM > 0.8 indicam jogos 'sangrentos', cheios de lutas (favorável para Overs de Kills). <b>KPM</b> mede a letalidade bruta de apenas um time.")
    # Data-based comments
    comments = []
    ckpm1 = float_list(s1.get("ckpm_history", []))
    ckpm2 = float_list(s2.get("ckpm_history", []))
    kpm1 = float_list(s1.get("kpm_history", []))
    kpm2 = float_list(s2.get("kpm_history", []))
    avg_ckpm1 = sum(ckpm1) / len(ckpm1) if ckpm1 else 0
    avg_ckpm2 = sum(ckpm2) / len(ckpm2) if ckpm2 else 0
    avg_kpm1 = sum(kpm1) / len(kpm1) if kpm1 else 0
    avg_kpm2 = sum(kpm2) / len(kpm2) if kpm2 else 0
    if avg_ckpm1 > 0.8 and avg_ckpm2 > 0.8:
        comments.append(f'🩸 <b>Jogo sangrento esperado!</b> Ambos os times têm CKPM alto ({t1}: {avg_ckpm1:.2f}, {t2}: {avg_ckpm2:.2f}). Quando dois times agressivos se encontram, <b>Over em Total Kills</b> é historicamente uma aposta forte.')
    elif avg_ckpm1 > 0.8 or avg_ckpm2 > 0.8:
        aggressive = t1 if avg_ckpm1 > avg_ckpm2 else t2
        comments.append(f'⚔️ <b>{aggressive} é o agressor</b> com CKPM mais alto. O ritmo da partida depende se o time passivo aceita as lutas ou joga por objetivos.')
    if avg_ckpm1 < 0.6 and avg_ckpm2 < 0.6:
        comments.append(f'🧊 <b>Jogo controlado esperado.</b> CKPM baixo de ambos ({avg_ckpm1:.2f} e {avg_ckpm2:.2f}) indica partida estratégica com poucas lutas. Favoreça <b>Under em kills</b> e <b>Over em duração</b>.')
    if avg_kpm1 > 0 and avg_kpm2 > 0:
        ratio = max(avg_kpm1, avg_kpm2) / min(avg_kpm1, avg_kpm2)
        if ratio > 1.3:
            lethal = t1 if avg_kpm1 > avg_kpm2 else t2
            comments.append(f'🎯 <b>{lethal} é {ratio:.1f}x mais letal</b> em KPM. Essa diferença sugere que {lethal} controla o ritmo das lutas — Handicap de kills pode ter valor.')
    html += data_comment(comments)
    html += '</div>'
    return html


def gen_economy_cards(s1, s2, t1, t2, g1=None, g2=None):
    """Métricas de Economia: EGPM, DPM e Gold Layer (EGDI, Throw, Comeback)."""
    html = '<div class="chart-card">'
    html += '<h3 style="color:#f8fafc;margin:0 0 20px 0;font-size:1.1rem;font-weight:700;">💰 Economia & Dano (The Advanced Stats Problem)</h3>'

    metrics = [
        ("EGPM (Earned Gold/Min)", "earnedgold_pm_history", "Ouro farmado/min (ignora ouro inicial), define o potencial de compra de itens. Alta EGPM = farm massivo."),
        ("DPM (Damage/Min)", "dmg_pm_history", "Dano a campeões por minuto. Mede a eficiência bruta em teamfights."),
    ]

    for title, key, exp in metrics:
        html += f'<div style="margin-bottom:24px;">'
        html += f'<div style="color:#fbbf24;font-weight:700;font-size:0.85rem;margin-bottom:12px;text-transform:uppercase;letter-spacing:1px;">{title}</div>'
        html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'
        for stats, team, color in [(s1, t1, "#3b82f6"), (s2, t2, "#ef4444")]:
            data = float_list(stats.get(key, []))
            if not data: continue
            st = calc_stats(data)
            html += f'<div style="background:#0f172a;padding:12px;border-radius:12px;border:1px solid rgba(255,255,255,0.05);">'
            html += f'<div style="color:{color};font-weight:800;font-size:0.8rem;margin-bottom:4px;">{team}</div>'
            html += f'<div style="font-size:1.4rem;font-weight:900;color:#f8fafc;">{st["avg"]:.0f}</div> '
            html += f'<div style="color:#64748b;font-size:0.7rem;font-weight:600;">MAX: {st["max"]:.0f} | MIN: {st["min"]:.0f}</div>'
            html += '</div>'
        html += '</div>'
        html += f'<div style="color:#64748b;font-size:0.75rem;margin-top:8px;font-style:italic;">{exp}</div>'
        html += '</div>'

    if g1 and g2:
        html += '<div style="margin-top:32px;padding-top:24px;border-top:1px solid rgba(255,255,255,0.1);">'
        html += '<h4 style="color:#fbbf24;font-size:0.95rem;margin-bottom:16px;text-transform:uppercase;">📈 Gold Layer Efficiency (Comebacks & Throws)</h4>'
        g_metrics = [("Early Game Dominance Index (EGDI)", "egdi_score", True), ("Throw Rate (Entregas)", "throw_rate", False), ("Comeback Rate (Viradas)", "comeback_rate", False)]
        for g_title, g_key, is_idx in g_metrics:
            html += f'<div style="margin-bottom:16px;"><div style="color:#cbd5e1;font-weight:600;font-size:0.85rem;margin-bottom:8px;">{g_title}</div>'
            html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'
            for g_stats, team, color in [(g1, t1, "#3b82f6"), (g2, t2, "#ef4444")]:
                val = g_stats.get(g_key, 0) or 0
                val_str = f"{val*100:.1f}%" if not is_idx else f"{val:+.1f}"
                html += f'<div style="background:#0f172a;padding:10px 12px;border-radius:10px;border:1px solid rgba(255,255,255,0.05);display:flex;justify-content:space-between;align-items:center;">'
                html += f'<span style="color:{color};font-size:0.75rem;font-weight:700;">{team}</span>'
                html += f'<span style="color:#fbbf24;font-weight:800;font-size:0.95rem;">{val_str}</span></div>'
            html += '</div></div>'
        html += '</div>'

    html += explain("Segundo o artigo <i>LoL's Advanced Stats Problem</i>, a verdadeira pressão do jogo provém de <b>Ouro Ganho (EGPM)</b> e <b>Dano Gerado (DPM)</b>.")
    comments = []
    avg_egpm1 = sum(float_list(s1.get("earnedgold_pm_history", []))) / max(len(s1.get("earnedgold_pm_history", [])), 1)
    avg_egpm2 = sum(float_list(s2.get("earnedgold_pm_history", []))) / max(len(s2.get("earnedgold_pm_history", [])), 1)
    avg_dpm1 = sum(float_list(s1.get("dmg_pm_history", []))) / max(len(s1.get("dmg_pm_history", [])), 1)
    avg_dpm2 = sum(float_list(s2.get("dmg_pm_history", []))) / max(len(s2.get("dmg_pm_history", [])), 1)
    for team, opp, e, d, eo, do_val in [(t1, t2, avg_egpm1, avg_dpm1, avg_egpm2, avg_dpm2), (t2, t1, avg_egpm2, avg_dpm2, avg_egpm1, avg_dpm1)]:
         if e > eo * 1.1 and d < do_val * 0.9: comments.append(f'💰 <b>{team} farms muito mas causa pouco dano.</b> Indica jogo passivo.')
         elif e < eo * 0.9 and d > do_val * 1.1: comments.append(f'⚔️ <b>{team} é eficiente com poucos recursos.</b> Indica time letal.')
    if g1 and g2:
        for g_stats, team in [(g1, t1), (g2, t2)]:
            th, cb = g_stats.get("throw_rate", 0) or 0, g_stats.get("comeback_rate", 0) or 0
            if th > 0.3: comments.append(f'⚠️ <b>{team} tem Throw Rate alto ({th*100:.0f}%).</b> Desperdiça vantagens.')
            if cb > 0.3: comments.append(f'🔄 <b>{team} é expert em viradas ({cb*100:.0f}%).</b> Bom para live betting.')
    html += data_comment(comments) + '</div>'
    return html


# ============================================================================
# Oracle's Elixir Meta-Models: EGR & MLR
# ============================================================================

def gen_first_objectives_egr(s1, s2, t1, t2):
    """Early Game Rating Proxy (First Blood, Dragon, Herald)."""
    html = '<div class="chart-card">'
    html += '<h3 style="color:#f8fafc;margin:0 0 20px 0;font-size:1.1rem;font-weight:700;">⚡ Early-Game Rating (EGR) Proxy</h3>'
    fb1, fb2, fd1, fd2, fh1, fh2 = s1["fb_rate"], s2["fb_rate"], s1["fd_rate"], s2["fd_rate"], s1["fherald_rate"], s2["fherald_rate"]
    categories = [("First Blood (FB%)", fb1, fb2), ("First Dragon (FD%)", fd1, fd2), ("First Herald (HLD%)", fh1, fh2)]
    for title, v1, v2 in categories:
        html += f'<div style="margin-bottom:20px;"><div style="color:#94a3b8;font-weight:700;font-size:0.75rem;margin-bottom:10px;text-transform:uppercase;">{title}</div>'
        html += f'<div style="display:flex;align-items:center;gap:12px;margin-bottom:8px;">'
        html += f'<div style="flex:1;background:#0f172a;border-radius:100px;height:14px;overflow:hidden;border:1px solid rgba(255,255,255,0.05);display:flex;justify-content:flex-end;">'
        html += f'<div style="width:{v1:.0f}%;height:100%;background:linear-gradient(90deg, #3b82f6, #60a5fa);border-radius:100px;"></div></div>'
        html += f'<span style="color:#3b82f6;font-weight:900;min-width:45px;text-align:center;font-size:0.9rem;">{v1:.0f}%</span><span style="color:#f87171;font-weight:900;min-width:45px;text-align:center;font-size:0.9rem;">{v2:.0f}%</span>'
        html += f'<div style="flex:1;background:#0f172a;border-radius:100px;height:14px;overflow:hidden;border:1px solid rgba(255,255,255,0.05);">'
        html += f'<div style="width:{v2:.0f}%;height:100%;background:linear-gradient(90deg, #f87171, #ef4444);border-radius:100px;"></div></div></div></div>'
    html += explain("O modelo de <b>EGR</b> demonstra que o time que conquista esses prêmios iniciais cria snowball de ouro.")
    comments = []
    e1, e2 = (fb1 + fd1 + fh1) / 3, (fb2 + fd2 + fh2) / 3
    for team, e_val in [(t1, e1), (t2, e2)]:
        if e_val > 60: comments.append(f'⚡ <b>{team} tem domínio early game ({e_val:.0f}% EGR).</b> Favorito a FB/FD.')
        elif e_val < 40: comments.append(f'⚠️ <b>{team} tem EGR baixo ({e_val:.0f}%).</b> Costuma começar atrás.')
    return html + data_comment(comments) + '</div>'


def gen_mlr_proxy(s1, s2, t1, t2):
    """Mid/Late Rating Proxy (Barons, Inhibitors, Towers)."""
    html = '<div class="chart-card"><h3 style="color:#f8fafc;margin:0 0 20px 0;font-size:1.1rem;font-weight:700;">🏰 Mid/Late Rating (MLR) Proxy</h3>'
    html += '''<div style="overflow-x:auto;"><table style="width:100%;border-collapse:collapse;font-size:0.85rem;text-align:center;">
        <thead style="background:rgba(255,255,255,0.03);"><tr style="color:#94a3b8;border-bottom:1px solid #334155;">
        <th style="padding:12px;text-align:left;">Time</th><th>FBN%</th><th>Barões (AVG)</th><th>Inibidores (AVG)</th><th>Torres (AVG)</th></tr></thead><tbody>'''
    for stats, team, color in [(s1, t1, "#3b82f6"), (s2, t2, "#ef4444")]:
        html += f'<tr style="color:#f8fafc;border-bottom:1px solid rgba(51,65,85,0.2);"><td style="padding:16px 12px;text-align:left;color:{color};font-weight:800;">{team}</td>'
        html += f'<td style="font-weight:700;">{stats["fbaron_rate"]:.0f}%</td><td>{stats["avg_barons"]:.1f}</td><td>{stats["avg_inhibitors"]:.1f}</td><td style="font-weight:800;color:#facc15;">{stats["avg_towers"]:.1f}</td></tr>'
    html += '</tbody></table></div><div style="margin-top:16px;"></div>'
    html += explain("O modelo <b>MLR</b> mostra como o time fecha o jogo no Mid-Late Game.")
    comments = []
    mlr1 = min((s1.get("avg_barons", 0) + s1.get("avg_inhibitors", 0) + s1.get("avg_towers", 0) / 5) / 3 * 20, 100)
    mlr2 = min((s2.get("avg_barons", 0) + s2.get("avg_inhibitors", 0) + s2.get("avg_towers", 0) / 5) / 3 * 20, 100)
    egr1 = (s1.get("fb_rate", 0) + s1.get("fd_rate", 0) + s1.get("fherald_rate", 0)) / 3
    egr2 = (s2.get("fb_rate", 0) + s2.get("fd_rate", 0) + s2.get("fherald_rate", 0)) / 3
    for team, opp, mlr, egr in [(t1, t2, mlr1, egr1), (t2, t1, mlr2, egr2)]:
        if mlr > 60 and egr < 40: comments.append(f'🔄 <b>{team} é um time de virada!</b> EGR fraco ({egr:.0f}%) mas MLR forte ({mlr:.0f}).')
        elif mlr > 60 and egr > 60: comments.append(f'👑 <b>{team} é completo:</b> forte no early e no late.')
    return html + data_comment(comments) + '</div>'

# ============================================================================
# Plotly Distribution Charts
# ============================================================================

def gen_total_abates(s1, s2, t1, t2, mult1=None, mult2=None):
    """Distribuição do total de kills combinadas na partida."""
    k1 = int_list(s1.get("kills_history", []))
    k2 = int_list(s2.get("kills_history", []))
    min_len = min(len(k1), len(k2))
    if min_len == 0:
        return ""
    total = [k1[i] + k2[i] for i in range(min_len)]
    st = calc_stats(total)
    counts = Counter(total)
    x_vals = sorted(counts.keys())
    y_vals = [counts[v] for v in x_vals]

    fig = go.Figure()
    fig.add_trace(go.Bar(x=x_vals, y=y_vals, marker_color="#8b5cf6", marker_line_color="#a78bfa", marker_line_width=1, text=[str(c) for c in y_vals], textposition="outside"))
    fig.add_vline(x=st["avg"], line=dict(color="#8b5cf6", width=2.5, dash="dash"))
    layout = base_layout(f"⚔️ Total de Abates na Partida — {t1} vs {t2}", height=380)
    layout["xaxis"]["title"] = "Total de Kills no Jogo"
    layout["yaxis"]["title"] = "Nº de Jogos"
    fig.update_layout(**layout)

    bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas sugeridas (Total Kills):</b><br>'
    for lv in [st["avg"] - 5, st["avg"] - 2.5, st["avg"], st["avg"] + 2.5, st["avg"] + 5]:
        line_v = round(lv * 2) / 2
        prob_over = sum(1 for v in total if v > line_v) / len(total) * 100
        prob_under = 100 - prob_over
        bets += bet_line(f"{t1}+{t2}", "Over", f"{line_v:.1f} kills", prob_over, len(total),
            f"Em {sum(1 for v in total if v > line_v)} de {len(total)} jogos o total de kills foi > {line_v:.1f}. "
            f"Média histórica: {st['avg']:.1f}, Mediana: {st['med']:.1f}, Desvio Padrão: {st['std']:.1f}. "
            f"{'Alta confiança: a linha está abaixo da média.' if line_v < st['avg'] else 'Linha acima da média: depende de jogos sangrentos (alto CKPM).'}")
        bets += bet_line(f"{t1}+{t2}", "Under", f"{line_v:.1f} kills", prob_under, len(total),
            f"Em {sum(1 for v in total if v <= line_v)} de {len(total)} jogos o total de kills foi ≤ {line_v:.1f}. "
            f"{'Conservador: linha acima da média favorece Under.' if line_v > st['avg'] else 'Arriscado: linha abaixo da média desfavorece Under.'}")
        bets += '<br>'
    bets += '</div>'

    proj_html = ""
    if mult1 and mult2:
        m1 = mult1.get("kills", 1.0)
        m2 = mult2.get("kills", 1.0)
        proj_avg1 = (sum(k1)/len(k1)) * m1 if k1 else 0
        proj_avg2 = (sum(k2)/len(k2)) * m2 if k2 else 0
        proj_total = proj_avg1 + proj_avg2
        proj_html = f'''
        <div style="margin-top:16px;padding:12px 16px;background:linear-gradient(90deg, rgba(139,92,246,0.1) 0%, rgba(139,92,246,0.2) 100%);border-left:4px solid #8b5cf6;border-radius:6px;display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.5rem;">✨</span>
                <div>
                    <div style="color:#c4b5fd;font-weight:700;font-size:0.95rem;">Projeção do Draft (Kills)</div>
                    <div style="color:#94a3b8;font-size:0.8rem;">Ajuste baseado na intensidade de combate (KPM) da composição.</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#64748b;font-size:0.8rem;text-decoration:line-through;">Média Base: {st["avg"]:.1f}</div>
                <div style="color:#e2e8f0;font-size:1.2rem;font-weight:800;">Proj: <span style="color:#a78bfa;">{proj_total:.1f}</span></div>
            </div>
        </div>
        '''

    # Data-based comments
    comments = []
    if st["avg"] > 25:
        pct_25 = sum(1 for v in total if v > 22.5) / len(total) * 100
        comments.append(f'⚔️ <b>Média de {st["avg"]:.1f} abates totais.</b> Esses times geram jogos sangrentos — <b>Over 22.5 kills</b> cobriu em <b>{pct_25:.0f}%</b> dos jogos históricos. Aposta de alta confiança.')
    elif st["avg"] < 20:
        pct_20 = sum(1 for v in total if v <= 20.5) / len(total) * 100
        comments.append(f'🧊 <b>Média baixa de {st["avg"]:.1f} abates.</b> Partidas controladas com poucas lutas. <b>Under 22.5 kills</b> cobriu em <b>{pct_20:.0f}%</b> dos jogos. Favorável para apostas conservadoras.')
    if st["std"] > 5:
        comments.append(f'🎲 <b>Alta volatilidade (σ={st["std"]:.1f}).</b> Os resultados variam muito — jogos podem ser stomps ou disputas equilibradas. Linhas próximas da média têm risco elevado; considere linhas mais extremas.')
    elif st["std"] < 3:
        comments.append(f'🎯 <b>Consistência alta (σ={st["std"]:.1f}).</b> Resultados previsíveis — a maioria dos jogos cai próximo da média ({st["avg"]:.1f}). Linhas próximas da média são mais seguras.')
    return (fig_to_html(fig) + f'<div style="margin-top:8px;">{stats_html(st)}</div>' + proj_html + bets
            + explain("A distribuição do <b>total de kills na partida</b> (soma). É guiada pela métrica global <b>CKPM</b> detalhada acima. Em jogos com times sanguinários, a cauda longa no gráfico encosta nos 40-50 abates.")
            + data_comment(comments))


def gen_kills_por_time(s1, s2, t1, t2, mult1=None, mult2=None):
    """Distribuição de kills por time (subplots lado a lado)."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{t1}", f"{t2}"], horizontal_spacing=0.1)
    stats_htmls = []
    for col, (stats, team, bar_color, line_color) in enumerate([(s1, t1, "#3b82f6", "#60a5fa"), (s2, t2, "#ef4444", "#f87171")], 1):
        raw = int_list(stats.get("kills_history", []))
        if not raw:
            continue
        st = calc_stats(raw)
        counts = Counter(raw)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=team, marker_color=bar_color, marker_line_color=line_color, marker_line_width=1, showlegend=False, text=[str(c) for c in y_vals], textposition="outside"), row=1, col=col)
        fig.add_vline(x=st["avg"], line=dict(color=line_color, width=2.5, dash="dash"), row=1, col=col)
        avg_line = round(st["avg"] * 2) / 2
        pct_over = sum(1 for v in raw if v > avg_line) / len(raw) * 100
        stats_htmls.append(f'<div style="margin-top:4px;"><span style="color:{line_color};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(pct_over)} <b>Over {avg_line:.1f} kills</b></div>')

    layout = base_layout("🎯 Distribuição de Kills Individuais", height=420)
    layout["xaxis"] = dict(title="Kills do Time", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["xaxis2"] = dict(title="Kills do Time", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis2"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    fig.update_layout(**layout)
    
    proj_html = ""
    if mult1 and mult2:
        raw1 = int_list(s1.get("kills_history", [])); avg1 = sum(raw1)/len(raw1) if raw1 else 0
        raw2 = int_list(s2.get("kills_history", [])); avg2 = sum(raw2)/len(raw2) if raw2 else 0
        m1 = mult1.get("kills", 1.0); m2 = mult2.get("kills", 1.0)
        
        proj_html += f'''
        <div style="margin-top:16px;padding:12px 16px;background:linear-gradient(90deg, rgba(139,92,246,0.1) 0%, rgba(139,92,246,0.2) 100%);border-left:4px solid #8b5cf6;border-radius:6px;display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.5rem;">✨</span>
                <div>
                    <div style="color:#c4b5fd;font-weight:700;font-size:0.95rem;">Projeção do Draft (Kills p/ Time)</div>
                    <div style="color:#94a3b8;font-size:0.8rem;">Como os campeões aceleram ou atrasam alvos individuais.</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#e2e8f0;font-size:1.0rem;">{t1}: <span style="color:#60a5fa;text-decoration:line-through;font-size:0.8rem;">{avg1:.1f}</span> ➡️ <b style="color:#3b82f6;">{avg1*m1:.1f}</b></div>
                <div style="color:#e2e8f0;font-size:1.0rem;">{t2}: <span style="color:#f87171;text-decoration:line-through;font-size:0.8rem;">{avg2:.1f}</span> ➡️ <b style="color:#ef4444;">{avg2*m2:.1f}</b></div>
            </div>
        </div>
        '''

    # Data-based comments
    comments = []
    raw1 = int_list(s1.get("kills_history", []))
    raw2 = int_list(s2.get("kills_history", []))
    avg1_k = sum(raw1) / len(raw1) if raw1 else 0
    avg2_k = sum(raw2) / len(raw2) if raw2 else 0
    if avg1_k > 0 and avg2_k > 0:
        ratio = max(avg1_k, avg2_k) / min(avg1_k, avg2_k)
        dominant = t1 if avg1_k > avg2_k else t2
        weaker = t2 if avg1_k > avg2_k else t1
        if ratio > 1.25:
            comments.append(f'🎯 <b>{dominant} é {ratio:.1f}x mais letal</b> em kills individuais (média {max(avg1_k,avg2_k):.1f} vs {min(avg1_k,avg2_k):.1f}). Handicap de kills favorece {dominant} — Over individual também tem valor.')
        else:
            comments.append(f'⚖️ <b>Produção de kills equilibrada</b> ({t1}: {avg1_k:.1f} vs {t2}: {avg2_k:.1f}). Diferença pequena dificulta apostas de handicap — foque em Over/Under total.')
    egr1 = (s1.get("fb_rate", 0) + s1.get("fd_rate", 0)) / 2
    egr2 = (s2.get("fb_rate", 0) + s2.get("fd_rate", 0)) / 2
    for team, stats_t, avg_k, egr in [(t1, s1, avg1_k, egr1), (t2, s2, avg2_k, egr2)]:
        if avg_k > 12 and egr < 40:
            comments.append(f'⚠️ <b>{team} tem muitas kills ({avg_k:.1f}) mas EGR baixo ({egr:.0f}%).</b> Isso pode significar que o time está reagindo a pressão inimiga ao invés de liderar — kills reativas nem sempre se convertem em vitórias.')
    return (fig_to_html(fig) + "".join(stats_htmls) + proj_html
            + explain("A <b>Odd ideal</b> exibida refere-se à entrada <b>Over X.X kills</b> (arredondamento da média). Se o time puxar mais que a média histórica, a linha é coberta. Kills por time medem a pressão terminal, mas times com alta kill rate sem EGR alto podem estar apenas sendo engajados frequentemente.")
            + data_comment(comments))


def gen_handicap(s1, s2, t1, t2, mult1=None, mult2=None):
    """Gráfico de Handicap (kill diff) com entradas de aposta e explicação."""
    fig = go.Figure()
    odds_html = ""
    bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas de Handicap sugeridas:</b><br>'
    for st_data, team, bar_col, line_col in [(s1, t1, "rgba(59,130,246,0.7)", "#60a5fa"), (s2, t2, "rgba(239,68,68,0.7)", "#f87171")]:
        data = [int(round(v)) for v in st_data.get("kill_diff_history", []) if v is not None]
        if not data:
            continue
        st = calc_stats(data)
        counts = Counter(data)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=f"{team} (μ={st['avg']:+.1f})", marker_color=bar_col, marker_line_color=line_col, marker_line_width=1))
        pct_pos = sum(1 for v in data if v > 0) / len(data) * 100
        odds_html += f'<div style="margin-top:4px;"><span style="color:{line_col};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(pct_pos)} <b>Handicap 0 (Positivo > 0 kills)</b></div>'
        bets += '<div class="bets-grid">'
        for hc_line in [-5.5, -4.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
            prob = sum(1 for v in data if v > hc_line) / len(data) * 100
            sign = "+" if hc_line > 0 else ""
            bets += bet_line(team, "Handicap", f"{sign}{hc_line:.1f} kills", prob, len(data),
                f"Em {sum(1 for v in data if v > hc_line)} de {len(data)} jogos, {team} teve diff > {hc_line:+.1f}. "
                f"Média de handicap: {st['avg']:+.1f}, Mediana: {st['med']:+.1f}, Desvio Padrão: {st['std']:.1f}. "
                f"{'Linha conservadora abaixo da média — alta cobertura.' if hc_line < st['avg'] else 'Linha agressiva acima da média — precisa de domínio claro.'}")
        bets += '</div><br>'
    bets += '</div>'

    handicap_explain = (
        '<div class="explain-box" style="margin-top:14px;border-left-color:#eab308;">'
        '🎮 <b>O que é o Handicap de Kills?</b><br>'
        'O Handicap mede a <b>diferença entre kills do time e kills sofridas</b> (teamkills - teamdeaths). '
        'Na prática, funciona assim:<br><br>'
        '<b>Exemplo 1:</b> Se você aposta em <b>FURIA Handicap -3.5</b>, a FURIA precisa vencer a partida com pelo '
        'menos <b>4 kills a mais</b> que o adversário (ex: 15×11 = diff +4 ✔️, 12×10 = diff +2 ❌).<br>'
        '<b>Exemplo 2:</b> Se você aposta em <b>Sentinels Handicap +5.5</b>, os Sentinels podem até <b>perder por '
        'até 5 kills de diferença</b> e sua aposta cobre (ex: 8×12 = diff -4 ✔️, 5×12 = diff -7 ❌).<br><br>'
        '<b>Handicap negativo (-)</b> = time precisa dominar. <b>Handicap positivo (+)</b> = time recebe "vantagem" virtual. '
        'Quanto mais extrema a linha, maior a odd e o risco.'
        '</div>'
    )

    fig.add_vline(x=0, line=dict(color="#94a3b8", width=1.5))
    layout = base_layout("📊 Handicap de Kills (Kill Diff)", height=380)
    layout["barmode"] = "overlay"
    layout["xaxis"]["title"] = "Diferença de Kills (positivo = dominou)"
    fig.update_layout(**layout)
    
    proj_html = ""
    if mult1 and mult2:
        raw1 = int_list(s1.get("kills_history", [])); avg1 = sum(raw1)/len(raw1) if raw1 else 0
        raw2 = int_list(s2.get("kills_history", [])); avg2 = sum(raw2)/len(raw2) if raw2 else 0
        m1 = mult1.get("kills", 1.0); m2 = mult2.get("kills", 1.0)
        proj_diff = (avg1*m1) - (avg2*m2)
        proj_html = f'''
        <div style="margin-top:16px;padding:12px 16px;background:linear-gradient(90deg, rgba(139,92,246,0.1) 0%, rgba(139,92,246,0.2) 100%);border-left:4px solid #8b5cf6;border-radius:6px;display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.5rem;">✨</span>
                <div>
                    <div style="color:#c4b5fd;font-weight:700;font-size:0.95rem;">Projeção do Draft (Diferença de Kills)</div>
                    <div style="color:#94a3b8;font-size:0.8rem;">Expectativa ajustada de Handicap Natural entre as duas composições.</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#e2e8f0;font-size:1.2rem;font-weight:800;">Proj: <span style="color:#a78bfa;">{proj_diff:+.1f}</span></div>
            </div>
        </div>
        '''

    # Data-based comments
    comments = []
    diff1 = [int(round(v)) for v in s1.get("kill_diff_history", []) if v is not None]
    diff2 = [int(round(v)) for v in s2.get("kill_diff_history", []) if v is not None]
    if diff1:
        avg_d1 = sum(diff1) / len(diff1)
        if avg_d1 > 3:
            pct_35 = sum(1 for v in diff1 if v > 3.5) / len(diff1) * 100
            comments.append(f'📈 <b>{t1} domina historicamente</b> com handicap médio de <b>{avg_d1:+.1f}</b>. Handicap -3.5 cobriu em {pct_35:.0f}% dos jogos. Time consistente para apostas de handicap negativo.')
        elif avg_d1 < -3:
            pct_p35 = sum(1 for v in diff1 if v > -3.5) / len(diff1) * 100
            comments.append(f'📉 <b>{t1} costuma perder por margem grande</b> (média {avg_d1:+.1f}). Handicap +3.5 cobriu em {pct_p35:.0f}% dos jogos — proteção viável como aposta de segurança.')
    if diff2:
        avg_d2 = sum(diff2) / len(diff2)
        if avg_d2 > 3:
            pct_35 = sum(1 for v in diff2 if v > 3.5) / len(diff2) * 100
            comments.append(f'📈 <b>{t2} domina historicamente</b> com handicap médio de <b>{avg_d2:+.1f}</b>. Handicap -3.5 cobriu em {pct_35:.0f}% dos jogos.')
        elif avg_d2 < -3:
            pct_p35 = sum(1 for v in diff2 if v > -3.5) / len(diff2) * 100
            comments.append(f'📉 <b>{t2} costuma perder por margem grande</b> (média {avg_d2:+.1f}). Handicap +3.5 cobriu em {pct_p35:.0f}%.')
    if diff1 and diff2:
        avg_d1 = sum(diff1) / len(diff1)
        avg_d2 = sum(diff2) / len(diff2)
        if abs(avg_d1) < 2 and abs(avg_d2) < 2:
            comments.append(f'⚖️ <b>Ambos os times têm handicap próximo de zero.</b> Jogos tendem a ser equilibrados em kills — linhas de handicap extremas (-4.5, +4.5) têm baixa cobertura. Foque em handicap ±1.5.')
    return (fig_to_html(fig) + odds_html + handicap_explain + proj_html + bets
            + explain("A <b>Odd ideal</b> mostrada acima refere-se à entrada <b>Handicap 0</b> (mais kills que mortes). Clique nas entradas para ver o detalhamento individual.")
            + data_comment(comments))


def gen_duracao(s1, s2, t1, t2, mult1=None, mult2=None):
    """Distribuição de duração do mapa com entradas Over/Under."""
    all_dur = [v for v in s1.get("duration_history", []) + s2.get("duration_history", []) if v]
    if not all_dur:
        return ""
    st = calc_stats(all_dur)
    fig = go.Figure()
    for stats, team, color in [(s1, t1, "rgba(59,130,246,0.55)"), (s2, t2, "rgba(239,68,68,0.55)")]:
        data = [v for v in stats.get("duration_history", []) if v]
        if data:
            fig.add_trace(go.Histogram(x=data, name=team, marker_color=color, opacity=0.7, xbins=dict(size=2)))
    fig.add_vline(x=st["avg"], line=dict(color="#10b981", width=2.5, dash="dash"))
    layout = base_layout("⏱️ Duração do Mapa (Pace Control)", height=380)
    layout["barmode"] = "overlay"
    layout["xaxis"]["title"] = "Duração (minutos)"
    fig.update_layout(**layout)

    bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas de Duração sugeridas:</b><br>'
    for lv in [25.5, 28.5, 31.5, 34.5, 37.5]:
        p_over = sum(1 for v in all_dur if v > lv) / len(all_dur) * 100
        p_under = 100 - p_over
        bets += bet_line(f"{t1}+{t2}", "Over", f"{lv}min", p_over, len(all_dur),
            f"Em {sum(1 for v in all_dur if v > lv)} de {len(all_dur)} jogos a duração excedeu {lv}min. "
            f"Média: {st['avg']:.1f}min, Mediana: {st['med']:.1f}min. "
            f"{'Linha conservadora.' if lv < st['avg'] else 'Linha agressiva — requer jogos longos.'}")
        bets += bet_line(f"{t1}+{t2}", "Under", f"{lv}min", p_under, len(all_dur),
            f"Em {sum(1 for v in all_dur if v <= lv)} de {len(all_dur)} jogos a duração foi ≤ {lv}min. "
            f"{'Favorável: linha acima da média.' if lv > st['avg'] else 'Arriscado: linha abaixo da média.'}")
        bets += '<br>'
    bets += '</div>'

    proj_html = ""
    if mult1 and mult2:
        m1 = mult1.get("duration", 1.0); m2 = mult2.get("duration", 1.0)
        d1 = [v for v in s1.get("duration_history", []) if v]
        d2 = [v for v in s2.get("duration_history", []) if v]
        proj_dur1 = (sum(d1)/len(d1)) * m1 if d1 else 0
        proj_dur2 = (sum(d2)/len(d2)) * m2 if d2 else 0
        proj_total = (proj_dur1 + proj_dur2) / 2
        proj_html = f'''
        <div style="margin-top:16px;padding:12px 16px;background:linear-gradient(90deg, rgba(139,92,246,0.1) 0%, rgba(139,92,246,0.2) 100%);border-left:4px solid #8b5cf6;border-radius:6px;display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.5rem;">✨</span>
                <div>
                    <div style="color:#c4b5fd;font-weight:700;font-size:0.95rem;">Projeção do Draft (Duração Inicial)</div>
                    <div style="color:#94a3b8;font-size:0.8rem;">Puxado pelos perfis de scaling (Mid-Late vs Early Game).</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#64748b;font-size:0.8rem;text-decoration:line-through;">Média Base: {st["avg"]:.1f}min</div>
                <div style="color:#e2e8f0;font-size:1.2rem;font-weight:800;">Proj: <span style="color:#a78bfa;">{proj_total:.1f}min</span></div>
            </div>
        </div>
        '''

    # Data-based comments
    comments = []
    if st["avg"] > 33:
        pct_31 = sum(1 for v in all_dur if v > 31.5) / len(all_dur) * 100
        comments.append(f'⏱️ <b>Jogos longos (média {st["avg"]:.1f}min).</b> Esses times tendem a arrastar partidas. <b>Over 31.5min</b> cobriu em <b>{pct_31:.0f}%</b> dos jogos. Favorável para apostas de duração longa e correlacionado com <b>Over em Barões</b>.')
    elif st["avg"] < 28:
        pct_28 = sum(1 for v in all_dur if v <= 28.5) / len(all_dur) * 100
        comments.append(f'⚡ <b>Jogos rápidos (média {st["avg"]:.1f}min).</b> Partidas decididas cedo. <b>Under 28.5min</b> cobriu em <b>{pct_28:.0f}%</b>. Favorável para <b>Under em Barões 0.5</b> (jogos curtos raramente chegam ao Baron).')
    else:
        comments.append(f'⏰ <b>Duração média padrão ({st["avg"]:.1f}min).</b> Sem tendência clara de jogos curtos ou longos. Linha de 31.5min é o pivot — analise EGR e MLR para determinar direção.')
    d1_data = [v for v in s1.get("duration_history", []) if v]
    d2_data = [v for v in s2.get("duration_history", []) if v]
    if d1_data and d2_data:
        avg_d1 = sum(d1_data) / len(d1_data)
        avg_d2 = sum(d2_data) / len(d2_data)
        if abs(avg_d1 - avg_d2) > 3:
            faster = t1 if avg_d1 < avg_d2 else t2
            slower = t2 if avg_d1 < avg_d2 else t1
            comments.append(f'📊 <b>Diferença de ritmo:</b> {faster} joga partidas ~{abs(avg_d1-avg_d2):.0f}min mais curtas que {slower}. O estilo do {faster} (early-game) pode forçar resolução rápida.')
    return (fig_to_html(fig) + f'<div style="margin-top:8px;">{stats_html(st, "min")}</div>' + proj_html + bets
            + explain("A <b>Duração (AGT - Avg Game Time)</b> reflete se os times controlam o pace. Um time de EGR baixo e AGT alto joga na defensiva pelas torres e falha nas chamadas de Barão.")
            + data_comment(comments))


# ============================================================================
# Objective Distribution Charts (Dragons, Torres, Barões)
# ============================================================================

def gen_dragons(s1, s2, t1, t2, mult1=None, mult2=None):
    """Distribuição de dragões por time (subplots lado a lado) + totais combinados."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{t1}", f"{t2}"], horizontal_spacing=0.1)
    combo_html = ""
    for col, (stats, team, bar_c, line_c) in enumerate([(s1, t1, "#f97316", "#fb923c"), (s2, t2, "#ef4444", "#f87171")], 1):
        raw = int_list(stats.get("dragons_history", []))
        if not raw:
            continue
        st = calc_stats(raw)
        counts = Counter(raw)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=team, marker_color=bar_c, marker_line_color=line_c, marker_line_width=1, showlegend=False, text=[str(c) for c in y_vals], textposition="outside"), row=1, col=col)
        fig.add_vline(x=st["avg"], line=dict(color=line_c, width=2.5, dash="dash"), row=1, col=col)
        combo_html += f'<div style="margin-top:4px;"><span style="color:{line_c};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(sum(1 for v in raw if v > 3.5)/len(raw)*100)} <b>Over 3.5 Dragões</b></div>'

    layout = base_layout("🐉 Distribuição de Dragões por Time", height=400)
    layout["xaxis"] = dict(title="Dragões Conquistados", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["xaxis2"] = dict(title="Dragões Conquistados", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis2"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    fig.update_layout(**layout)

    # Total combinado
    d1 = int_list(s1.get("dragons_history", []))
    d2 = int_list(s2.get("dragons_history", []))
    min_len = min(len(d1), len(d2))
    total_html = ""
    if min_len > 0:
        total = [d1[i] + d2[i] for i in range(min_len)]
        st_t = calc_stats(total)
        bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas Total Dragões (Partida):</b><br>'
        for lv in [3.5, 4.5, 5.5]:
            prob_o = sum(1 for v in total if v > lv) / len(total) * 100
            bets += bet_line(f"{t1}+{t2}", "Over", f"{lv:.1f} dragões", prob_o, len(total),
                f"Em {sum(1 for v in total if v > lv)} de {len(total)} jogos, o total de dragões foi > {lv:.1f}. "
                f"Média combinada: {st_t['avg']:.1f}. Dragon Soul exige 4 dragões para um time.")
            bets += '<br>'
        bets += '</div>'
        total_html = f'<div style="margin-top:8px;">{stats_html(st_t, " dragões (total)")}</div>' + bets

    proj_html = ""
    if mult1 and mult2:
        raw1 = int_list(s1.get("dragons_history", [])); avg1 = sum(raw1)/len(raw1) if raw1 else 0
        raw2 = int_list(s2.get("dragons_history", [])); avg2 = sum(raw2)/len(raw2) if raw2 else 0
        m1 = mult1.get("dragons", 1.0); m2 = mult2.get("dragons", 1.0)
        proj_total = (avg1*m1) + (avg2*m2)
        proj_html = f'''
        <div style="margin-top:16px;padding:12px 16px;background:linear-gradient(90deg, rgba(139,92,246,0.1) 0%, rgba(139,92,246,0.2) 100%);border-left:4px solid #8b5cf6;border-radius:6px;display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.5rem;">✨</span>
                <div>
                    <div style="color:#c4b5fd;font-weight:700;font-size:0.95rem;">Projeção do Draft (Dragões Totais)</div>
                    <div style="color:#94a3b8;font-size:0.8rem;">Ajuste baseado na sinergia de objetivos/bot-side.</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#64748b;font-size:0.8rem;text-decoration:line-through;">Média Base: {avg1+avg2:.1f}</div>
                <div style="color:#e2e8f0;font-size:1.2rem;font-weight:800;">Proj: <span style="color:#a78bfa;">{proj_total:.1f}</span></div>
            </div>
        </div>
        '''

    # Data-based comments
    comments = []
    dr1 = int_list(s1.get("dragons_history", []))
    dr2 = int_list(s2.get("dragons_history", []))
    avg_dr1 = sum(dr1) / len(dr1) if dr1 else 0
    avg_dr2 = sum(dr2) / len(dr2) if dr2 else 0
    for team, avg_dr, fd_rate in [(t1, avg_dr1, s1.get("fd_rate", 0)), (t2, avg_dr2, s2.get("fd_rate", 0))]:
        if fd_rate > 60 and avg_dr > 3:
            pct_35 = sum(1 for v in (dr1 if team == t1 else dr2) if v > 3.5) / len(dr1 if team == t1 else dr2) * 100 if (dr1 if team == t1 else dr2) else 0
            comments.append(f'🐉 <b>{team} domina objetivos bot-side</b> (FD% {fd_rate:.0f}%, média {avg_dr:.1f} dragões). <b>Over 3.5 dragões</b> para o time cobriu em <b>{pct_35:.0f}%</b>. Dragon Soul é muito provável.')
        elif avg_dr < 2:
            comments.append(f'⚠️ <b>{team} conquista poucos dragões (média {avg_dr:.1f}).</b> Fraco no controle bot-side — dificilmente chega ao Dragon Soul. Under em dragões individuais pode ter valor.')
    if min_len > 0 and total:
        avg_total_dr = sum(total) / len(total)
        if avg_total_dr > 6:
            comments.append(f'🔥 <b>Média de {avg_total_dr:.1f} dragões totais por jogo.</b> Alta contestação de dragões indica jogos longos com múltiplas lutas no rio. Over 5.5 dragões totais é uma aposta consistente.')
    return (fig_to_html(fig) + combo_html + total_html + proj_html
            + explain("O controle de <b>Dragões</b> é um proxy do domínio bot-side e da visão do rio. Times com FD% alto tendem a acumular 3-4 dragões de modo mais consisteente. O Dragon Soul (~4 dragões) é um gamechanger.")
            + data_comment(comments))


def gen_torres(s1, s2, t1, t2, mult1=None, mult2=None):
    """Distribuição de torres destruídas por time (subplots lado a lado)."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{t1}", f"{t2}"], horizontal_spacing=0.1)
    combo_html = ""
    for col, (stats, team, bar_c, line_c) in enumerate([(s1, t1, "#eab308", "#facc15"), (s2, t2, "#ef4444", "#f87171")], 1):
        raw = int_list(stats.get("towers_history", []))
        if not raw:
            continue
        st = calc_stats(raw)
        counts = Counter(raw)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=team, marker_color=bar_c, marker_line_color=line_c, marker_line_width=1, showlegend=False, text=[str(c) for c in y_vals], textposition="outside"), row=1, col=col)
        fig.add_vline(x=st["avg"], line=dict(color=line_c, width=2.5, dash="dash"), row=1, col=col)
        combo_html += f'<div style="margin-top:4px;"><span style="color:{line_c};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(sum(1 for v in raw if v > 5.5)/len(raw)*100)} <b>Over 5.5 Torres</b></div>'

    layout = base_layout("🏰 Distribuição de Torres Destruídas por Time", height=400)
    layout["xaxis"] = dict(title="Torres Destruídas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["xaxis2"] = dict(title="Torres Destruídas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis2"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    fig.update_layout(**layout)

    # Total combinado
    t1_d = int_list(s1.get("towers_history", []))
    t2_d = int_list(s2.get("towers_history", []))
    min_len = min(len(t1_d), len(t2_d))
    total_html = ""
    if min_len > 0:
        total = [t1_d[i] + t2_d[i] for i in range(min_len)]
        st_t = calc_stats(total)
        bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas Total Torres (Partida):</b><br>'
        for lv in [10.5, 12.5, 14.5]:
            prob_o = sum(1 for v in total if v > lv) / len(total) * 100
            bets += bet_line(f"{t1}+{t2}", "Over", f"{lv:.1f} torres", prob_o, len(total),
                f"Em {sum(1 for v in total if v > lv)} de {len(total)} jogos, o total de torres foi > {lv:.1f}. "
                f"Média combinada: {st_t['avg']:.1f}. Existem 11 torres por time (22 no total).")
            bets += '<br>'
        bets += '</div>'
        total_html = f'<div style="margin-top:8px;">{stats_html(st_t, " torres (total)")}</div>' + bets

    proj_html = ""
    if mult1 and mult2:
        raw1 = int_list(s1.get("towers_history", [])); avg1 = sum(raw1)/len(raw1) if raw1 else 0
        raw2 = int_list(s2.get("towers_history", [])); avg2 = sum(raw2)/len(raw2) if raw2 else 0
        m1 = mult1.get("towers", 1.0); m2 = mult2.get("towers", 1.0)
        proj_total = (avg1*m1) + (avg2*m2)
        proj_html = f'''
        <div style="margin-top:16px;padding:12px 16px;background:linear-gradient(90deg, rgba(139,92,246,0.1) 0%, rgba(139,92,246,0.2) 100%);border-left:4px solid #8b5cf6;border-radius:6px;display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.5rem;">✨</span>
                <div>
                    <div style="color:#c4b5fd;font-weight:700;font-size:0.95rem;">Projeção do Draft (Torres Totais)</div>
                    <div style="color:#94a3b8;font-size:0.8rem;">Ajuste baseado no poder de avanço e siege da composição.</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#64748b;font-size:0.8rem;text-decoration:line-through;">Média Base: {avg1+avg2:.1f}</div>
                <div style="color:#e2e8f0;font-size:1.2rem;font-weight:800;">Proj: <span style="color:#a78bfa;">{proj_total:.1f}</span></div>
            </div>
        </div>
        '''

    # Data-based comments
    comments = []
    tw1 = int_list(s1.get("towers_history", []))
    tw2 = int_list(s2.get("towers_history", []))
    avg_tw1 = sum(tw1) / len(tw1) if tw1 else 0
    avg_tw2 = sum(tw2) / len(tw2) if tw2 else 0
    for team, avg_tw in [(t1, avg_tw1), (t2, avg_tw2)]:
        if avg_tw > 7:
            raw_t = tw1 if team == t1 else tw2
            pct_55 = sum(1 for v in raw_t if v > 5.5) / len(raw_t) * 100 if raw_t else 0
            comments.append(f'🏰 <b>{team} destrói média de {avg_tw:.1f} torres</b> — excelente conversão de vantagem. <b>Over 5.5 torres</b> cobriu em <b>{pct_55:.0f}%</b>. Time que fecha jogos destruindo estruturas.')
        elif avg_tw < 4:
            comments.append(f'⚠️ <b>{team} destrói poucas torres (média {avg_tw:.1f}).</b> Time que tem dificuldade em converter vantagens em estruturas — pode indicar passividade ou foco excessivo em lutas.')
    if abs(avg_tw1 - avg_tw2) > 2:
        dom_t = t1 if avg_tw1 > avg_tw2 else t2
        comments.append(f'📊 <b>Diferença de {abs(avg_tw1-avg_tw2):.1f} torres entre os times.</b> {dom_t} é muito superior em siege. Handicap de torres pode ter valor.')
    return (fig_to_html(fig) + combo_html + total_html + proj_html
            + explain("O <b>MLR (Mid/Late Rating)</b> mostra que torres destruídas indicam conversão de vantagem. Times que pegam Barão mas não derrubam torres são passivos e falham em <i>snowballar</i>.")
            + data_comment(comments))


def gen_baroes(s1, s2, t1, t2, mult1=None, mult2=None):
    """Distribuição de barões por time (subplots lado a lado)."""
    fig = make_subplots(rows=1, cols=2, subplot_titles=[f"{t1}", f"{t2}"], horizontal_spacing=0.1)
    combo_html = ""
    for col, (stats, team, bar_c, line_c) in enumerate([(s1, t1, "#10b981", "#34d399"), (s2, t2, "#ef4444", "#f87171")], 1):
        raw = int_list(stats.get("barons_history", []))
        if not raw:
            continue
        st = calc_stats(raw)
        counts = Counter(raw)
        x_vals = sorted(counts.keys())
        y_vals = [counts[v] for v in x_vals]
        fig.add_trace(go.Bar(x=x_vals, y=y_vals, name=team, marker_color=bar_c, marker_line_color=line_c, marker_line_width=1, showlegend=False, text=[str(c) for c in y_vals], textposition="outside"), row=1, col=col)
        fig.add_vline(x=st["avg"], line=dict(color=line_c, width=2.5, dash="dash"), row=1, col=col)
        combo_html += f'<div style="margin-top:4px;"><span style="color:{line_c};font-weight:700;">{team}:</span> {stats_html(st)} {odd_badge(sum(1 for v in raw if v > 0.5)/len(raw)*100)} <b>Over 0.5 Barões</b></div>'

    layout = base_layout("💚 Distribuição de Barões por Time", height=400)
    layout["xaxis"] = dict(title="Barões Conquistados", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["xaxis2"] = dict(title="Barões Conquistados", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    layout["yaxis2"] = dict(title="Nº de Partidas", gridcolor="rgba(51,65,85,0.5)", zerolinecolor="#334155")
    fig.update_layout(**layout)

    # Total combinado
    b1 = int_list(s1.get("barons_history", []))
    b2 = int_list(s2.get("barons_history", []))
    min_len = min(len(b1), len(b2))
    total_html = ""
    if min_len > 0:
        total = [b1[i] + b2[i] for i in range(min_len)]
        st_t = calc_stats(total)
        bets = '<div style="margin-top:10px;"><b style="color:#e2e8f0;">📌 Entradas Total Barões (Partida):</b><br>'
        for lv in [0.5, 1.5]:
            prob_o = sum(1 for v in total if v > lv) / len(total) * 100
            bets += bet_line(f"{t1}+{t2}", "Over", f"{lv:.1f} barões", prob_o, len(total),
                f"Em {sum(1 for v in total if v > lv)} de {len(total)} jogos, o total de barões foi > {lv:.1f}. "
                f"Média combinada: {st_t['avg']:.1f}. Jogos que ultrapassam 25min tendem a ter pelo menos 1 Barão.")
            bets += '<br>'
        bets += '</div>'
        total_html = f'<div style="margin-top:8px;">{stats_html(st_t, " barões (total)")}</div>' + bets

    proj_html = ""
    if mult1 and mult2:
        raw1 = int_list(s1.get("barons_history", [])); avg1 = sum(raw1)/len(raw1) if raw1 else 0
        raw2 = int_list(s2.get("barons_history", [])); avg2 = sum(raw2)/len(raw2) if raw2 else 0
        m1 = mult1.get("barons", 1.0); m2 = mult2.get("barons", 1.0)
        proj_total = (avg1*m1) + (avg2*m2)
        proj_html = f'''
        <div style="margin-top:16px;padding:12px 16px;background:linear-gradient(90deg, rgba(139,92,246,0.1) 0%, rgba(139,92,246,0.2) 100%);border-left:4px solid #8b5cf6;border-radius:6px;display:flex;align-items:center;justify-content:space-between;">
            <div style="display:flex;align-items:center;gap:12px;">
                <span style="font-size:1.5rem;">✨</span>
                <div>
                    <div style="color:#c4b5fd;font-weight:700;font-size:0.95rem;">Projeção do Draft (Barões Totais)</div>
                    <div style="color:#94a3b8;font-size:0.8rem;">Ajustado pelo controle e speed de Nashor.</div>
                </div>
            </div>
            <div style="text-align:right;">
                <div style="color:#64748b;font-size:0.8rem;text-decoration:line-through;">Média Base: {avg1+avg2:.1f}</div>
                <div style="color:#e2e8f0;font-size:1.2rem;font-weight:800;">Proj: <span style="color:#a78bfa;">{proj_total:.1f}</span></div>
            </div>
        </div>
        '''

    # Data-based comments
    comments = []
    br1 = int_list(s1.get("barons_history", []))
    br2 = int_list(s2.get("barons_history", []))
    fbr1 = s1.get("fbaron_rate", 0)
    fbr2 = s2.get("fbaron_rate", 0)
    for team, br, fbr in [(t1, br1, fbr1), (t2, br2, fbr2)]:
        if fbr > 60:
            pct_05 = sum(1 for v in br if v > 0.5) / len(br) * 100 if br else 0
            comments.append(f'💚 <b>{team} controla o Baron Pit ({fbr:.0f}% First Baron).</b> Correlação altíssima com vitória. <b>Over 0.5 Barões</b> cobriu em <b>{pct_05:.0f}%</b> dos jogos. Aposta de alta confiança combinada com ML do time.')
        elif fbr < 30:
            comments.append(f'⚠️ <b>{team} raramente conquista o First Baron ({fbr:.0f}%).</b> Sem controle do Baron Pit, o time depende de teamfights desesesperadas no late. Dificilmente fecha jogos longos.')
    if min_len > 0 and total:
        avg_total_b = sum(total) / len(total)
        if avg_total_b > 1.5:
            comments.append(f'🔥 <b>Média de {avg_total_b:.1f} barões por jogo.</b> Jogos tendem a ter múltiplos Barões — indicativo de partidas longas e com disputa de objetivos. <b>Over 1.5 Barões</b> tem valor.')
    return (fig_to_html(fig) + combo_html + total_html + proj_html
            + explain("O <b>Barão Nashor</b> é o principal indicador do MLR. Seu buff de empurro de lanes permite cercar torres e inibidores. Times que controlam o Baron Pit ditam o ritmo do mid-late game.")
            + data_comment(comments))


# ============================================================================
# Advanced Visualizations: Timeline, Radar & Vision
# ============================================================================

def gen_timeline_chart(s1, s2, t1, t2, mult1=None, mult2=None):
    """Gráfico de linha do tempo de Gold, CS e XP Difference com Projeção de Draft."""
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.08, 
                        subplot_titles=["Gold Difference", "CS Difference", "XP Difference"])
    
    x_vals = [10, 15, 20, 25]
    
    m1_adv = 1.0; m2_adv = 1.0
    if mult1 and mult2:
        m1_adv = (mult1.get("firstblood", 1.0) + mult1.get("firstdragon", 1.0) + mult1.get("kills", 1.0)) / 3
        m2_adv = (mult2.get("firstblood", 1.0) + mult2.get("firstdragon", 1.0) + mult2.get("kills", 1.0)) / 3

    for row, metric in enumerate(["golddiff", "csdiff", "xpdiff"], 1):
        for stats, team, color in [(s1, t1, "#3b82f6"), (s2, t2, "#ef4444")]:
            y_vals = [stats.get(f"{metric}at{m}", 0) for m in x_vals]
            fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines+markers",
                                     name=team, line=dict(color=color, width=3),
                                     marker=dict(size=8, symbol="circle"),
                                     showlegend=(row == 1)),
                          row=row, col=1)
            
            # Draft Projection Line
            if mult1 and mult2:
                proj_y = []
                for val in y_vals:
                    # If this is team 1, use m1_adv / m2_adv. If team 2, use m2_adv / m1_adv
                    ratio = (m1_adv / m2_adv) if team == t1 else (m2_adv / m1_adv)
                    
                    if val > 0: proj_val = val * ratio
                    else: proj_val = val / ratio if ratio > 0 else val
                    proj_y.append(proj_val)
                    
                proj_color = "#60a5fa" if team == t1 else "#f87171"
                fig.add_trace(go.Scatter(x=x_vals, y=proj_y, mode="lines",
                                         name=f"✨ {team} (Proj)", 
                                         line=dict(color=proj_color, width=2, dash="dot"),
                                         showlegend=(row == 1)),
                              row=row, col=1)

        # Linha Zero
        fig.add_hline(y=0, line=dict(color="#64748b", width=1.5, dash="dash"), row=row, col=1)

    layout = base_layout("📈 Evolução da Vantagem no Tempo (Timeline)", height=600)
    layout["xaxis3"] = dict(title="Minutos de Jogo", tickvals=x_vals, gridcolor="rgba(51,65,85,0.5)")
    for i in range(1, 4):
        layout[f"yaxis{i}"] = dict(gridcolor="rgba(51,65,85,0.5)", zeroline=False)
    fig.update_layout(**layout)
    
    html = fig_to_html(fig)
    if mult1 and mult2:
        html += f'''
        <div style="margin-top:16px;padding:12px 16px;background:linear-gradient(90deg, rgba(139,92,246,0.1) 0%, rgba(139,92,246,0.2) 100%);border-left:4px solid #8b5cf6;border-radius:6px;display:flex;align-items:center;">
            <span style="font-size:1.5rem;margin-right:12px;">✨</span>
            <div>
                <div style="color:#c4b5fd;font-weight:700;font-size:0.95rem;">Projeção de Snowball (Draft)</div>
                <div style="color:#94a3b8;font-size:0.8rem;">Diferença de aceleração Early Game: {t1} <b>{m1_adv:.2f}x</b> vs {t2} <b>{m2_adv:.2f}x</b>. Linhas pontilhadas (···) mostram a expectativa ajustada na timeline.</div>
            </div>
        </div>
        '''

    # Data-based comments
    comments = []
    gd15_1 = s1.get("golddiffat15", 0) or 0
    gd15_2 = s2.get("golddiffat15", 0) or 0
    gd10_1 = s1.get("golddiffat10", 0) or 0
    gd10_2 = s2.get("golddiffat10", 0) or 0
    for team, opp, gd10, gd15 in [(t1, t2, gd10_1, gd15_1), (t2, t1, gd10_2, gd15_2)]:
        if gd15 > 1000:
            comments.append(f'💰 <b>{team} domina com +{gd15:.0f}g aos 15min.</b> Vantagem significativa que historicamente se converte em vitória. Apostar <b>live no favorito early</b> pode ter odds piores — melhor valor no pré-jogo ou nos primeiros 5min.')
        elif gd15 < -1000:
            comments.append(f'📉 <b>{team} costuma estar {abs(gd15):.0f}g atrás aos 15min.</b> Se o MLR for alto, este é o time para apostar live após os 10-15min quando as odds estarão melhores.')
        if gd10 > 0 and gd15 < gd10 * 0.5:
            comments.append(f'🔄 <b>{team} perde vantagem entre 10 e 15min.</b> Começa bem (+{gd10:.0f}g@10) mas não sustenta ({gd15:+.0f}g@15). Possível fraqueza na transição para mid-game.')
    if abs(gd15_1) < 300 and abs(gd15_2) < 300:
        comments.append(f'⚖️ <b>Ambos os times chegam aos 15min equilibrados em ouro.</b> Early game competitivo — o jogo será decidido no mid/late. Apostas de duração Over e Barões ganham relevância.')
    return (html + 
            explain("A curva de <b>Diferença (Diff)</b> mostra o ritmo da partida. Se a linha pontilhada de projeção (✨) for mais alta que a histórica, o draft acelera a vantagem. "
                    "Dominar o <b>Early Game</b> (10-15m) no Ouro, CS e XP força o adversário ao desespero.")
            + data_comment(comments))

def gen_radar_dna(s1, s2, t1, t2):
    """Radar (Spider) Chart mapeando o DNA do time."""
    categories = ['Win Rate', 'EGR Score (Early)', 'MLR Score (Late)', 'Ação (KPM)']
    
    def calc_radar(stats):
        wr = stats.get("win_rate", 0)
        egr = (stats.get("fb_rate", 0) + stats.get("fd_rate", 0)) / 2
        mlr = min((stats.get("avg_barons", 0) + stats.get("avg_inhibitors", 0) * 1.5 + stats.get("avg_towers", 0) / 4) * 20, 100)
        kpm = min(stats.get("avg_kpm", 0) / 1.0 * 100, 100) # Norm 1.0 kpm
        return [wr, egr, mlr, kpm]

    fig = go.Figure()
    for stats, team, color in [(s1, t1, "rgba(59,130,246,0.3)"), (s2, t2, "rgba(239,68,68,0.3)")]:
        r_vals = calc_radar(stats)
        fig.add_trace(go.Scatterpolar(
            r=r_vals, theta=categories, fill='toself', name=team,
            marker=dict(color=color.replace("0.3", "1")), line=dict(width=2)
        ))
    
    layout = base_layout("🧬 DNA do Time (Radar de Atributos)", height=500)
    layout["polar"] = dict(
        radialaxis=dict(visible=True, range=[0, 100], gridcolor="#334155", tickfont=dict(size=10, color="#94a3b8")),
        angularaxis=dict(gridcolor="#334155", tickfont=dict(size=11, color="#f8fafc")),
        bgcolor="rgba(0,0,0,0)"
    )
    fig.update_layout(**layout)

    # Data-based comments — use EV Finder-aligned formulas (3-component EGR, aligned MLR)
    comments = []
    # EGR: 3 components (fb + fd + fherald) / 3 — aligned with EV Finder egr_score
    egr_1 = (s1.get("fb_rate", 0) + s1.get("fd_rate", 0) + s1.get("fherald_rate", 0)) / 3
    egr_2 = (s2.get("fb_rate", 0) + s2.get("fd_rate", 0) + s2.get("fherald_rate", 0)) / 3
    # MLR: aligned with EV Finder formula (barons + inhibitors + towers/5) / 3 * 20
    mlr_1 = min((s1.get("avg_barons", 0) + s1.get("avg_inhibitors", 0) + s1.get("avg_towers", 0) / 5) / 3 * 20, 100)
    mlr_2 = min((s2.get("avg_barons", 0) + s2.get("avg_inhibitors", 0) + s2.get("avg_towers", 0) / 5) / 3 * 20, 100)
    kpm_1 = min(s1.get("avg_kpm", 0) / 1.0 * 100, 100)
    kpm_2 = min(s2.get("avg_kpm", 0) / 1.0 * 100, 100)

    # Identify team profiles using EV-aligned metrics
    for team, egr_v, mlr_v, kpm_v in [(t1, egr_1, mlr_1, kpm_1), (t2, egr_2, mlr_2, kpm_2)]:
        if egr_v > 60 and kpm_v > 60:
            comments.append(f'⚔️ <b>{team} tem perfil AGRESSIVO</b> (EGR {egr_v:.0f}%, KPM {kpm_v:.0f}%). Busca jogos caóticos e rápidos. Favoreça <b>Over em kills</b> e <b>Under em duração</b> quando este time joga.')
        elif mlr_v > 60:
            comments.append(f'🧠 <b>{team} tem perfil CONTROLADO</b> (MLR {mlr_v:.0f}%). Joga por objetivos e controle de mapa. Favoreça <b>Over em duração</b> e <b>Over em Barões</b>.')

    # Profile clash using EV-aligned EGR/MLR
    if egr_1 > 55 and kpm_1 > 55 and mlr_2 > 55:
        comments.append(f'💥 <b>Duelo de estilos!</b> {t1} (agressivo/early) vs {t2} (controlado/late). A partida depende de quem impõe o ritmo. Se {t1} não dominar o early, {t2} tende a virar. Janela de aposta live nos 15min.')
    elif egr_2 > 55 and kpm_2 > 55 and mlr_1 > 55:
        comments.append(f'💥 <b>Duelo de estilos!</b> {t2} (agressivo/early) vs {t1} (controlado/late). A partida depende de quem impõe o ritmo. Se {t2} não dominar o early, {t1} tende a virar. Janela de aposta live nos 15min.')
    return (fig_to_html(fig) + 
            explain("O <b>Gráfico de Radar</b> é o padrão-ouro para ler o DNA dos times. Um time esticado em <i>EGR e Ação</i> busca jogos caóticos e curtos. Um dominando <i>MLR</i> joga pelas lutas de objetivos amplas.")
            + data_comment(comments))

def gen_vision_control(s1, s2, t1, t2):
    """Gráfico de controle de visão."""
    fig = go.Figure()
    
    metrics = [
        ("Wards Colocadas", "wardsplaced"),
        ("Wards Destruídas", "wardskilled"),
        ("Control Wards", "controlwardsbought")
    ]
    x_labels = [m[0] for m in metrics]
    
    for stats, team, color in [(s1, t1, "#60a5fa"), (s2, t2, "#f87171")]:
        y_vals = [stats.get(m[1], 0) for m in metrics]
        fig.add_trace(go.Bar(name=team, x=x_labels, y=y_vals, marker_color=color))

    layout = base_layout("👁️ Controle do Mapa (Visão)", height=350)
    layout["barmode"] = "group"
    layout["yaxis"]["title"] = "Média por Jogo"
    fig.update_layout(**layout)
    
    vspmm1 = s1.get("visionscore", 0)
    vspmm2 = s2.get("visionscore", 0)
    
    html = fig_to_html(fig)
    html += f'<div style="text-align:center;padding:12px;background:rgba(255,255,255,0.05);border-radius:8px;margin-top:10px;">'
    html += f'<strong style="color:#cbd5e1;">🎯 Vision Score Total (Média):</strong><br>'
    html += f'<span style="color:#60a5fa;font-size:1.1rem;font-weight:bold;">{t1}: {vspmm1:.1f}</span>'
    html += f'<span style="color:#94a3b8;margin:0 15px;">vs</span>'
    html += f'<span style="color:#f87171;font-size:1.1rem;font-weight:bold;">{t2}: {vspmm2:.1f}</span>'
    html += f'</div>'

    # Data-based comments
    comments = []
    wp1 = s1.get("wardsplaced", 0)
    wp2 = s2.get("wardsplaced", 0)
    wk1 = s1.get("wardskilled", 0)
    wk2 = s2.get("wardskilled", 0)
    cw1 = s1.get("controlwardsbought", 0)
    cw2 = s2.get("controlwardsbought", 0)
    for team, wp, wk, cw, vs, opp_wk in [(t1, wp1, wk1, cw1, vspmm1, wk2), (t2, wp2, wk2, cw2, vspmm2, wk1)]:
        if wk > opp_wk * 1.2:
            pct_more = ((wk / max(opp_wk, 0.1)) - 1) * 100
            comments.append(f'👁️ <b>{team} destrói {pct_more:.0f}% mais wards.</b> Controle de visão superior favorece apostas em <b>First Baron</b> e <b>First Dragon</b> — o time vê mais do mapa e prepara emboscadas.')
        if cw > 4:
            comments.append(f'🟣 <b>{team} compra muitas Control Wards ({cw:.1f}/jogo).</b> Investimento pesado em visão indica foco em controle de objetivos. Forte indicador de <b>First Baron</b>.')
    if vspmm1 > 0 and vspmm2 > 0:
        if abs(vspmm1 - vspmm2) > 0.5:
            vision_dom = t1 if vspmm1 > vspmm2 else t2
            comments.append(f'🎯 <b>{vision_dom} tem Vision Score superior</b> ({max(vspmm1,vspmm2):.1f} vs {min(vspmm1,vspmm2):.1f}). Controle de mapa é a base para objetivos neutros — Barão e Dragão favorecem {vision_dom}.')
    return (html + explain("A base do controle de macro no LoL é a <b>Visão</b>. Mais Wards Destruídas e Control Wards indicam foco em varrer a selva e preparar armadilhas em Barão/Dragão.")
            + data_comment(comments))


# ============================================================================
# Gold Layer Metrics (Advanced Betting)
# ============================================================================

def gen_gold_team_summary(g1, g2, t1, t2):
    """HTML para os novos índices da camada Gold (EGDI, Vision Efficiency, Throws)."""
    if not g1 or not g2:
        return ""
        
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#fbbf24;margin:0 0 16px 0;font-size:1.1rem;border-bottom:1px solid #78350f;padding-bottom:12px;">📈 Gold Layer Metrics (Team Level)</h3>'
    
    metrics = [
        ("Early Game Dominance Index (EGDI)", "egdi_score", "Índice composto que mede vantagens de ouro, XP e tropas aos 15 minutos. Valores > 0 indicam times que amassam no início. Ótimo para prop bets de early game/first tower.", True),
        ("Throw Rate (Entregas)", "throw_rate", "Chances de perder quando já está vencendo aos 15 min (>1k ouro) (%)", False),
        ("Comeback Rate (Viradas)", "comeback_rate", "Chances de vencer quando já está perdendo aos 15 min (<1k ouro) (%)", False),
        ("Vision Eff: Wards per Kill (WPK)", "wards_per_kill", "Wards gastas em média para conseguir 1 abate (menor é mais letal).", False),
        ("Vision Eff: Wards per Baron (WPB)", "wards_per_baron", "Wards gastas em média ao redor da conquista de um barão.", False)
    ]

    for title, key, desc, is_index in metrics:
        html += f'<div style="margin-bottom:16px;">'
        html += f'<div style="color:#e2e8f0;font-weight:600;font-size:0.9rem;margin-bottom:6px;">{title}</div>'
        
        for g_stats, team, color in [(g1, t1, "#60a5fa"), (g2, t2, "#f87171")]:
            val = g_stats.get(key, 0)
            if val is None: val = 0
            
            # Format according to type
            if "rate" in key:
                val_str = f"{val * 100:.1f}%"
            elif is_index:
                val_str = f"{val:+.1f}" if val != 0 else "0.0"
            else:
                val_str = f"{val:.1f}"

            html += f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
            html += f'<span style="color:{color};font-weight:700;min-width:120px;font-size:0.85rem;">{team}</span>'
            html += f'<span style="color:#fbbf24;font-size:0.95rem;font-weight:bold;">{val_str}</span>'
            html += '</div>'
            
        html += f'<div style="color:#94a3b8;font-size:0.75rem;border-left:2px solid #334155;padding-left:8px;margin-top:2px;"><i>{desc}</i></div>'
        html += '</div>'

    # Data-based comments
    comments = []
    egdi1 = g1.get("egdi_score", 0) or 0
    egdi2 = g2.get("egdi_score", 0) or 0
    throw1 = (g1.get("throw_rate", 0) or 0)
    throw2 = (g2.get("throw_rate", 0) or 0)
    comeback1 = (g1.get("comeback_rate", 0) or 0)
    comeback2 = (g2.get("comeback_rate", 0) or 0)
    for team, egdi, throw, comeback in [(t1, egdi1, throw1, comeback1), (t2, egdi2, throw2, comeback2)]:
        if egdi > 0.5 and throw > 0.3:
            comments.append(f'⚠️ <b>{team} domina o early (EGDI {egdi:+.1f}) mas tem Throw Rate alto ({throw*100:.0f}%).</b> Vantagem no início é frequentemente desperdiçada! Cuidado com apostas de ML pre-game — considere esperar a confirmação do mid-game.')
        elif egdi > 0.5 and throw < 0.15:
            comments.append(f'👑 <b>{team} domina E converte (EGDI {egdi:+.1f}, Throw Rate apenas {throw*100:.0f}%).</b> Time confiável — quando abre vantagem, fecha o jogo. ML é aposta segura.')
        if comeback > 0.35:
            comments.append(f'🔄 <b>{team} tem Comeback Rate excepcional ({comeback*100:.0f}%).</b> Mesmo perdendo o early, vira com frequência. Reforça a estratégia de apostar live quando o time estiver atrás — odds infladas são oportunidade.')
        elif comeback < 0.1 and egdi < 0:
            comments.append(f'📉 <b>{team} raramente vira jogos ({comeback*100:.0f}% comeback) e já começa atrás (EGDI {egdi:+.1f}).</b> Time em desvantagem estrutural — ML arriscado, Handicap positivo pode ser o caminho.')
    html += data_comment(comments)
    html += '</div>'
    return html


def gen_gold_player_table(p1_list, p2_list, t1, t2):
    """Gera tabelas comparativas para Player Props da camada Gold."""
    if not p1_list and not p2_list:
        return ""
        
    html = '<div class="chart-card" style="padding:20px;">'
    html += '<h3 style="color:#fbbf24;margin:0 0 16px 0;font-size:1.1rem;border-bottom:1px solid #78350f;padding-bottom:12px;">👤 Gold Layer Metrics (Player Props / Carry Potential)</h3>'

    def render_team_table(p_list, team_name, color):
        if not p_list:
            return f'<p style="color:#94a3b8;font-size:0.85rem;">Sem dados individuais para {team_name}</p>'
            
        t_html = f'<div style="margin-bottom:20px;">'
        t_html += f'<h4 style="color:{color};margin:0 0 10px 0;">{team_name}</h4>'
        t_html += '''<table style="width:100%;border-collapse:collapse;font-size:0.8rem;text-align:center;">
            <tr style="color:#cbd5e1;border-bottom:1px solid #334155;background:rgba(255,255,255,0.05);">
                <th style="padding:6px;text-align:left;">Player</th>
                <th>Role</th>
                <th title="Kill/Death/Assist Ratio">KDA</th>
                <th title="Dano causado por ouro de farm (eficiência)">Dmg/Gold</th>
                <th title="% das kills do time que o jogador participa">KP%</th>
                <th title="Farm por minuto">CSPM</th>
            </tr>'''

        # Ordenar por role (top, jng, mid, bot, sup) seria ideal, aqui vamos apenas renderizar o que temos
        roles_order = {"top": 1, "jng": 2, "mid": 3, "bot": 4, "sup": 5}
        p_sorted = sorted(p_list, key=lambda x: roles_order.get(str(x.get("position","")).lower(), 99))

        for p in p_sorted:
            name = p.get("playername", "Unknown")
            role = p.get("position", "-")
            kda = p.get("kda_ratio", 0) or 0
            dmg_gold = p.get("damage_per_gold", 0) or 0
            kp = p.get("kill_participation", 0) or 0
            cspm = p.get("avg_cspm", 0) or 0
            
            kda_color = "#4ade80" if kda >= 4 else ("#facc15" if kda >= 2.5 else "#f87171")
            
            t_html += f'<tr style="color:#e2e8f0;border-bottom:1px solid rgba(51,65,85,0.3);">'
            t_html += f'<td style="padding:6px;text-align:left;font-weight:600;">{name}</td>'
            t_html += f'<td style="text-transform:uppercase;color:#94a3b8;font-size:0.7rem;">{role}</td>'
            t_html += f'<td style="color:{kda_color};font-weight:bold;">{kda:.1f}</td>'
            t_html += f'<td>{dmg_gold:.2f}</td>'
            t_html += f'<td>{kp*100:.0f}%</td>'
            t_html += f'<td>{cspm:.1f}</td>'
            t_html += '</tr>'
        t_html += '</table></div>'
        return t_html

    html += '<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(350px,1fr));gap:20px;">'
    html += render_team_table(p1_list, t1, "#60a5fa")
    html += render_team_table(p2_list, t2, "#f87171")
    html += '</div>'
    
    html += explain("Estas tabelas destacam propensões individuais (Player Props). <b>Dmg/Gold (Carry Potential)</b> aponta jogadores que carregam o jogo independentemente dos recursos alocados. <b>KP%</b> alto mostra dependência das lutas em grupo para abates.")
    # Data-based comments
    comments = []
    for p_list, team in [(p1_list, t1), (p2_list, t2)]:
        if not p_list:
            continue
        for p in p_list:
            name = p.get("playername", "Unknown")
            kda = p.get("kda_ratio", 0) or 0
            dmg_gold = p.get("damage_per_gold", 0) or 0
            kp = p.get("kill_participation", 0) or 0
            role = str(p.get("position", "")).lower()
            if kda >= 5:
                comments.append(f'⭐ <b>{name} ({team}) é o carry principal com KDA {kda:.1f}.</b> Player Props focados neste jogador (Over kills, Over assists) podem ter valor significativo.')
            if dmg_gold > 1.0 and role in ["mid", "bot"]:
                comments.append(f'💥 <b>{name} ({team}) tem excelência em Dmg/Gold ({dmg_gold:.2f}).</b> Converte recursos em dano acima da média — alta probabilidade de ser o MVP. Prop bets de dano favorecem este jogador.')
            if kp > 0.75 and role in ["jng", "sup"]:
                comments.append(f'🤝 <b>{name} ({team}) participa de {kp*100:.0f}% das kills.</b> Jogador centrão — Over em assists para junglers/supports com KP% alto é uma aposta inteligente.')
    html += data_comment(comments)
    html += '</div>'
    return html

# [REMOVED: gen_champion_insights]
