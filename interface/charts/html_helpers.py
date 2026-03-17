"""
charts/html_helpers.py — CSS, Layout Plotly, Badges e Funções Auxiliares HTML.
Builder Pattern: cada função constrói um fragmento HTML independente e reutilizável.
"""

import statistics
import html as html_module
import plotly.io as pio

# Enforce dark theme globally for all plotly operations in this process
pio.templates.default = "plotly_dark"

# ============================================================================
# CSS — Tema Dark Premium
# ============================================================================

INSIGHTS_CSS = """
<style>
@keyframes fadeInUp {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
.insights-container {
    font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    max-width: 1200px;
    margin: 0 auto;
    padding: 0;
    color: #e2e8f0;
}
.chart-section { margin-bottom: 32px; animation: fadeInUp 0.6s ease-out both; }
.chart-card {
    background: #1e293b;
    border-radius: 16px;
    padding: 24px;
    border: 1px solid #334155;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
}
.chart-card:hover {
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2), 0 10px 10px -5px rgba(0, 0, 0, 0.1);
    transform: translateY(-4px);
}
.explain-box {
    background: rgba(15, 23, 42, 0.5);
    border-left: 4px solid #3b82f6;
    border-radius: 4px 12px 12px 4px;
    padding: 16px 20px;
    margin-top: 16px;
    font-size: 0.875rem;
    color: #cbd5e1;
    line-height: 1.6;
}
.explain-box b { color: #60a5fa; font-weight: 600; }
.stats-badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 600;
    margin: 4px;
    position: relative;
    cursor: default;
    border: 1px solid rgba(255, 255, 255, 0.1);
}
.stats-badge:hover::after {
    content: attr(data-tip);
    position: absolute;
    bottom: 125%;
    left: 50%;
    transform: translateX(-50%);
    background: #0f172a;
    color: #f8fafc;
    padding: 10px 14px;
    border-radius: 10px;
    font-size: 0.8rem;
    font-weight: 400;
    white-space: normal;
    width: max-content;
    max-width: 280px;
    text-align: left;
    line-height: 1.5;
    z-index: 100;
    border: 1px solid #334155;
    box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.3);
    animation: fadeInUp 0.2s ease-out;
    pointer-events: none;
}
.stats-container {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 12px;
}
.odd-badge {
    background: rgba(234, 179, 8, 0.1);
    color: #fbbf24;
    border: 1px solid rgba(234, 179, 8, 0.2);
    padding: 6px 12px;
    border-radius: 10px;
    font-size: 0.875rem;
    font-weight: 700;
    display: inline-block;
    margin-top: 12px;
}
@keyframes led-rotate {
    0% { transform: translate(-50%, -50%) rotate(0deg); }
    100% { transform: translate(-50%, -50%) rotate(360deg); }
}
@keyframes pulse-emerald {
    0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
    100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
}
.data-comment-box {
    position: relative;
    padding: 3px;
    background: #0f172a;
    border-radius: 16px;
    margin-top: 24px;
    overflow: hidden;
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
}
.data-comment-box::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    width: 250%;
    height: 250%;
    background: conic-gradient(
        from 0deg,
        transparent 0deg,
        #10b981 30deg,
        transparent 60deg,
        transparent 180deg,
        #fbbf24 210deg,
        transparent 240deg
    );
    animation: led-rotate 4s linear infinite;
    z-index: 0;
}
.data-comment-box-inner {
    position: relative;
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border-radius: 14px;
    padding: 20px;
    z-index: 1;
    color: #e2e8f0;
}
.pulse-dot {
    width: 8px;
    height: 8px;
    background: #10b981;
    border-radius: 50%;
    display: inline-block;
    animation: pulse-emerald 2s infinite;
    margin-right: 8px;
}
.data-comment-box-inner b { color: #4ade80; }
.comment-title {
    display: flex;
    align-items: center;
    font-weight: 800;
    font-size: 0.95rem;
    color: #4ade80;
    margin-bottom: 12px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
}
.insight-item {
    margin-bottom: 8px;
    padding-left: 12px;
    border-left: 2px solid rgba(16, 185, 129, 0.3);
    font-size: 0.9rem;
    line-height: 1.5;
}
/* Estilos para o Bet Line / EV Finder */
.bet-grid-item { margin-bottom: 8px; width: 100%; }
.bet-entry {
    background: rgba(15, 23, 42, 0.6);
    border-radius: 12px;
    padding: 10px 14px;
    border: 1px solid rgba(255, 255, 255, 0.05);
    transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 6px;
}
.bet-entry:hover {
    background: rgba(30, 41, 59, 1);
    border-color: rgba(59, 130, 246, 0.4);
    transform: translateX(4px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.3);
}
.bet-low { border-left: 4px solid #10b981; }
.bet-med { border-left: 4px solid #fbbf24; }
.bet-high { border-left: 4px solid #ef4444; }

.bet-entry summary {
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 600;
    color: #f1f5f9;
    list-style: none;
    display: flex;
    justify-content: space-between;
    align-items: center;
}
.bet-entry summary::-webkit-details-marker { display: none; }
.bet-entry summary b { color: #fbbf24; font-size: 0.95rem; }

.bet-detail {
    margin-top: 12px;
    padding: 12px;
    background: rgba(15, 23, 42, 0.8);
    border-radius: 8px;
    font-size: 0.8rem;
    color: #94a3b8;
    line-height: 1.5;
    border: 1px solid rgba(255, 255, 255, 0.03);
}
.bet-detail b { color: #60a5fa; }
</style>
"""


