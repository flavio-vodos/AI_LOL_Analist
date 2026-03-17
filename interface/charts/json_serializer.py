"""
charts/json_serializer.py — Pure data module replacing renderer.py.
Returns structured dicts matching AnalyticsResponse instead of generating HTML.
All computation logic is preserved from html_helpers.py, chart_generators.py, and ev_finder.py.
"""

from .html_helpers import calc_stats, float_list, int_list, risk_tier


# ============================================================================
# Core Helpers
# ============================================================================

def make_bet_entry(team, market, line, prob, data_points, explanation, has_draft=False, draft_mult=None):
    """Returns BetEntryData-shaped dict. odd = 100 / prob."""
    if not prob or prob <= 0:
        return None
    odd = 100 / prob
    tier, label = risk_tier(prob)
    return {
        "team": team,
        "market": market,
        "line": line,
        "probability": prob,
        "data_points": data_points,
        "odd": odd,
        "risk_tier": tier,
        "risk_label": label,
        "explanation": explanation,
        "has_draft_projection": has_draft,
        "draft_multiplier": draft_mult,
    }


def _rate_prob(data, cond):
    """Calculates (probability%, count) of a condition over data."""
    v = [x for x in data if x is not None]
    return (sum(1 for x in v if cond(x)) / len(v) * 100, len(v)) if v else (None, 0)


# ============================================================================
# Section Builders
# ============================================================================

def build_meta_section(s1, s2, t1, t2, patches):
    """Returns MetaSection dict."""
    patch_label = ", ".join(patches) if patches and "Todos" not in patches else "Todos os patches"
    return {
        "team1": t1,
        "team2": t2,
        "patch_label": patch_label,
        "games_t1": s1["total_games"],
        "games_t2": s2["total_games"],
    }


def build_educational_section():
    """Returns static educational content as structured dict."""
    return {
        "odds_modeling": {
            "title": "Modelagem de Probabilidades (Odds)",
            "content": (
                'Segundo o artigo "What Are the Odds?", prever estatísticas não é sobre "certezas", mas sobre identificar valor. '
                'A <b>Odd Ideal</b> é calculada matematicamente como <code>1 / (Probabilidade% / 100)</code> baseada no histórico.<br><br>'
                'Se a odd for <b>1.50</b> (66% chance) e a casa oferecer <b>1.80</b>, há uma discrepância estatística (+EV).'
            ),
        },
        "draft_projection": {
            "title": "✨ Projeção do Draft",
            "content": (
                'É um multiplicador dinâmico calculado ao isolar o desempenho histórico do Campeão escolhido (Platinum Layer) '
                'frente à média global de todos os campeões naquela função. Por exemplo, se um time pega <i>Draven</i>, o algoritmo '
                'percebe que o <b style="color:#c4b5fd;">Multiplicador de First Blood</b> dele é <i>1.40x</i>. As projeções empurram '
                'as odds/quantidades originais para refletir a nova agressividade da composição.'
            ),
        },
        "egr_mlr": {
            "title": "EGR (Early-Game Rating) & MLR (Mid/Late Rating)",
            "content": (
                '<i>EGR</i> estima a probabilidade de um time vencer aos 15 minutos, baseado no controle de primeiros objetivos '
                '(<b style="color:#ef4444;">FB%</b>, <b style="color:#fbbf24;">FD%</b>, <b style="color:#a855f7;">HLD%</b>) e vantagem de ouro.<br><br>'
                '<i>MLR</i> mede se um time destrói estruturas (Torres, <b style="color:#eab308;">FBN%</b>, Inibidores) ou perde jogos '
                'que estava ganhando. Um time com bons Barões mas longa duração sofre para fechar o mapa.'
            ),
        },
        "glossary": {
            "title": "Glossário de Terminologias",
            "items": [
                {"term": "CKPM", "definition": 'Combined Kills Per Minute (Dita a "sangria" ou velocidade do jogo).'},
                {"term": "FB% / FD%", "definition": "First Blood / First Dragon Rate (Controle inicial)."},
                {"term": "FBN%", "definition": "First Baron Rate (Controle de mapa mid-late)."},
                {"term": "EGPM", "definition": "Earned Gold Per Minute (Mede eficiência na fazenda/abates)."},
                {"term": "DPM", "definition": "Damage Per Minute (O dano real trocado com campeões)."},
            ],
        },
    }


def build_egr_section(s1, s2, t1, t2):
    """Returns EGRSection dict."""
    fb1, fb2 = s1["fb_rate"], s2["fb_rate"]
    fd1, fd2 = s1["fd_rate"], s2["fd_rate"]
    fh1, fh2 = s1["fherald_rate"], s2["fherald_rate"]
    egr1 = (fb1 + fd1 + fh1) / 3
    egr2 = (fb2 + fd2 + fh2) / 3

    comments = []
    for team, e_val in [(t1, egr1), (t2, egr2)]:
        if e_val > 60:
            comments.append(f'⚡ <b>{team} tem domínio early game ({e_val:.0f}% EGR).</b> Favorito a FB/FD.')
        elif e_val < 40:
            comments.append(f'⚠️ <b>{team} tem EGR baixo ({e_val:.0f}%).</b> Costuma começar atrás.')

    return {
        "t1_values": {"fb": fb1, "fd": fd1, "fh": fh1},
        "t2_values": {"fb": fb2, "fd": fd2, "fh": fh2},
        "egr_score_t1": egr1,
        "egr_score_t2": egr2,
        "explain_text": "O modelo de <b>EGR</b> demonstra que o time que conquista esses prêmios iniciais cria snowball de ouro.",
        "comments": comments,
    }


def build_mlr_section(s1, s2, t1, t2):
    """Returns MLRSection dict."""
    mlr1 = min((s1.get("avg_barons", 0) + s1.get("avg_inhibitors", 0) + s1.get("avg_towers", 0) / 5) / 3 * 20, 100)
    mlr2 = min((s2.get("avg_barons", 0) + s2.get("avg_inhibitors", 0) + s2.get("avg_towers", 0) / 5) / 3 * 20, 100)
    egr1 = (s1.get("fb_rate", 0) + s1.get("fd_rate", 0) + s1.get("fherald_rate", 0)) / 3
    egr2 = (s2.get("fb_rate", 0) + s2.get("fd_rate", 0) + s2.get("fherald_rate", 0)) / 3

    comments = []
    for team, opp, mlr, egr in [(t1, t2, mlr1, egr1), (t2, t1, mlr2, egr2)]:
        if mlr > 60 and egr < 40:
            comments.append(f'🔄 <b>{team} é um time de virada!</b> EGR fraco ({egr:.0f}%) mas MLR forte ({mlr:.0f}).')
        elif mlr > 60 and egr > 60:
            comments.append(f'👑 <b>{team} é completo:</b> forte no early e no late.')

    return {
        "t1": {
            "fbaron_rate": s1["fbaron_rate"],
            "avg_barons": s1["avg_barons"],
            "avg_inhibitors": s1["avg_inhibitors"],
            "avg_towers": s1["avg_towers"],
        },
        "t2": {
            "fbaron_rate": s2["fbaron_rate"],
            "avg_barons": s2["avg_barons"],
            "avg_inhibitors": s2["avg_inhibitors"],
            "avg_towers": s2["avg_towers"],
        },
        "explain_text": "O modelo <b>MLR</b> mostra como o time fecha o jogo no Mid-Late Game.",
        "comments": comments,
    }


def build_radar_section(s1, s2, t1, t2, g1=None, g2=None):
    """Returns RadarSection dict. g1/g2 are optional Gold layer dicts."""
    def calc_radar(stats):
        wr = stats.get("win_rate", 0)
        egr = (stats.get("fb_rate", 0) + stats.get("fd_rate", 0) + stats.get("fherald_rate", 0)) / 3
        mlr = min((stats.get("avg_barons", 0) + stats.get("avg_inhibitors", 0) + stats.get("avg_towers", 0) / 5) / 3 * 20, 100)
        kpm = min(stats.get("avg_kpm", 0) / 1.0 * 100, 100)
        return [wr, egr, mlr, kpm]

    t1_vals = calc_radar(s1)
    t2_vals = calc_radar(s2)
    wr_1, egr_1, mlr_1, kpm_1 = t1_vals
    wr_2, egr_2, mlr_2, kpm_2 = t2_vals

    comments = []

    # --- Archetype detection (lowered thresholds to fire more often) ---
    for team, wr_v, egr_v, mlr_v, kpm_v in [
        (t1, wr_1, egr_1, mlr_1, kpm_1),
        (t2, wr_2, egr_2, mlr_2, kpm_2),
    ]:
        if egr_v > 55 and kpm_v > 50:
            comments.append(
                f'⚔️ <b>{team} tem perfil AGRESSIVO</b> (EGR {egr_v:.0f}%, KPM {kpm_v:.0f}%). '
                f'Busca jogos caóticos e rápidos. Favoreça <b>Over em kills</b> e <b>Under em duração</b>.'
            )
        elif mlr_v > 50:
            comments.append(
                f'🧠 <b>{team} tem perfil CONTROLADO</b> (MLR {mlr_v:.0f}%). '
                f'Joga por objetivos e controle de mapa. Favoreça <b>Over em duração</b> e <b>Over em Barões</b>.'
            )
        else:
            # Generic comment always fires as fallback
            dominant_dim = max(
                [("EGR", egr_v), ("MLR", mlr_v), ("KPM", kpm_v)],
                key=lambda x: x[1]
            )
            comments.append(
                f'📊 <b>{team} tem perfil EQUILIBRADO</b> com destaque em <b>{dominant_dim[0]} ({dominant_dim[1]:.0f}%)</b>. '
                f'Win Rate histórico: {wr_v:.0f}%.'
            )

    # --- Style clash detection ---
    if egr_1 > 50 and kpm_1 > 45 and mlr_2 > 50:
        comments.append(
            f'💥 <b>Duelo de estilos!</b> {t1} (agressivo/early) vs {t2} (controlado/late). '
            f'Se {t1} não dominar o early, {t2} tende a virar. Janela de aposta live nos 15min.'
        )
    elif egr_2 > 50 and kpm_2 > 45 and mlr_1 > 50:
        comments.append(
            f'💥 <b>Duelo de estilos!</b> {t2} (agressivo/early) vs {t1} (controlado/late). '
            f'Se {t2} não dominar o early, {t1} tende a virar. Janela de aposta live nos 15min.'
        )

    # --- Win rate gap ---
    wr_diff = abs(wr_1 - wr_2)
    if wr_diff > 15:
        fav, dog = (t1, t2) if wr_1 > wr_2 else (t2, t1)
        fav_wr = max(wr_1, wr_2)
        comments.append(
            f'🏆 <b>{fav} lidera em Win Rate ({fav_wr:.0f}%)</b> com vantagem de {wr_diff:.0f}% sobre {dog}. '
            f'O DNA tático confirma o domínio histórico.'
        )

    # --- Gold layer enrichment (throw/comeback/egdi) ---
    for team, g in [(t1, g1), (t2, g2)]:
        if not g:
            continue
        throw = g.get("throw_rate") or 0
        comeback = g.get("comeback_rate") or 0
        egdi = g.get("egdi_score") or 0
        if throw > 25:
            comments.append(
                f'⚠️ <b>{team} tem Throw Rate de {throw:.0f}%</b> (Gold Layer). '
                f'Desperdiça vantagens com frequência — cuidado com apostas de ML em jogos onde este time lidera no early.'
            )
        if comeback > 25:
            comments.append(
                f'🔄 <b>{team} é especialista em viradas ({comeback:.0f}%)</b> (Gold Layer). '
                f'Excelente para <b>live betting</b> quando este time está atrás no placar.'
            )
        if egdi > 0.6:
            comments.append(
                f'💎 <b>{team} tem EGDI Score alto ({egdi:.2f})</b> — converte vantagens de ouro em vitórias com eficiência acima da média.'
            )

    return {
        "labels": ["Win Rate", "EGR Score (Early)", "MLR Score (Late)", "Ação (KPM)"],
        "t1_values": t1_vals,
        "t2_values": t2_vals,
        "explain_text": (
            "O <b>Gráfico de Radar</b> é o padrão-ouro para ler o DNA dos times. Um time esticado em <i>EGR e Ação</i> "
            "busca jogos caóticos e curtos. Um dominando <i>MLR</i> joga pelas lutas de objetivos amplas."
        ),
        "comments": comments,
    }


def build_timeline_section(s1, s2, t1, t2, mult1, mult2):
    """Returns TimelineSection dict with exactly 4 points per dimension."""
    x_vals = [10, 15, 20, 25]
    gold_t1 = [s1.get(f"golddiffat{m}", 0) for m in x_vals]
    cs_t1 = [s1.get(f"csdiffat{m}", 0) for m in x_vals]
    xp_t1 = [s1.get(f"xpdiffat{m}", 0) for m in x_vals]
    gold_t2 = [s2.get(f"golddiffat{m}", 0) for m in x_vals]
    cs_t2 = [s2.get(f"csdiffat{m}", 0) for m in x_vals]
    xp_t2 = [s2.get(f"xpdiffat{m}", 0) for m in x_vals]

    draft_active = mult1 is not None and mult2 is not None
    draft_gold_t1 = draft_cs_t1 = draft_xp_t1 = None
    draft_gold_t2 = draft_cs_t2 = draft_xp_t2 = None
    m1_adv = m2_adv = None

    if draft_active:
        m1_adv = (mult1.get("firstblood", 1.0) + mult1.get("firstdragon", 1.0) + mult1.get("kills", 1.0)) / 3
        m2_adv = (mult2.get("firstblood", 1.0) + mult2.get("firstdragon", 1.0) + mult2.get("kills", 1.0)) / 3

        def proj_vals(base_vals, ratio):
            result = []
            for val in base_vals:
                if val > 0:
                    result.append(val * ratio)
                else:
                    result.append(val / ratio if ratio > 0 else val)
            return result

        ratio_t1 = m1_adv / m2_adv if m2_adv > 0 else 1.0
        ratio_t2 = m2_adv / m1_adv if m1_adv > 0 else 1.0
        draft_gold_t1 = proj_vals(gold_t1, ratio_t1)
        draft_cs_t1 = proj_vals(cs_t1, ratio_t1)
        draft_xp_t1 = proj_vals(xp_t1, ratio_t1)
        draft_gold_t2 = proj_vals(gold_t2, ratio_t2)
        draft_cs_t2 = proj_vals(cs_t2, ratio_t2)
        draft_xp_t2 = proj_vals(xp_t2, ratio_t2)

    comments = []
    gd15_1 = s1.get("golddiffat15", 0) or 0
    gd15_2 = s2.get("golddiffat15", 0) or 0
    gd10_1 = s1.get("golddiffat10", 0) or 0
    gd10_2 = s2.get("golddiffat10", 0) or 0
    xp15_1 = s1.get("xpdiffat15", 0) or 0
    xp15_2 = s2.get("xpdiffat15", 0) or 0
    cs15_1 = s1.get("csdiffat15", 0) or 0
    cs15_2 = s2.get("csdiffat15", 0) or 0

    for team, opp, gd10, gd15, xp15, cs15 in [
        (t1, t2, gd10_1, gd15_1, xp15_1, cs15_1),
        (t2, t1, gd10_2, gd15_2, xp15_2, cs15_2),
    ]:
        if gd15 > 1000:
            comments.append(f'💰 <b>{team} domina com +{gd15:.0f}g aos 15min.</b> Vantagem significativa que historicamente se converte em vitória.')
        elif gd15 > 400:
            comments.append(f'📈 <b>{team} costuma ter vantagem de ouro aos 15min (+{gd15:.0f}g).</b> Early game consistentemente positivo.')
        elif gd15 < -1000:
            comments.append(f'📉 <b>{team} costuma estar {abs(gd15):.0f}g atrás aos 15min.</b> Se o MLR for alto, este é o time para apostar live após os 10-15min.')
        elif gd15 < -400:
            comments.append(f'⚠️ <b>{team} tende a estar atrás em ouro aos 15min ({gd15:+.0f}g).</b> Depende de virada no mid/late.')

        if gd10 > 0 and gd15 < gd10 * 0.5:
            comments.append(f'🔄 <b>{team} perde vantagem entre 10 e 15min.</b> Começa bem (+{gd10:.0f}g@10) mas não sustenta ({gd15:+.0f}g@15).')
        elif gd10 < 0 and gd15 > gd10 * 0.5:
            comments.append(f'📈 <b>{team} recupera terreno entre 10 e 15min.</b> Começa atrás ({gd10:+.0f}g@10) mas reage ({gd15:+.0f}g@15).')

        if xp15 > 500:
            comments.append(f'⚡ <b>{team} tem vantagem de XP aos 15min (+{xp15:.0f} XP).</b> Nível superior favorece lutas e objetivos.')
        if cs15 > 10:
            comments.append(f'🌾 <b>{team} domina em CS aos 15min (+{cs15:.0f} CS).</b> Eficiência de farm superior.')

    if abs(gd15_1) < 300 and abs(gd15_2) < 300:
        comments.append(f'⚖️ <b>Ambos os times chegam aos 15min equilibrados em ouro.</b> Early game competitivo — o jogo será decidido no mid/late.')

    return {
        "minutes": x_vals,
        "gold_diff_t1": gold_t1,
        "cs_diff_t1": cs_t1,
        "xp_diff_t1": xp_t1,
        "gold_diff_t2": gold_t2,
        "cs_diff_t2": cs_t2,
        "xp_diff_t2": xp_t2,
        "draft_projection_active": draft_active,
        "draft_gold_diff_t1": draft_gold_t1,
        "draft_cs_diff_t1": draft_cs_t1,
        "draft_xp_diff_t1": draft_xp_t1,
        "draft_gold_diff_t2": draft_gold_t2,
        "draft_cs_diff_t2": draft_cs_t2,
        "draft_xp_diff_t2": draft_xp_t2,
        "mult_t1": m1_adv,
        "mult_t2": m2_adv,
        "explain_text": (
            "A curva de <b>Diferença (Diff)</b> mostra o ritmo da partida. Se a linha pontilhada de projeção (✨) for mais alta "
            "que a histórica, o draft acelera a vantagem. Dominar o <b>Early Game</b> (10-15m) no Ouro, CS e XP força o adversário ao desespero."
        ),
        "comments": comments,
    }


def build_vision_section(s1, s2, t1, t2):
    """Returns VisionSection dict."""
    wp1, wp2 = s1.get("wardsplaced", 0), s2.get("wardsplaced", 0)
    wk1, wk2 = s1.get("wardskilled", 0), s2.get("wardskilled", 0)
    cw1, cw2 = s1.get("controlwardsbought", 0), s2.get("controlwardsbought", 0)
    vs1, vs2 = s1.get("visionscore", 0), s2.get("visionscore", 0)

    comments = []
    for team, wp, wk, cw, vs, opp_wk in [(t1, wp1, wk1, cw1, vs1, wk2), (t2, wp2, wk2, cw2, vs2, wk1)]:
        if wk > opp_wk * 1.2:
            pct_more = ((wk / max(opp_wk, 0.1)) - 1) * 100
            comments.append(f'👁️ <b>{team} destrói {pct_more:.0f}% mais wards.</b> Controle de visão superior favorece apostas em <b>First Baron</b> e <b>First Dragon</b>.')
        if cw > 4:
            comments.append(f'🟣 <b>{team} compra muitas Control Wards ({cw:.1f}/jogo).</b> Investimento pesado em visão indica foco em controle de objetivos.')
    if vs1 > 0 and vs2 > 0 and abs(vs1 - vs2) > 0.5:
        vision_dom = t1 if vs1 > vs2 else t2
        comments.append(f'🎯 <b>{vision_dom} tem Vision Score superior</b> ({max(vs1,vs2):.1f} vs {min(vs1,vs2):.1f}). Controle de mapa é a base para objetivos neutros.')

    return {
        "wards_placed": {"t1": wp1, "t2": wp2},
        "wards_killed": {"t1": wk1, "t2": wk2},
        "control_wards": {"t1": cw1, "t2": cw2},
        "vision_score": {"t1": vs1, "t2": vs2},
        "explain_text": (
            "A base do controle de macro no LoL é a <b>Visão</b>. Mais Wards Destruídas e Control Wards indicam "
            "foco em varrer a selva e preparar armadilhas em Barão/Dragão."
        ),
        "comments": comments,
    }