# ============================================================================
# Plotly Layout & Conversion
# ============================================================================

def base_layout(title="", height=400):
    """Retorna dict de layout padrão Plotly com tema dark moderno e legível."""
    return dict(
        template="plotly_dark",
        title=dict(
            text=title, 
            font=dict(size=18, color="#f8fafc", weight="bold"),
            x=0.05,
            y=0.95
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#cbd5e1", family="Inter, Segoe UI, sans-serif"),
        height=height,
        margin=dict(l=60, r=40, t=80, b=40),
        xaxis=dict(
            gridcolor="rgba(148, 163, 184, 0.1)", 
            zerolinecolor="rgba(148, 163, 184, 0.2)",
            tickfont=dict(size=11, color="#94a3b8"),
            title=dict(font=dict(size=12, color="#94a3b8"))
        ),
        yaxis=dict(
            gridcolor="rgba(148, 163, 184, 0.1)", 
            zerolinecolor="rgba(148, 163, 184, 0.2)",
            tickfont=dict(size=11, color="#94a3b8"),
            title=dict(font=dict(size=12, color="#94a3b8"))
        ),
        legend=dict(
            bgcolor="rgba(15, 23, 42, 0.8)",
            bordercolor="rgba(51, 65, 85, 0.5)",
            borderwidth=1,
            font=dict(size=12, color="#e2e8f0"),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        colorway=["#3b82f6", "#ef4444", "#10b981", "#f59e0b", "#8b5cf6", "#ec4899"],
        hoverlabel=dict(
            bgcolor="#1e293b",
            font_size=13,
            font_family="Inter, system-ui",
            bordercolor="#334155"
        ),
        hovermode="x unified"
    )


def fig_to_html(fig):
    """Converte uma Plotly Figure em iframe HTML com transparência forçada em todas as camadas."""
    # Ensure layout is transparent even if not created via base_layout
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        template="plotly_dark"
    )
    
    raw = fig.to_html(
        full_html=False, include_plotlyjs="cdn",
        config={"displayModeBar": True, "scrollZoom": True, "responsive": True,
                "modeBarButtonsToRemove": ["sendDataToCloud", "editInChartStudio", "lasso2d"]},
    )
    
    # Ultimate CSS reset for Plotly backgrounds inside the iframe
    style_fix = """
    <style>
        :root, html, body { background-color: transparent !important; background: transparent !important; margin: 0; padding: 0; overflow: hidden; }
        .plotly-graph-div { background-color: transparent !important; background: transparent !important; }
        .main-svg { background-color: transparent !important; background: transparent !important; }
        .bg, .bglayer, .plotbg { fill: transparent !important; }
        .js-plotly-plot .plotly .bg { fill: transparent !important; }
        canvas { background-color: transparent !important; }
    </style>
    """
    
    # Inject style and wrap in a clean structure
    content = f"<html><head>{style_fix}</head><body style='background:transparent;'>{raw}</body></html>"
    # Fallback replace for the main div class just in case
    content = content.replace('class="plotly-graph-div"', 'class="plotly-graph-div" style="background:transparent !important;"')
    
    escaped = html_module.escape(content)
    height = fig.layout.height or 400
    return f'<iframe srcdoc="{escaped}" style="width:100%;height:{height + 10}px;border:none;background:transparent;" allowtransparency="true" scrolling="no"></iframe>'


# ============================================================================
# Data Conversion Helpers
# ============================================================================

def int_list(data):
    """Filtra None e converte para lista de inteiros."""
    return [int(round(v)) for v in data if v is not None]


def float_list(data):
    """Filtra None e converte para lista de floats."""
    return [float(v) for v in data if v is not None]


# ============================================================================
# Statistics
# ============================================================================

def calc_stats(data):
    """Calcula estatísticas descritivas completas: μ, Med, σ, Min, Max, Moda, P25, P75."""
    if not data:
        return {}
    clean = [v for v in data if v is not None]
    if not clean:
        return {}
    n = len(clean)
    avg = sum(clean) / n
    med = statistics.median(clean)
    try:
        mode_val = statistics.mode([round(v, 1) for v in clean])
    except statistics.StatisticsError:
        mode_val = avg
    std = statistics.stdev(clean) if n > 1 else 0
    sorted_d = sorted(clean)
    p25 = sorted_d[max(0, int(n * 0.25))]
    p75 = sorted_d[min(n - 1, int(n * 0.75))]
    return {"avg": avg, "med": med, "std": std, "min": min(clean), "max": max(clean),
            "mode": mode_val, "p25": p25, "p75": p75, "n": n}


# ============================================================================
# HTML Badge Builders
# ============================================================================

def stats_html(st, unit=""):
    """Gera badges HTML com tooltips para cada estatística."""
    if not st:
        return ""
    u = unit
    return (
        f'<div class="stats-container">'
        f'<span class="stats-badge tooltip-left" style="background:rgba(59,130,246,0.15);color:#60a5fa;" data-tip="Média (μ): Valor central de todos os dados. Em LoL, indica a tendência de longo prazo do time.">μ={st["avg"]:.1f}{u}</span>'
        f'<span class="stats-badge tooltip-left" style="background:rgba(168,85,247,0.15);color:#c084fc;" data-tip="Mediana: O valor do meio quando os dados são ordenados. Menos afetada por jogos extremos (stomps ou derrotas pesadas).">Med={st["med"]:.1f}{u}</span>'
        f'<span class="stats-badge" style="background:rgba(34,197,94,0.15);color:#4ade80;" data-tip="Desvio Padrão (σ): Mede a consistência. σ baixo = time previsível, σ alto = resultados voláteis (bom para apostas de risco).">σ={st["std"]:.1f}</span>'
        f'<span class="stats-badge" style="background:rgba(234,179,8,0.12);color:#fbbf24;" data-tip="Min/Max: Os extremos históricos. Mostra o pior e o melhor desempenho do time nesta métrica.">Min={st["min"]:.0f} Max={st["max"]:.0f}</span>'
        f'<span class="stats-badge tooltip-right" style="background:rgba(99,102,241,0.15);color:#818cf8;" data-tip="Moda: O valor que mais se repete. Em LoL, indica o resultado \'típico\' da equipe.">Moda={st["mode"]:.1f}</span>'
        f'<span class="stats-badge tooltip-right" style="background:rgba(236,72,153,0.12);color:#f472b6;" data-tip="Percentis 25/75: 50% dos resultados caem entre P25 e P75. É a faixa \'normal\' de desempenho.">P25={st["p25"]:.1f} P75={st["p75"]:.1f}</span>'
        f'</div>'
    )


def odd_badge(prob):
    """Gera badge amarelo com a odd ideal baseada na probabilidade."""
    if not prob or prob <= 0:
        return ""
    odd = 100 / prob
    return f'<span class="odd-badge">💰 Odd ideal: {odd:.2f} (prob. {prob:.0f}%)</span>'


def explain(text):
    """Gera caixa explicativa '📖 Como ler:' com bordas indigo."""
    return f'<div class="explain-box">📖 <b>Como ler:</b> {text}</div>'


def data_comment(insights):
    """Gera caixa animada '💡 Comentário Baseado em Dados' com insights dinâmicos.
    
    Args:
        insights: string ou lista de strings com insights acionáveis.
    """
    if not insights:
        return ""
    if isinstance(insights, str):
        insights = [insights]
    items = "".join(f'<div class="insight-item">{i}</div>' for i in insights if i)
    if not items:
        return ""
    return (
        '<div class="data-comment-box">'
        '<div class="data-comment-box-inner">'
        '<div class="comment-title"><span class="pulse-dot"></span>💡 Comentário Baseado em Dados</div>'
        f'{items}'
        '</div>'
        '</div>'
    )


def risk_tier(prob):
    """Classifica probabilidade em tier de risco: low (≥65%), med (50-64%), high (<50%)."""
    if prob >= 65:
        return ("low", "🟢 Baixo Risco")
    if prob >= 50:
        return ("med", "🟡 Risco Médio")
    return ("high", "🔴 Alto Risco")


def bet_line(team, market, line, prob, data_points, explanation):
    """Gera um card de aposta com details/summary nativo (funciona sem JS)."""
    if prob is None or prob <= 0:
        return ""
    odd = 100 / prob
    tier, label = risk_tier(prob)
    return (
        f'<div class="bet-entry bet-grid-item bet-{tier}">'
        f'<details>'
        f'<summary>{team} — {market} {line} @ <b>{odd:.2f}x</b> ({prob:.0f}%) [{label}]</summary>'
        f'<div class="bet-detail">'
        f'<b>📊 Detalhamento do Cálculo:</b><br>'
        f'<b>Mercado:</b> {market} {line}<br>'
        f'<b>Time:</b> {team}<br>'
        f'<b>Probabilidade Empírica:</b> {prob:.1f}% (baseada em {data_points} jogos reais)<br>'
        f'<b>Odd Justa (matemática):</b> 1 / ({prob:.1f}% / 100) = <b>{odd:.2f}</b><br>'
        f'<b>Classificação de Risco:</b> {label}<br><br>'
        f'<b>💡 Por que esse risco?</b><br>{explanation}<br><br>'
        f'<b>📐 Fórmula:</b> Odd = 100 / Prob%. Se a casa oferece odd &gt; {odd:.2f}, há <b>Expected Value positivo (+EV)</b>.'
        f'</div></details></div>'
    )