def build_economy_section(s1, s2, t1, t2, g1, g2):
    """Returns EconomySection dict."""
    egpm1_data = float_list(s1.get("earnedgold_pm_history", []))
    egpm2_data = float_list(s2.get("earnedgold_pm_history", []))
    dpm1_data = float_list(s1.get("dmg_pm_history", []))
    dpm2_data = float_list(s2.get("dmg_pm_history", []))

    avg_egpm1 = sum(egpm1_data) / len(egpm1_data) if egpm1_data else 0
    avg_egpm2 = sum(egpm2_data) / len(egpm2_data) if egpm2_data else 0
    avg_dpm1 = sum(dpm1_data) / len(dpm1_data) if dpm1_data else 0
    avg_dpm2 = sum(dpm2_data) / len(dpm2_data) if dpm2_data else 0

    gold_layer = None
    if g1 and g2:
        gold_layer = {
            "t1": {
                "egdi": g1.get("egdi_score", 0),
                "throw_rate": g1.get("throw_rate", 0),
                "comeback_rate": g1.get("comeback_rate", 0),
            },
            "t2": {
                "egdi": g2.get("egdi_score", 0),
                "throw_rate": g2.get("throw_rate", 0),
                "comeback_rate": g2.get("comeback_rate", 0),
            },
        }

    comments = []
    for team, opp, e, d, eo, do_val in [
        (t1, t2, avg_egpm1, avg_dpm1, avg_egpm2, avg_dpm2),
        (t2, t1, avg_egpm2, avg_dpm2, avg_egpm1, avg_dpm1),
    ]:
        if e > eo * 1.1 and d < do_val * 0.9:
            comments.append(f'💰 <b>{team} farms muito mas causa pouco dano.</b> Indica jogo passivo.')
        elif e < eo * 0.9 and d > do_val * 1.1:
            comments.append(f'⚔️ <b>{team} é eficiente com poucos recursos.</b> Indica time letal.')
    if g1 and g2:
        for g_stats, team in [(g1, t1), (g2, t2)]:
            # Assuming throw_rate and comeback_rate are now 0-100 percentages
            th = g_stats.get("throw_rate", 0) or 0
            cb = g_stats.get("comeback_rate", 0) or 0
            if th > 30:
                comments.append(f'⚠️ <b>{team} tem Throw Rate alto ({th:.0f}%).</b> Desperdiça vantagens.')
            if cb > 30:
                comments.append(f'🔄 <b>{team} é expert em viradas ({cb:.0f}%).</b> Bom para live betting.')

    return {
        "egpm": {"t1": avg_egpm1, "t2": avg_egpm2},
        "dpm": {"t1": avg_dpm1, "t2": avg_dpm2},
        "gold_layer": gold_layer,
        "explain_text": (
            "Segundo o artigo <i>LoL's Advanced Stats Problem</i>, a verdadeira pressão do jogo provém de "
            "<b>Ouro Ganho (EGPM)</b> e <b>Dano Gerado (DPM)</b>."
        ),
        "comments": comments,
    }


def build_pace_section(s1, s2, t1, t2):
    """Returns PaceSection dict."""
    ckpm1 = float_list(s1.get("ckpm_history", []))
    ckpm2 = float_list(s2.get("ckpm_history", []))
    kpm1 = float_list(s1.get("kpm_history", []))
    kpm2 = float_list(s2.get("kpm_history", []))

    avg_ckpm1 = sum(ckpm1) / len(ckpm1) if ckpm1 else 0
    avg_ckpm2 = sum(ckpm2) / len(ckpm2) if ckpm2 else 0
    avg_kpm1 = sum(kpm1) / len(kpm1) if kpm1 else 0
    avg_kpm2 = sum(kpm2) / len(kpm2) if kpm2 else 0

    comments = []
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

    return {
        "ckpm": {"t1": avg_ckpm1, "t2": avg_ckpm2},
        "kpm": {"t1": avg_kpm1, "t2": avg_kpm2},
        "explain_text": (
            "<b>CKPM</b> indica o ritmo global da partida. CKPM > 0.8 indicam jogos 'sangrentos', cheios de lutas "
            "(favorável para Overs de Kills). <b>KPM</b> mede a letalidade bruta de apenas um time."
        ),
        "comments": comments,
    }


def build_winrate_section(s1, s2, t1, t2):
    """Returns WinRateSection dict."""
    wr1, wr2 = s1["win_rate"], s2["win_rate"]
    comments = []
    diff = abs(wr1 - wr2)
    fav, dog = (t1, t2) if wr1 > wr2 else (t2, t1)
    fav_wr, dog_wr = max(wr1, wr2), min(wr1, wr2)
    if diff > 20:
        comments.append(f'🏆 <b>Domínio claro:</b> {fav} tem {fav_wr:.0f}% de WR vs {dog_wr:.0f}% de {dog} — uma diferença de <b>{diff:.0f}%</b>. Odds pré-jogo provavelmente já refletem isso; procure valor em mercados de handicap ou props.')
    elif diff > 10:
        comments.append(f'📊 <b>Vantagem moderada:</b> {fav} lidera com {fav_wr:.0f}% vs {dog_wr:.0f}%. A diferença de {diff:.0f}% sugere que {fav} é favorito mas não dominante.')
    else:
        comments.append(f'⚖️ <b>Duelo equilibrado:</b> WR próximos ({wr1:.0f}% vs {wr2:.0f}%). Neste cenário, fatores como draft, forma recente e EGR/MLR serão decisivos.')
    if fav_wr > 65:
        comments.append(f'💰 {fav} com WR acima de 65% é um time de <b>tier superior</b>. Odds de ML podem estar comprimidas — considere <b>Handicap -1.5 ou -2.5</b> para melhor valor.')
    if dog_wr < 35:
        comments.append(f'⚠️ {dog} com WR abaixo de 35% está em dificuldade. Apostar neste time como ML é arriscado, mas <b>Handicap +5.5 kills</b> pode oferecer proteção.')

    return {
        "t1_win_rate": wr1,
        "t2_win_rate": wr2,
        "t1_wins": s1["wins"],
        "t2_wins": s2["wins"],
        "t1_total": s1["total_games"],
        "t2_total": s2["total_games"],
        "explain_text": "O <b>Win Rate</b> é o indicador mais direto de performance. Delta vs 50% mostra o quanto o time está acima ou abaixo da média.",
        "comments": comments,
    }


def build_recent_form_section(s1, s2, t1, t2):
    """Returns RecentFormSection dict."""
    r1 = s1.get("recent_results", [])
    r2 = s2.get("recent_results", [])
    wr1 = sum(1 for r in r1 if r == "1") / len(r1) * 100 if r1 else 0
    wr2 = sum(1 for r in r2 if r == "1") / len(r2) * 100 if r2 else 0

    comments = []
    for team_name, results, color in [(t1, r1, "#3b82f6"), (t2, r2, "#ef4444")]:
        if not results:
            continue
        recent_wr = sum(1 for r in results if r == "1") / len(results) * 100
        streak_type, streak_count = None, 0
        for r in reversed(results):
            if streak_type is None:
                streak_type = r
                streak_count = 1
            elif r == streak_type:
                streak_count += 1
            else:
                break
        if streak_count >= 4 and streak_type == "1":
            comments.append(f'🔥 <b>{team_name} em sequência de {streak_count} vitórias!</b> Momentum forte — odds pré-jogo podem estar comprimidas.')
        elif streak_count >= 3 and streak_type == "0":
            comments.append(f'📉 <b>{team_name} em sequência de {streak_count} derrotas.</b> Momento negativo pode afetar moral.')
        if recent_wr >= 80:
            comments.append(f'⭐ {team_name} com <b>{recent_wr:.0f}% WR recente</b> (últimos 10 jogos). Desempenho excepcional no período recente.')
        elif recent_wr <= 20:
            comments.append(f'⚠️ {team_name} com apenas <b>{recent_wr:.0f}% WR recente</b>. Time em crise — risco elevado para ML.')

    return {
        "t1_results": [str(r) for r in r1],
        "t2_results": [str(r) for r in r2],
        "t1_recent_wr": wr1,
        "t2_recent_wr": wr2,
        "comments": comments,
    }


# ============================================================================
# Distribution Section Builders
# ============================================================================

def build_kills_total_section(s1, s2, t1, t2, mult1, mult2):
    """Returns DistributionSection dict for total kills."""
    k1 = int_list(s1.get("kills_history", []))
    k2 = int_list(s2.get("kills_history", []))
    min_len = min(len(k1), len(k2))
    if min_len == 0:
        return None
    total = [k1[i] + k2[i] for i in range(min_len)]
    st = calc_stats(total)
    if not st:
        return None

    bet_entries = []
    for lv in [st["avg"] - 5, st["avg"] - 2.5, st["avg"], st["avg"] + 2.5, st["avg"] + 5]:
        line_v = round(lv * 2) / 2
        prob_over = sum(1 for v in total if v > line_v) / len(total) * 100
        prob_under = 100 - prob_over
        e = make_bet_entry(
            f"{t1}+{t2}", "Over", f"{line_v:.1f} kills", prob_over, len(total),
            f"Em {sum(1 for v in total if v > line_v)} de {len(total)} jogos o total de kills foi > {line_v:.1f}. "
            f"Média histórica: {st['avg']:.1f}, Mediana: {st['med']:.1f}, Desvio Padrão: {st['std']:.1f}. "
            f"{'Alta confiança: a linha está abaixo da média.' if line_v < st['avg'] else 'Linha acima da média: depende de jogos sangrentos (alto CKPM).'}",
        )
        if e:
            bet_entries.append(e)
        e2 = make_bet_entry(
            f"{t1}+{t2}", "Under", f"{line_v:.1f} kills", prob_under, len(total),
            f"Em {sum(1 for v in total if v <= line_v)} de {len(total)} jogos o total de kills foi ≤ {line_v:.1f}. "
            f"{'Conservador: linha acima da média favorece Under.' if line_v > st['avg'] else 'Arriscado: linha abaixo da média desfavorece Under.'}",
        )
        if e2:
            bet_entries.append(e2)

    draft_projection = None
    if mult1 and mult2:
        m1 = mult1.get("kills", 1.0)
        m2 = mult2.get("kills", 1.0)
        proj_avg1 = (sum(k1) / len(k1)) * m1 if k1 else 0
        proj_avg2 = (sum(k2) / len(k2)) * m2 if k2 else 0
        draft_projection = {"avg_base": st["avg"], "proj_total": proj_avg1 + proj_avg2, "mult_t1": m1, "mult_t2": m2}

    comments = []
    if st["avg"] > 25:
        pct_25 = sum(1 for v in total if v > 22.5) / len(total) * 100
        comments.append(f'⚔️ <b>Média de {st["avg"]:.1f} abates totais.</b> Esses times geram jogos sangrentos — <b>Over 22.5 kills</b> cobriu em <b>{pct_25:.0f}%</b> dos jogos históricos.')
    elif st["avg"] < 20:
        pct_20 = sum(1 for v in total if v <= 20.5) / len(total) * 100
        comments.append(f'🧊 <b>Média baixa de {st["avg"]:.1f} abates.</b> Partidas controladas com poucas lutas. <b>Under 22.5 kills</b> cobriu em <b>{pct_20:.0f}%</b> dos jogos.')
    if st["std"] > 5:
        comments.append(f'🎲 <b>Alta volatilidade (σ={st["std"]:.1f}).</b> Os resultados variam muito — linhas próximas da média têm risco elevado.')
    elif st["std"] < 3:
        comments.append(f'🎯 <b>Consistência alta (σ={st["std"]:.1f}).</b> Resultados previsíveis — a maioria dos jogos cai próximo da média ({st["avg"]:.1f}).')

    return {
        "title": f"⚔️ Total de Abates na Partida — {t1} vs {t2}",
        "histogram_data": [float(v) for v in total],
        "stats": st,
        "bet_entries": bet_entries,
        "draft_projection": draft_projection,
        "explain_text": (
            "A distribuição do <b>total de kills na partida</b> (soma). É guiada pela métrica global <b>CKPM</b> detalhada acima. "
            "Em jogos com times sanguinários, a cauda longa no gráfico encosta nos 40-50 abates."
        ),
        "comments": comments,
    }


def build_kills_per_team_section(s1, s2, t1, t2, mult1, mult2):
    """Returns KillsPerTeamSection dict."""
    raw1 = int_list(s1.get("kills_history", []))
    raw2 = int_list(s2.get("kills_history", []))
    st1 = calc_stats(raw1) if raw1 else {}
    st2 = calc_stats(raw2) if raw2 else {}

    def make_over_entries(raw, stats, team):
        entries = []
        if not raw or not stats:
            return entries
        avg_k = stats["avg"]
        for lv in [round((avg_k - 2) * 2) / 2, round(avg_k * 2) / 2, round((avg_k + 2) * 2) / 2]:
            prob_o = sum(1 for v in raw if v > lv) / len(raw) * 100
            e = make_bet_entry(
                team, "Over Kills", f"{lv:.1f} kills", prob_o, len(raw),
                f"Em {sum(1 for v in raw if v > lv)} de {len(raw)} jogos, {team} teve > {lv:.1f} kills. "
                f"Média histórica: {avg_k:.1f}.",
            )
            if e:
                entries.append(e)
        return entries

    t1_bets = make_over_entries(raw1, st1, t1)
    t2_bets = make_over_entries(raw2, st2, t2)

    draft_projection = None
    if mult1 and mult2:
        avg1 = sum(raw1) / len(raw1) if raw1 else 0
        avg2 = sum(raw2) / len(raw2) if raw2 else 0
        m1 = mult1.get("kills", 1.0)
        m2 = mult2.get("kills", 1.0)
        draft_projection = {"t1_base": avg1, "t1_proj": avg1 * m1, "t2_base": avg2, "t2_proj": avg2 * m2}

    comments = []
    avg1_k = sum(raw1) / len(raw1) if raw1 else 0
    avg2_k = sum(raw2) / len(raw2) if raw2 else 0
    if avg1_k > 0 and avg2_k > 0:
        ratio = max(avg1_k, avg2_k) / min(avg1_k, avg2_k)
        dominant = t1 if avg1_k > avg2_k else t2
        if ratio > 1.25:
            comments.append(f'🎯 <b>{dominant} é {ratio:.1f}x mais letal</b> em kills individuais (média {max(avg1_k,avg2_k):.1f} vs {min(avg1_k,avg2_k):.1f}). Handicap de kills favorece {dominant}.')
        else:
            comments.append(f'⚖️ <b>Produção de kills equilibrada</b> ({t1}: {avg1_k:.1f} vs {t2}: {avg2_k:.1f}). Diferença pequena dificulta apostas de handicap — foque em Over/Under total.')
    egr1 = (s1.get("fb_rate", 0) + s1.get("fd_rate", 0)) / 2
    egr2 = (s2.get("fb_rate", 0) + s2.get("fd_rate", 0)) / 2
    for team, avg_k, egr in [(t1, avg1_k, egr1), (t2, avg2_k, egr2)]:
        if avg_k > 12 and egr < 40:
            comments.append(f'⚠️ <b>{team} tem muitas kills ({avg_k:.1f}) mas EGR baixo ({egr:.0f}%).</b> Kills reativas nem sempre se convertem em vitórias.')

    return {
        "t1_histogram": [float(v) for v in raw1],
        "t2_histogram": [float(v) for v in raw2],
        "t1_stats": st1 if st1 else None,
        "t2_stats": st2 if st2 else None,
        "t1_bet_entries": t1_bets,
        "t2_bet_entries": t2_bets,
        "draft_projection": draft_projection,
        "explain_text": (
            "A <b>Odd ideal</b> exibida refere-se à entrada <b>Over X.X kills</b> (arredondamento da média). "
            "Se o time puxar mais que a média histórica, a linha é coberta. Kills por time medem a pressão terminal, "
            "mas times com alta kill rate sem EGR alto podem estar apenas sendo engajados frequentemente."
        ),
        "comments": comments,
    }


def build_handicap_section(s1, s2, t1, t2, mult1, mult2):
    """Returns HandicapSection dict."""
    k1_hist = [v for v in s1.get("kills_history", []) if v is not None]
    k2_hist = [v for v in s2.get("kills_history", []) if v is not None]
    m1_k = mult1.get("kills", 1.0) if mult1 else 1.0
    m2_k = mult2.get("kills", 1.0) if mult2 else 1.0
    min_k = min(len(k1_hist), len(k2_hist))
    adj_kd1 = [(k1_hist[i] * m1_k) - (k2_hist[i] * m2_k) for i in range(min_k)]
    adj_kd2 = [(k2_hist[i] * m2_k) - (k1_hist[i] * m1_k) for i in range(min_k)]

    hist1 = [int(round(v)) for v in s1.get("kill_diff_history", []) if v is not None]
    hist2 = [int(round(v)) for v in s2.get("kill_diff_history", []) if v is not None]
    st1 = calc_stats(hist1) if hist1 else {}
    st2 = calc_stats(hist2) if hist2 else {}

    bet_entries = []
    for team, adj_kd, hist_kd, m_team, m_opp in [
        (t1, adj_kd1, hist1, m1_k, m2_k),
        (t2, adj_kd2, hist2, m2_k, m1_k),
    ]:
        for hc in [-5.5, -4.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
            prob_hc, cnt = _rate_prob(adj_kd, lambda v, h=hc: v > h)
            if prob_hc is not None and prob_hc > 5:
                sign = "+" if hc >= 0 else ""
                st_kd = calc_stats(hist_kd) if hist_kd else {}
                avg_adj = sum(adj_kd) / len(adj_kd) if adj_kd else (st_kd.get("avg", 0) if st_kd else 0)
                e = make_bet_entry(
                    team, "Handicap", f"{sign}{hc:.1f} kills", prob_hc, cnt,
                    f"Calculado usando as kills ajustadas pelo draft (Este time: {m_team:.2f}x, Inimigo: {m_opp:.2f}x). "
                    f"Diff Histórica Média: {st_kd.get('avg', 0):+.1f} ➡️ <b>Projeção c/ Draft: {avg_adj:+.1f}</b>.<br><br>"
                    f"{'Linha conservadora (negativa).' if hc < 0 else 'Linha agressiva — precisa de domínio.'}",
                    has_draft=(m_team != 1.0 or m_opp != 1.0),
                )
                if e:
                    bet_entries.append(e)

    draft_projection = None
    if mult1 and mult2:
        avg1 = sum(k1_hist) / len(k1_hist) if k1_hist else 0
        avg2 = sum(k2_hist) / len(k2_hist) if k2_hist else 0
        draft_projection = {"proj_diff_t1": (avg1 * m1_k) - (avg2 * m2_k), "mult_t1": m1_k, "mult_t2": m2_k}

    comments = []
    if hist1:
        avg_d1 = sum(hist1) / len(hist1)
        if avg_d1 > 3:
            pct_35 = sum(1 for v in hist1 if v > 3.5) / len(hist1) * 100
            comments.append(f'📈 <b>{t1} domina historicamente</b> com handicap médio de <b>{avg_d1:+.1f}</b>. Handicap -3.5 cobriu em {pct_35:.0f}% dos jogos.')
        elif avg_d1 < -3:
            pct_p35 = sum(1 for v in hist1 if v > -3.5) / len(hist1) * 100
            comments.append(f'📉 <b>{t1} costuma perder por margem grande</b> (média {avg_d1:+.1f}). Handicap +3.5 cobriu em {pct_p35:.0f}% dos jogos.')
    if hist2:
        avg_d2 = sum(hist2) / len(hist2)
        if avg_d2 > 3:
            pct_35 = sum(1 for v in hist2 if v > 3.5) / len(hist2) * 100
            comments.append(f'📈 <b>{t2} domina historicamente</b> com handicap médio de <b>{avg_d2:+.1f}</b>. Handicap -3.5 cobriu em {pct_35:.0f}% dos jogos.')
        elif avg_d2 < -3:
            pct_p35 = sum(1 for v in hist2 if v > -3.5) / len(hist2) * 100
            comments.append(f'📉 <b>{t2} costuma perder por margem grande</b> (média {avg_d2:+.1f}). Handicap +3.5 cobriu em {pct_p35:.0f}%.')
    if hist1 and hist2:
        avg_d1 = sum(hist1) / len(hist1)
        avg_d2 = sum(hist2) / len(hist2)
        if abs(avg_d1) < 2 and abs(avg_d2) < 2:
            comments.append(f'⚖️ <b>Ambos os times têm handicap próximo de zero.</b> Jogos tendem a ser equilibrados em kills — linhas de handicap extremas têm baixa cobertura.')

    return {
        "t1_histogram": [float(v) for v in hist1],
        "t2_histogram": [float(v) for v in hist2],
        "t1_stats": st1 if st1 else None,
        "t2_stats": st2 if st2 else None,
        "bet_entries": bet_entries,
        "draft_projection": draft_projection,
        "explain_text": (
            "🎮 <b>O que é o Handicap de Kills?</b><br>"
            "O Handicap mede a <b>diferença entre kills do time e kills sofridas</b> (teamkills - teamdeaths). "
            "Na prática, funciona assim:<br><br>"
            "<b>Exemplo 1:</b> Se você aposta em <b>FURIA Handicap -3.5</b>, a FURIA precisa vencer a partida com pelo menos "
            "<b>4 kills a mais</b> que o adversário (ex: 15×11 = diff +4 ✔️, 12×10 = diff +2 ❌).<br>"
            "<b>Exemplo 2:</b> Se você aposta em <b>Sentinels Handicap +5.5</b>, os Sentinels podem até <b>perder por até 5 kills de diferença</b> "
            "e sua aposta cobre (ex: 8×12 = diff -4 ✔️, 5×12 = diff -7 ❌).<br><br>"
            "<b>Handicap negativo (-)</b> = time precisa dominar. <b>Handicap positivo (+)</b> = time recebe \"vantagem\" virtual. "
            "Quanto mais extrema a linha, maior a odd e o risco."
        ),
        "comments": comments,
    }


def build_dragons_section(s1, s2, t1, t2, mult1, mult2):
    """Returns DistributionSection dict for dragons."""
    d1 = int_list(s1.get("dragons_history", []))
    d2 = int_list(s2.get("dragons_history", []))
    min_len = min(len(d1), len(d2))
    if min_len == 0:
        return None
    total = [d1[i] + d2[i] for i in range(min_len)]
    st = calc_stats(total)
    if not st:
        return None

    bet_entries = []
    for lv in [3.5, 4.5, 5.5]:
        prob_o = sum(1 for v in total if v > lv) / len(total) * 100
        e = make_bet_entry(
            f"{t1}+{t2}", "Over", f"{lv:.1f} dragões", prob_o, len(total),
            f"Em {sum(1 for v in total if v > lv)} de {len(total)} jogos, o total de dragões foi > {lv:.1f}. "
            f"Média combinada: {st['avg']:.1f}. Dragon Soul exige 4 dragões para um time.",
        )
        if e:
            bet_entries.append(e)

    draft_projection = None
    if mult1 and mult2:
        avg1 = sum(d1) / len(d1) if d1 else 0
        avg2 = sum(d2) / len(d2) if d2 else 0
        m1 = mult1.get("dragons", 1.0)
        m2 = mult2.get("dragons", 1.0)
        draft_projection = {"avg_base": avg1 + avg2, "proj_total": (avg1 * m1) + (avg2 * m2)}

    comments = []
    avg_dr1 = sum(d1) / len(d1) if d1 else 0
    avg_dr2 = sum(d2) / len(d2) if d2 else 0
    for team, avg_dr, fd_rate, dr_list in [(t1, avg_dr1, s1.get("fd_rate", 0), d1), (t2, avg_dr2, s2.get("fd_rate", 0), d2)]:
        if fd_rate > 60 and avg_dr > 3:
            pct_35 = sum(1 for v in dr_list if v > 3.5) / len(dr_list) * 100 if dr_list else 0
            comments.append(f'🐉 <b>{team} domina objetivos bot-side</b> (FD% {fd_rate:.0f}%, média {avg_dr:.1f} dragões). <b>Over 3.5 dragões</b> para o time cobriu em <b>{pct_35:.0f}%</b>.')
        elif avg_dr < 2:
            comments.append(f'⚠️ <b>{team} conquista poucos dragões (média {avg_dr:.1f}).</b> Fraco no controle bot-side.')
    avg_total_dr = sum(total) / len(total) if total else 0
    if avg_total_dr > 6:
        comments.append(f'🔥 <b>Média de {avg_total_dr:.1f} dragões totais por jogo.</b> Alta contestação de dragões indica jogos longos. Over 5.5 dragões totais é uma aposta consistente.')

    return {
        "title": "🐉 Distribuições de Dragões",
        "histogram_data": [float(v) for v in total],
        "stats": st,
        "bet_entries": bet_entries,
        "draft_projection": draft_projection,
        "explain_text": (
            "O controle de <b>Dragões</b> é um proxy do domínio bot-side e da visão do rio. Times com FD% alto tendem a "
            "acumular 3-4 dragões de modo mais consistente. O Dragon Soul (~4 dragões) é um gamechanger."
        ),
        "comments": comments,
    }


def build_towers_section(s1, s2, t1, t2, mult1, mult2):
    """Returns DistributionSection dict for towers."""
    t1_d = int_list(s1.get("towers_history", []))
    t2_d = int_list(s2.get("towers_history", []))
    min_len = min(len(t1_d), len(t2_d))
    if min_len == 0:
        return None
    total = [t1_d[i] + t2_d[i] for i in range(min_len)]
    st = calc_stats(total)
    if not st:
        return None

    bet_entries = []
    for lv in [10.5, 12.5, 14.5]:
        prob_o = sum(1 for v in total if v > lv) / len(total) * 100
        e = make_bet_entry(
            f"{t1}+{t2}", "Over", f"{lv:.1f} torres", prob_o, len(total),
            f"Em {sum(1 for v in total if v > lv)} de {len(total)} jogos, o total de torres foi > {lv:.1f}. "
            f"Média combinada: {st['avg']:.1f}. Existem 11 torres por time (22 no total).",
        )
        if e:
            bet_entries.append(e)

    draft_projection = None
    if mult1 and mult2:
        avg1 = sum(t1_d) / len(t1_d) if t1_d else 0
        avg2 = sum(t2_d) / len(t2_d) if t2_d else 0
        m1 = mult1.get("towers", 1.0)
        m2 = mult2.get("towers", 1.0)
        draft_projection = {"avg_base": avg1 + avg2, "proj_total": (avg1 * m1) + (avg2 * m2)}

    comments = []
    avg_tw1 = sum(t1_d) / len(t1_d) if t1_d else 0
    avg_tw2 = sum(t2_d) / len(t2_d) if t2_d else 0
    for team, avg_tw, tw_list in [(t1, avg_tw1, t1_d), (t2, avg_tw2, t2_d)]:
        if avg_tw > 7:
            pct_55 = sum(1 for v in tw_list if v > 5.5) / len(tw_list) * 100 if tw_list else 0
            comments.append(f'🏰 <b>{team} destrói média de {avg_tw:.1f} torres</b> — excelente conversão de vantagem. <b>Over 5.5 torres</b> cobriu em <b>{pct_55:.0f}%</b>.')
        elif avg_tw < 4:
            comments.append(f'⚠️ <b>{team} destrói poucas torres (média {avg_tw:.1f}).</b> Time que tem dificuldade em converter vantagens em estruturas.')
    if abs(avg_tw1 - avg_tw2) > 2:
        dom_t = t1 if avg_tw1 > avg_tw2 else t2
        comments.append(f'📊 <b>Diferença de {abs(avg_tw1-avg_tw2):.1f} torres entre os times.</b> {dom_t} é muito superior em siege.')

    return {
        "title": "🏰 Distribuições de Torres",
        "histogram_data": [float(v) for v in total],
        "stats": st,
        "bet_entries": bet_entries,
        "draft_projection": draft_projection,
        "explain_text": (
            "O <b>MLR (Mid/Late Rating)</b> mostra que torres destruídas indicam conversão de vantagem. "
            "Times que pegam Barão mas não derrubam torres são passivos e falham em <i>snowballar</i>."
        ),
        "comments": comments,
    }


def build_barons_section(s1, s2, t1, t2, mult1, mult2):
    """Returns DistributionSection dict for barons."""
    b1 = int_list(s1.get("barons_history", []))
    b2 = int_list(s2.get("barons_history", []))
    min_len = min(len(b1), len(b2))
    if min_len == 0:
        return None
    total = [b1[i] + b2[i] for i in range(min_len)]
    st = calc_stats(total)
    if not st:
        return None

    bet_entries = []
    for lv in [0.5, 1.5]:
        prob_o = sum(1 for v in total if v > lv) / len(total) * 100
        e = make_bet_entry(
            f"{t1}+{t2}", "Over", f"{lv:.1f} barões", prob_o, len(total),
            f"Em {sum(1 for v in total if v > lv)} de {len(total)} jogos, o total de barões foi > {lv:.1f}. "
            f"Média combinada: {st['avg']:.1f}. Jogos que ultrapassam 25min tendem a ter pelo menos 1 Barão.",
        )
        if e:
            bet_entries.append(e)

    draft_projection = None
    if mult1 and mult2:
        avg1 = sum(b1) / len(b1) if b1 else 0
        avg2 = sum(b2) / len(b2) if b2 else 0
        m1 = mult1.get("barons", 1.0)
        m2 = mult2.get("barons", 1.0)
        draft_projection = {"avg_base": avg1 + avg2, "proj_total": (avg1 * m1) + (avg2 * m2)}

    comments = []
    fbr1 = s1.get("fbaron_rate", 0)
    fbr2 = s2.get("fbaron_rate", 0)
    for team, br, fbr in [(t1, b1, fbr1), (t2, b2, fbr2)]:
        if fbr > 60:
            pct_05 = sum(1 for v in br if v > 0.5) / len(br) * 100 if br else 0
            comments.append(f'💚 <b>{team} controla o Baron Pit ({fbr:.0f}% First Baron).</b> <b>Over 0.5 Barões</b> cobriu em <b>{pct_05:.0f}%</b> dos jogos.')
        elif fbr < 30:
            comments.append(f'⚠️ <b>{team} raramente conquista o First Baron ({fbr:.0f}%).</b> Sem controle do Baron Pit, o time depende de teamfights desesperadas no late.')
    avg_total_b = sum(total) / len(total) if total else 0
    if avg_total_b > 1.5:
        comments.append(f'🔥 <b>Média de {avg_total_b:.1f} barões por jogo.</b> Jogos tendem a ter múltiplos Barões — indicativo de partidas longas. <b>Over 1.5 Barões</b> tem valor.')

    return {
        "title": "💚 Distribuições de Barões",
        "histogram_data": [float(v) for v in total],
        "stats": st,
        "bet_entries": bet_entries,
        "draft_projection": draft_projection,
        "explain_text": (
            "O <b>Barão Nashor</b> é o principal indicador do MLR. Seu buff de empurro de lanes permite cercar torres e inibidores. "
            "Times que controlam o Baron Pit ditam o ritmo do mid-late game."
        ),
        "comments": comments,
    }


def build_duration_section(s1, s2, t1, t2, mult1, mult2):
    """Returns DistributionSection dict for game duration."""
    all_dur = [v for v in s1.get("duration_history", []) + s2.get("duration_history", []) if v]
    if not all_dur:
        return None
    st = calc_stats(all_dur)
    if not st:
        return None

    bet_entries = []
    for lv in [25.5, 28.5, 31.5, 34.5, 37.5]:
        p_over = sum(1 for v in all_dur if v > lv) / len(all_dur) * 100
        p_under = 100 - p_over
        e = make_bet_entry(
            f"{t1}+{t2}", "Over", f"{lv}min", p_over, len(all_dur),
            f"Em {sum(1 for v in all_dur if v > lv)} de {len(all_dur)} jogos a duração excedeu {lv}min. "
            f"Média: {st['avg']:.1f}min, Mediana: {st['med']:.1f}min. "
            f"{'Linha conservadora.' if lv < st['avg'] else 'Linha agressiva — requer jogos longos.'}",
        )
        if e:
            bet_entries.append(e)
        e2 = make_bet_entry(
            f"{t1}+{t2}", "Under", f"{lv}min", p_under, len(all_dur),
            f"Em {sum(1 for v in all_dur if v <= lv)} de {len(all_dur)} jogos a duração foi ≤ {lv}min. "
            f"{'Favorável: linha acima da média.' if lv > st['avg'] else 'Arriscado: linha abaixo da média.'}",
        )
        if e2:
            bet_entries.append(e2)

    draft_projection = None
    if mult1 and mult2:
        m1 = mult1.get("duration", 1.0)
        m2 = mult2.get("duration", 1.0)
        d1 = [v for v in s1.get("duration_history", []) if v]
        d2 = [v for v in s2.get("duration_history", []) if v]
        proj_dur1 = (sum(d1) / len(d1)) * m1 if d1 else 0
        proj_dur2 = (sum(d2) / len(d2)) * m2 if d2 else 0
        draft_projection = {"avg_base": st["avg"], "proj_total": (proj_dur1 + proj_dur2) / 2}

    comments = []
    if st["avg"] > 33:
        pct_31 = sum(1 for v in all_dur if v > 31.5) / len(all_dur) * 100
        comments.append(f'⏱️ <b>Jogos longos (média {st["avg"]:.1f}min).</b> <b>Over 31.5min</b> cobriu em <b>{pct_31:.0f}%</b> dos jogos. Favorável para apostas de duração longa e correlacionado com <b>Over em Barões</b>.')
    elif st["avg"] < 28:
        pct_28 = sum(1 for v in all_dur if v <= 28.5) / len(all_dur) * 100
        comments.append(f'⚡ <b>Jogos rápidos (média {st["avg"]:.1f}min).</b> <b>Under 28.5min</b> cobriu em <b>{pct_28:.0f}%</b>. Favorável para <b>Under em Barões 0.5</b>.')
    else:
        comments.append(f'⏰ <b>Duração média padrão ({st["avg"]:.1f}min).</b> Sem tendência clara de jogos curtos ou longos. Linha de 31.5min é o pivot.')
    d1_data = [v for v in s1.get("duration_history", []) if v]
    d2_data = [v for v in s2.get("duration_history", []) if v]
    if d1_data and d2_data:
        avg_d1 = sum(d1_data) / len(d1_data)
        avg_d2 = sum(d2_data) / len(d2_data)
        if abs(avg_d1 - avg_d2) > 3:
            faster = t1 if avg_d1 < avg_d2 else t2
            comments.append(f'📊 <b>Diferença de ritmo:</b> {faster} joga partidas ~{abs(avg_d1-avg_d2):.0f}min mais curtas. O estilo do {faster} (early-game) pode forçar resolução rápida.')

    return {
        "title": "⏱ Duração do Jogo (AGT)",
        "histogram_data": [float(v) for v in all_dur],
        "stats": st,
        "bet_entries": bet_entries,
        "draft_projection": draft_projection,
        "explain_text": (
            "A <b>Duração (AGT - Avg Game Time)</b> reflete se os times controlam o pace. Um time de EGR baixo e AGT alto "
            "joga na defensiva pelas torres e falha nas chamadas de Barão."
        ),
        "comments": comments,
    }


# ============================================================================
# EV Finder Section Builder
# ============================================================================

def _ev_gen_winner_entries(stats, team, n, fb, fd, fh, m_team):
    """Generates winner (ML) bet entries as dicts."""
    m_fb = m_team.get("firstblood", 1.0) if m_team else 1.0
    m_fd = m_team.get("firstdragon", 1.0) if m_team else 1.0
    m_fh = m_team.get("firstherald", 1.0) if m_team else 1.0
    avg_early_m = (m_fb + m_fd + m_fh) / 3 if m_fb and m_fd and m_fh else 1.0

    wr = stats["win_rate"]
    adj_wr = min(wr * avg_early_m, 95)
    egr_score = (fb + fd + fh) / 3
    mlr_indicators = (stats["avg_barons"] + stats["avg_inhibitors"] + stats["avg_towers"] / 5) / 3
    combined_score = adj_wr * 0.5 + egr_score * 0.3 + min(mlr_indicators * 20, 100) * 0.2

    has_draft = avg_early_m != 1.0
    e = make_bet_entry(
        team, "Vencedor (ML)", "Moneyline", combined_score, n,
        f"Win Rate histórico: {wr:.1f}%. Projeção c/ Draft: {adj_wr:.1f}%. "
        f"EGR Proxy Score (FB%+FD%+HLD%)/3: {egr_score:.0f}%. "
        f"MLR Proxy (Barões+Inibs+Torres): {mlr_indicators:.2f}. "
        f"Score Combinado: {combined_score:.0f}%.<br><br><b>💡 Conselho do Draft:</b> Sinergias escolhidas alteram a Força de Early Game em <b>{avg_early_m:.2f}x</b>.",
        has_draft=has_draft,
        draft_mult=avg_early_m if has_draft else None,
    )
    return [e] if e else []


def _ev_gen_over_kills_entries(stats, team, kills, avg_k, egpm_data, dpm_data, mult=1.0):
    """Generates Over Kills bet entries as dicts."""
    entries = []
    adj_kills = [(v * mult) for v in kills if v is not None] if kills else []
    avg_adj = sum(adj_kills) / len(adj_kills) if adj_kills else avg_k
    has_draft = mult != 1.0

    for line in [round((avg_k - 2) * 2) / 2, round(avg_k * 2) / 2, round((avg_k + 2) * 2) / 2]:
        prob_o, cnt = _rate_prob(adj_kills, lambda v, l=line: v > l)
        if prob_o is not None and prob_o > 5:
            egpm_avg = sum(float_list(egpm_data)) / len(float_list(egpm_data)) if float_list(egpm_data) else 0
            dpm_avg = sum(float_list(dpm_data)) / len(float_list(dpm_data)) if float_list(dpm_data) else 0
            e = make_bet_entry(
                team, "Over Kills", f"{line:.1f}", prob_o, cnt,
                f"Em {sum(1 for v in adj_kills if v > line)} simulações ajustadas (de {cnt} reais), a projeção passa de {line:.1f}. "
                f"Multiplicador do draft: <b>{mult:.2f}x</b>. Média Histórica {avg_k:.1f} ➡️ <b>{avg_adj:.1f} proj</b>.<br><br>"
                f"KPM: {stats['avg_kpm']:.2f}, CKPM: {stats['avg_ckpm']:.2f}. "
                f"EGPM ({egpm_avg:.0f}/min) e DPM ({dpm_avg:.0f}/min).",
                has_draft=has_draft,
                draft_mult=mult if has_draft else None,
            )
            if e:
                entries.append(e)
    return entries


def _ev_gen_handicap_entries(stats, team, adj_kd, hist_kd, m_team, m_opp):
    """Generates Handicap bet entries as dicts."""
    if not adj_kd:
        return []
    entries = []
    st_kd = calc_stats(hist_kd) if hist_kd else {}
    has_draft = m_team != 1.0 or m_opp != 1.0
    for hc in [-5.5, -4.5, -3.5, -2.5, -1.5, -0.5, 0.5, 1.5, 2.5, 3.5, 4.5, 5.5]:
        prob_hc, cnt = _rate_prob(adj_kd, lambda v, h=hc: v > h)
        if prob_hc is not None and prob_hc > 5:
            sign = "+" if hc >= 0 else ""
            avg_adj = sum(adj_kd) / len(adj_kd) if adj_kd else st_kd.get("avg", 0)
            e = make_bet_entry(
                team, "Handicap", f"{sign}{hc:.1f} kills", prob_hc, cnt,
                f"Calculado usando as kills ajustadas pelo draft (Este time: {m_team:.2f}x, Inimigo: {m_opp:.2f}x). "
                f"Diff Histórica Média: {st_kd.get('avg', 0):+.1f} ➡️ <b>Projeção c/ Draft: {avg_adj:+.1f}</b>.<br><br>"
                f"{'Linha conservadora (negativa).' if hc < 0 else 'Linha agressiva — precisa de domínio.'}",
                has_draft=has_draft,
                draft_mult=m_team if has_draft else None,
            )
            if e:
                entries.append(e)
    return entries


def _ev_gen_first_to_x_kills(stats, team, opp_stats, n, m_team):
    """Generates First to X Kills proxy entries as dicts."""
    entries = []
    m_fb = m_team.get("firstblood", 1.0) if m_team else 1.0
    m_k = m_team.get("kills", 1.0) if m_team else 1.0
    kpm_diff = (stats["avg_kpm"] * m_k) - opp_stats["avg_kpm"]
    fb = stats["fb_rate"] * m_fb
    wr = stats["win_rate"]
    prob_5 = min(max((fb * 0.6) + (kpm_diff * 40) + 20, 10), 90)
    prob_10 = min(max((fb * 0.4) + (kpm_diff * 60) + 30, 10), 90)
    prob_15 = min(max((wr * 0.5) + (kpm_diff * 80) + 25, 10), 90)
    has_draft = m_k != 1.0 or m_fb != 1.0
    math_base = (
        "<br><br><b>🧮 Matemática do Proxy Model:</b><br>"
        f"• <b>FB% Ajustado ({fb:.0f}%):</b> Taxa (peso maior no 'First to 5', Mult Draft: {m_fb:.2f}x).<br>"
        f"• <b>KPM Diff ({kpm_diff:+.2f}):</b> Diferença de agressividade entre times, após Draft.<br>"
        f"• <b>WR ({wr:.0f}%):</b> Probabilidade de vitória (peso no 'First to 15').<br><br>"
    )
    for label, prob in [("Primeiro a 5 Kills", prob_5), ("Primeiro a 10 Kills", prob_10), ("Primeiro a 15 Kills", prob_15)]:
        e = make_bet_entry(
            team, "Corrida Abates", label, prob, n,
            f"Estimativa Proxy para corrida de abates. {math_base}"
            "<b>💡 Conselho do Draft:</b> Multiplicadores de kills e First Blood da composição influenciam fortemente a primeira fase.",
            has_draft=has_draft,
            draft_mult=m_k if has_draft else None,
        )
        if e:
            entries.append(e)
    return entries


def _ev_gen_joint_totals_dicts(arr1, arr2, market, lines_func, explain_text, m1=1.0, m2=1.0):
    """Generates joint total bet entries as dicts."""
    if not arr1 or not arr2:
        return []
    min_len = min(len(arr1), len(arr2))
    joint_base = [arr1[i] + arr2[i] for i in range(min_len)]
    joint_adj = [(arr1[i] * m1) + (arr2[i] * m2) for i in range(min_len)]
    st_base = calc_stats(joint_base)
    avg_base = st_base["avg"] if st_base else 0
    avg_adj = sum(joint_adj) / len(joint_adj) if joint_adj else avg_base
    has_draft = m1 != 1.0 or m2 != 1.0
    entries = []
    lines = lines_func(avg_base)
    for line in lines:
        prob_adj, cnt = _rate_prob(joint_adj, lambda v, l=line: v > l)
        if prob_adj is not None and prob_adj > 5:
            e = make_bet_entry(
                "Partida", market, f"Over {line}", prob_adj, cnt,
                f"Soma do histórico ajustado pelo impacto dos campeões (T1: {m1:.2f}x, T2: {m2:.2f}x). "
                f"Média Histórica Pura: {avg_base:.1f} ➡️ <b>Projeção c/ Draft: {avg_adj:.1f}</b>.<br><br>{explain_text}",
                has_draft=has_draft,
                draft_mult=(m1 + m2) / 2 if has_draft else None,
            )
            if e:
                entries.append(e)
    return entries


def build_ev_finder_section(s1, s2, t1, t2, mult1, mult2):
    """Returns EVFinderSection dict with team cards and joint card."""
    k1_hist = [v for v in s1.get("kills_history", []) if v is not None]
    k2_hist = [v for v in s2.get("kills_history", []) if v is not None]
    m1_k = mult1.get("kills", 1.0) if mult1 else 1.0
    m2_k = mult2.get("kills", 1.0) if mult2 else 1.0
    min_k = min(len(k1_hist), len(k2_hist))
    adj_kd1 = [(k1_hist[i] * m1_k) - (k2_hist[i] * m2_k) for i in range(min_k)]
    adj_kd2 = [(k2_hist[i] * m2_k) - (k1_hist[i] * m1_k) for i in range(min_k)]

    def build_team_card(stats, opp_stats, team, color, adj_kd, hist_kd, m_team, m_opp):
        n = stats["total_games"]
        m_t_fb = m_team.get("firstblood", 1.0) if m_team else 1.0
        m_t_fd = m_team.get("firstdragon", 1.0) if m_team else 1.0
        m_t_k = m_team.get("kills", 1.0) if m_team else 1.0
        m_o_k = m_opp.get("kills", 1.0) if m_opp else 1.0

        all_entries = []
        all_entries.extend(_ev_gen_winner_entries(stats, team, n, stats["fb_rate"], stats["fd_rate"], stats["fherald_rate"], m_team))
        all_entries.extend(_ev_gen_over_kills_entries(
            stats, team, stats.get("kills_history", []), stats["avg_kills"],
            stats.get("earnedgold_pm_history", []), stats.get("dmg_pm_history", []),
            m_t_k,
        ))
        all_entries.extend(_ev_gen_handicap_entries(stats, team, adj_kd, hist_kd, m_t_k, m_o_k))
        all_entries.extend(_ev_gen_first_to_x_kills(stats, team, opp_stats, n, m_team))

        # First Blood
        has_fb = m_t_fb != 1.0
        e_fb = make_bet_entry(
            team, "First Blood", "Sim", min(stats["fb_rate"] * m_t_fb, 98), n,
            f"FB% histórico de {team}: {stats['fb_rate']:.0f}% em {n} jogos. Projeção c/ Draft: <b>{stats['fb_rate']*m_t_fb:.0f}%</b>.<br><br>"
            f"<b>💡 Conselho do Draft:</b> Um Multiplicador de FB de {m_t_fb:.2f}x sinaliza um early game {'poderoso.' if m_t_fb >= 1 else 'defensivo.'}",
            has_draft=has_fb,
            draft_mult=m_t_fb if has_fb else None,
        )
        if e_fb:
            all_entries.append(e_fb)

        # First Dragon
        has_fd = m_t_fd != 1.0
        e_fd = make_bet_entry(
            team, "First Dragon", "Sim", min(stats["fd_rate"] * m_t_fd, 98), n,
            f"FD% de {team}: {stats['fd_rate']:.0f}% em {n} jogos. Projeção c/ Draft: <b>{stats['fd_rate']*m_t_fd:.0f}%</b>.<br><br>"
            f"<b>💡 Conselho do Draft:</b> Multiplicador de {m_t_fd:.2f}x indica que a composição tem "
            f"{'ferramentas absurdas para prioridade no Bot/Rio.' if m_t_fd >= 1 else 'dependência de escalar bot.'}",
            has_draft=has_fd,
            draft_mult=m_t_fd if has_fd else None,
        )
        if e_fd:
            all_entries.append(e_fd)

        # Group by market
        market_keys = ["Vencedor (ML)", "Handicap", "Over Kills", "First Blood", "First Dragon", "Corrida Abates"]
        markets = {}
        for mk in market_keys:
            group = [e for e in all_entries if e and e["market"] == mk]
            if group:
                markets[mk] = group

        return {"team": team, "color": color, "markets": markets}

    t1_card = build_team_card(s1, s2, t1, "#60a5fa", adj_kd1, [int(round(v)) for v in s1.get("kill_diff_history", []) if v is not None], mult1, mult2)
    t2_card = build_team_card(s2, s1, t2, "#f87171", adj_kd2, [int(round(v)) for v in s2.get("kill_diff_history", []) if v is not None], mult2, mult1)

    # Joint markets
    m1_d = mult1.get("dragons", 1.0) if mult1 else 1.0
    m2_d = mult2.get("dragons", 1.0) if mult2 else 1.0
    m1_t = mult1.get("towers", 1.0) if mult1 else 1.0
    m2_t = mult2.get("towers", 1.0) if mult2 else 1.0
    m1_b = mult1.get("barons", 1.0) if mult1 else 1.0
    m2_b = mult2.get("barons", 1.0) if mult2 else 1.0
    m1_dur = mult1.get("duration", 1.0) if mult1 else 1.0
    m2_dur = mult2.get("duration", 1.0) if mult2 else 1.0

    joint_entries = []
    if k1_hist and k2_hist:
        joint_entries.extend(_ev_gen_joint_totals_dicts(k1_hist, k2_hist, "Total Kills", lambda a: [round((a-5)*2)/2, round(a*2)/2, round((a+5)*2)/2], "Forte dependência do CKPM combinado (partidas sangrentas).", m1_k, m2_k))

    d1 = [v for v in s1.get("dragons_history", []) if v is not None]
    d2 = [v for v in s2.get("dragons_history", []) if v is not None]
    if d1 and d2:
        joint_entries.extend(_ev_gen_joint_totals_dicts(d1, d2, "Total Dragões", lambda a: [3.5, 4.5, 5.5], "Reflete times que trocam objetivos (Soul games longos aumentam o limite para > 4.5).", m1_d, m2_d))

    t1_h = [v for v in s1.get("towers_history", []) if v is not None]
    t2_h = [v for v in s2.get("towers_history", []) if v is not None]
    if t1_h and t2_h:
        joint_entries.extend(_ev_gen_joint_totals_dicts(t1_h, t2_h, "Total Torres", lambda a: [10.5, 12.5, 14.5], "Jogos mais longos e disputados geram quebras nas duas bases.", m1_t, m2_t))

    b1 = [v for v in s1.get("barons_history", []) if v is not None]
    b2 = [v for v in s2.get("barons_history", []) if v is not None]
    if b1 and b2:
        joint_entries.extend(_ev_gen_joint_totals_dicts(b1, b2, "Total Barões", lambda a: [0.5, 1.5], "Partidas caóticas e longas = múltiplos Nashors roubados/trocados.", m1_b, m2_b))

    # Duration
    all_dur = [v for v in s1.get("duration_history", []) + s2.get("duration_history", []) if v]
    if all_dur:
        m_avg_dur = (m1_dur + m2_dur) / 2
        adj_all_dur = [v * m_avg_dur for v in all_dur]
        st_dur = calc_stats(all_dur)
        adj_dur_avg = sum(adj_all_dur) / len(adj_all_dur) if adj_all_dur else 0
        has_draft = m_avg_dur != 1.0
        for dl in [28.5, 31.5, 34.5]:
            prob_do, cnt = _rate_prob(adj_all_dur, lambda v, l=dl: v > l)
            if prob_do is not None and prob_do > 5:
                e = make_bet_entry(
                    "Partida", "Over Duração", f"{dl}min", prob_do, cnt,
                    f"Dur. Média Histórica pura: {st_dur['avg']:.1f}min ➡️ <b>Projeção c/ Draft: {adj_dur_avg:.1f}min</b>.<br><br>"
                    f"Apostas conjuntas calculadas baseadas na união das durações projetadas de todas as partidas.",
                    has_draft=has_draft,
                    draft_mult=m_avg_dur if has_draft else None,
                )
                if e:
                    joint_entries.append(e)

    joint_market_keys = ["Total Kills", "Total Dragões", "Total Torres", "Total Barões", "Over Duração"]
    joint_markets = {}
    for mk in joint_market_keys:
        group = [e for e in joint_entries if e and e["market"] == mk]
        if group:
            joint_markets[mk] = group

    joint_card = {"team": f"⚔️ {t1} vs {t2} (Estimativas de Jogo)", "color": "#f59e0b", "markets": joint_markets}

    return {"t1_card": t1_card, "t2_card": t2_card, "joint_card": joint_card}



def build_series_section(s1_series, s2_series, t1, t2):
    """Returns SeriesSection dict with insights per game number."""
    comments = []
    
    # Analisa tendências de abates no Mapa 5 (pico de emoção/decisão)
    t1_g5 = next((x for x in s1_series if x['game'] == 5), None)
    t2_g5 = next((x for x in s2_series if x['game'] == 5), None)
    
    if t1_g5 and t2_g5:
        # Soma das médias de abates no jogo 5
        g5_kills = t1_g5['avg_kills'] + t2_g5['avg_kills']
        
        # Média geral de todos os jogos para comparação
        def calc_overall_kills(series):
            total_k = sum(x['avg_kills'] * x['matches'] for x in series)
            total_m = sum(x['matches'] for x in series)
            return total_k / total_m if total_m > 0 else 0
            
        overall_k1 = calc_overall_kills(s1_series)
        overall_k2 = calc_overall_kills(s2_series)
        overall_total_k = overall_k1 + overall_k2
        
        if overall_total_k > 0:
            diff_pct = ((g5_kills / overall_total_k) - 1) * 100
            if diff_pct > 10:
                comments.append(f"🔥 <b>Tendência de MAPA 5:</b> O quinto jogo desta série tende a ser <b>{diff_pct:.1f}%</b> mais sangrento ({g5_kills:.1f} abates) que a média geral ({overall_total_k:.1f}). Ótimo para <b>Over Kills</b>.")
            elif diff_pct < -10:
                comments.append(f"🧊 <b>Tendência de MAPA 5:</b> O jogo decisivo tende a ser <b>{abs(diff_pct):.1f}%</b> mais passivo ({g5_kills:.1f} abates) que a média geral ({overall_total_k:.1f}). Times jogam com mais medo de errar.")

    # Tendência de duração no Mapa 1 (estatística comum)
    t1_g1 = next((x for x in s1_series if x['game'] == 1), None)
    t2_g1 = next((x for x in s2_series if x['game'] == 1), None)
    if t1_g1 and t2_g1:
        avg_dur_g1 = (t1_g1['avg_duration_min'] + t2_g1['avg_duration_min']) / 2
        if avg_dur_g1 > 35:
            comments.append(f"⏳ <b>Mapa 1 Longo:</b> As partidas de abertura tendem a ser extensas ({avg_dur_g1:.1f} min).")

    return {
        "t1_series": s1_series,
        "t2_series": s2_series,
        "explain_text": (
            "Análise de performance por <b>Número do Mapa</b>. Jogos decisivos (Mapa 5) ou de abertura (Mapa 1) "
            "frequentemente apresentam desvios estatísticos em relação à média do time devido à pressão ou estratégias específicas."
        ),
        "comments": comments
    }


def build_side_performance_section(side_data1, side_data2):
    """Calcula win rate por lado para ambos os times."""
    def process_data(rows):
        entries = []
        # Normaliza Lado para Capitalized
        for r in rows:
            s = r['side'].capitalize()
            wr = (r['wins'] / r['games'] * 100) if r['games'] > 0 else 0
            entries.append({
                "side": s,
                "games": r['games'],
                "wins": r['wins'],
                "win_rate": wr
            })
        return entries
        
    return {
        "t1": process_data(side_data1),
        "t2": process_data(side_data2)
    }

def build_league_context_section(league_context, league_name):
    """Constrói a seção de baseline da liga."""
    if not league_context:
        return None
        
    insights = []
    # Kills
    if league_context['avg_total_kills'] > 32:
        insights.append(f"🩸 <b>Liga Sangrenta:</b> A {league_name} tem uma média de {league_context['avg_total_kills']:.1f} abates, favorecendo mercados de <b>Over</b>.")
    elif league_context['avg_total_kills'] < 26:
        insights.append(f"🛡️ <b>Liga Conservadora:</b> Média de abates baixa ({league_context['avg_total_kills']:.1f}), favorecendo <b>Under</b>.")
        
    # Side Bias
    blue_wr = league_context['blue_win_rate']
    if blue_wr > 58:
        insights.append(f"🔵 <b>Viés de BLUE SIDE:</b> O lado azul vence {blue_wr:.1f}% das vezes nesta liga.")
    elif blue_wr < 42:
        insights.append(f"🔴 <b>Viés de RED SIDE:</b> O lado vermelho domina com {(100-blue_wr):.1f}% de WR.")
        
    return {
        "league": league_name,
        "avg_total_kills": league_context['avg_total_kills'],
        "blue_win_rate": blue_wr,
        "avg_duration": league_context['avg_duration'],
        "total_games_analyzed": league_context['total_games'],
        "insights": insights
    }


# ============================================================================
# Main Orchestrator
# ============================================================================

def generate_analytics_json(team1, team2, patches=None, champs_t1=None, champs_t2=None):
    """
    Replaces generate_charts(). Returns a structured dict matching AnalyticsResponse.
    All computation logic is preserved; only the output format changes.
    """
    from .data_provider import (
        get_team_stats,
        get_gold_team_stats,
        get_global_baseline_stats,
        get_platinum_champion_stats,
        get_series_stats,
        get_side_stats,
        get_league_context,
        get_objective_win_correlations,
    )

    stats1 = get_team_stats(team1, patches)
    stats2 = get_team_stats(team2, patches)

    if not stats1 or not stats2:
        return None

    gold_t1 = get_gold_team_stats(team1, patches)
    gold_t2 = get_gold_team_stats(team2, patches)

    s1_series = get_series_stats(team1, patches)
    s2_series = get_series_stats(team2, patches)

    s1_side = get_side_stats(team1, patches)
    s2_side = get_side_stats(team2, patches)

    # Contexto de liga (usando a liga do time 1 como referência)
    league_name = stats1.get("league", "Unknown")
    l_context = get_league_context(league_name)

    obj_corrs = get_objective_win_correlations(patches)

    # Platinum layer (same as renderer.py)
    plat1, plat2 = {}, {}
    if champs_t1:
        for role, champ in champs_t1.items():
            if champ:
                plat1[champ] = get_platinum_champion_stats(team1, champ)
    if champs_t2:
        for role, champ in champs_t2.items():
            if champ:
                plat2[champ] = get_platinum_champion_stats(team2, champ)

    global_baseline = get_global_baseline_stats(patches)

    def calc_multipliers(plat_data):
        if not plat_data or not global_baseline:
            return None
        factors = {
            "kills": [], "dragons": [], "towers": [], "barons": [], "duration": [],
            "firstblood": [], "firstdragon": [], "firstherald": [],
        }
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

    return {
        "meta": build_meta_section(stats1, stats2, team1, team2, patches),
        "educational": build_educational_section(),
        "egr": build_egr_section(stats1, stats2, team1, team2),
        "mlr": build_mlr_section(stats1, stats2, team1, team2),
        "radar": build_radar_section(stats1, stats2, team1, team2, gold_t1, gold_t2),
        "timeline": build_timeline_section(stats1, stats2, team1, team2, mult_t1, mult_t2),
        "economy": build_economy_section(stats1, stats2, team1, team2, gold_t1, gold_t2),
        "pace": build_pace_section(stats1, stats2, team1, team2),
        "winrate": build_winrate_section(stats1, stats2, team1, team2),
        "recent_form": build_recent_form_section(stats1, stats2, team1, team2),
        "kills_total": build_kills_total_section(stats1, stats2, team1, team2, mult_t1, mult_t2),
        "kills_per_team": build_kills_per_team_section(stats1, stats2, team1, team2, mult_t1, mult_t2),
        "handicap": build_handicap_section(stats1, stats2, team1, team2, mult_t1, mult_t2),
        "dragons": build_dragons_section(stats1, stats2, team1, team2, mult_t1, mult_t2),
        "towers": build_towers_section(stats1, stats2, team1, team2, mult_t1, mult_t2),
        "barons": build_barons_section(stats1, stats2, team1, team2, mult_t1, mult_t2),
        "duration": build_duration_section(stats1, stats2, team1, team2, mult_t1, mult_t2),
        "series": build_series_section(s1_series, s2_series, team1, team2),
        "side_performance": build_side_performance_section(s1_side, s2_side),
        "league_context": build_league_context_section(l_context, league_name),
        "objective_correlations": obj_corrs,
        "ev_finder": build_ev_finder_section(stats1, stats2, team1, team2, mult_t1, mult_t2),
    }
