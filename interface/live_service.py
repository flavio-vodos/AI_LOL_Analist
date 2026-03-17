"""
live_service.py
Módulo responsável por buscar e renderizar dados ao vivo das partidas profissionais
de League of Legends usando a API pública do LoL Esports.

API de referência: https://github.com/vickz84259/lolesports-api-docs
Inspirado em: https://github.com/Aureom/live-lol-esports
"""

import httpx
import random
import time
import os
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

load_dotenv("c:/Projetos/AI_LOL_Predictor/.env")

# ─── Constantes da API ────────────────────────────────────────────────────────
API_URL_PERSISTED = "https://esports-api.lolesports.com/persisted/gw"
API_URL_LIVE      = "https://feed.lolesports.com/livestats/v1"
API_KEY           = "0TvQnueqKa5mxJntVWt0w4LpLfEkrV1Ta8rQBb9Z"
CHAMPIONS_URL     = "https://ddragon.leagueoflegends.com/cdn/16.5.1/img/champion/"
ITEMS_URL         = "https://ddragon.leagueoflegends.com/cdn/16.5.1/img/item/"

HEADERS = {"x-api-key": API_KEY}

# ─── Imports de componentes de infraestrutura ────────────────────────────────
from interface.retry_system import RetrySystem, RetryConfig
from interface.cache_layer import CacheLayer
import logging


class _ContextFilter(logging.Filter):
    """Injeta campos match_id e game_id com valores padrão quando não fornecidos."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "match_id"):
            record.match_id = "-"
        if not hasattr(record, "game_id"):
            record.game_id = "-"
        return True


# ─── Configuração de logging estruturado ──────────────────────────────────────
# Silencia logs de bibliotecas externas
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("interface.retry_system").setLevel(logging.WARNING)

logging.basicConfig(
    level=logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(match_id)s/%(game_id)s] - %(message)s'
)
# Adiciona o filtro no root handler para que todos os loggers (uvicorn, urllib3, etc.)
# tenham os campos match_id e game_id injetados antes da formatação
_context_filter = _ContextFilter()
for _handler in logging.root.handlers:
    _handler.addFilter(_context_filter)

logger = logging.getLogger(__name__)
logger.addFilter(_context_filter)
logger.setLevel(logging.ERROR)

# ─── Inicialização de componentes globais ────────────────────────────────────
# Sistema de retry com backoff exponencial para requisições HTTP
_retry_system = RetrySystem(logger=logger)

# Cache em memória thread-safe com TTL de 5 segundos
_cache_layer = CacheLayer(logger=logger)


# ─── Helpers de tempo ─────────────────────────────────────────────────────────
def _get_cache_buster():
    """Gera um valor aleatório para evitar cache de rede."""
    return f"{int(time.time())}{random.randint(1000, 9999)}"


def get_iso_date_multiple_of_10() -> str:
    """Retorna ISO 8601 arredondado para múltiplos de 10s, subtraídos de 60s."""
    now = datetime.now(timezone.utc)
    remainder = now.second % 10
    rounded = now.replace(microsecond=0, second=now.second - remainder)
    # Reduzido de 180s para 60s para diminuir o atraso em relação ao tempo real.
    # Se houver erro 400, o RetrySystem remove o parâmetro e pega o frame mais recente.
    adjusted = rounded - timedelta(seconds=60)
    return adjusted.strftime("%Y-%m-%dT%H:%M:%SZ")


# ─── Funções de acesso à API ──────────────────────────────────────────────────
async def get_live_games() -> list:
    """Retorna lista de jogos em andamento com metadados dos times."""
    try:
        # Busca schedule de hoje como referência caso faltem dados no getLive
        today_sched = await get_schedule_today()
        
        data = await _retry_system.async_fetch_with_retry(
            url=f"{API_URL_PERSISTED}/getLive",
            params={"hl": "pt-BR"},
            headers=HEADERS,
            timeout=10,
        )
        if not data: return []
        events = (data.get("data", {}) if "data" in data else data).get("schedule", {}).get("events", [])
        result = []
        
        # Manter controle de quais match_ids do schedule já foram usados para evitar colisões
        used_schedule_match_ids = set()

        for ev in events:
            # 1. Filtro estrito de estado do evento
            if ev.get("state") == "completed":
                continue

            match = ev.get("match")
            match_id = match.get("id") if match else None
            
            # Se a partida em si já está marcada como finalizada, descartamos do Ao Vivo
            if match and match.get("state") == "completed":
                if match_id: used_schedule_match_ids.add(match_id)
                continue

            # 2. Validação por placar (Score cleanup)
            # Se um time já ganhou a maioria dos jogos (ex: 2 em BO3), a série acabou
            if match:
                strategy = match.get("strategy", {})
                win_threshold = 2 if strategy.get("count") == 3 else 1
                teams_data = match.get("teams", [])
                
                # Se algum time já atingiu as vitórias necessárias, a série acabou na prática
                if any(t.get("result", {}).get("gameWins", 0) >= win_threshold for t in teams_data):
                    if match_id: used_schedule_match_ids.add(match_id)
                    continue

            games = match.get("games", []) if match else []
            # Se todos os games da série já terminaram, a série acabou. Descartamos do Ao Vivo.
            if games and all(g.get("state") == "completed" for g in games):
                if match_id: used_schedule_match_ids.add(match_id)
                continue

            # Tenta pegar times do match ou resolver do schedule
            teams = match.get("teams", []) if match else []
            league_data = ev.get("league", {})
            league_name = league_data.get("name", "Desconhecido")
            
            # Fallback de ID e Times
            found_in_sched = None
            for s in today_sched:
                if s["match_id"] == match_id:
                    found_in_sched = s
                    break
            
            if not found_in_sched and match and match.get("teams"):
                live_teams = match.get("teams", [])
                if len(live_teams) >= 2:
                    b_c = live_teams[0].get("code", "").upper()
                    r_c = live_teams[1].get("code", "").upper()
                    for s in today_sched:
                        if s["match_id"] in used_schedule_match_ids: continue
                        sb = (s["team_blue"] or {}).get("code", "").upper()
                        sr = (s["team_red"] or {}).get("code", "").upper()
                        if (b_c == sb and r_c == sr) or (b_c == sr and r_c == sb):
                            found_in_sched = s
                            break

            if found_in_sched:
                match_id = found_in_sched["match_id"]
                used_schedule_match_ids.add(match_id)
                if len(teams) < 2:
                    teams = [found_in_sched["team_blue"], found_in_sched["team_red"]]
                    league_name = found_in_sched["league"]
            elif match_id:
                used_schedule_match_ids.add(match_id)

            if len(teams) < 2: continue

            game_number = 1
            for g in games:
                if g.get("state") == "inProgress":
                    game_number = g.get("number", 1)
                    break
            else:
                comp = sum(1 for g in games if g.get("state") == "completed")
                game_number = min(comp + 1, len(games)) if games else 1
            # gameId = matchId + game.number (convenção da Riot, igual ao Aureon)
            game_id = str(int(match_id) + game_number) if match_id else "unknown"

            result.append({
                "match_id":    match_id,
                "game_id":     game_id,
                "game_number": game_number,
                "league":      league_name,
                "team_blue":   teams[0],
                "team_red":    teams[1],
            })

        # --- FALLBACK AGRESSIVO (TEMPORAL) ---
        now = datetime.now(timezone.utc)
        for s in today_sched:
            if s["match_id"] in used_schedule_match_ids:
                continue
            
            # Se no schedule já diz que acabou, ignora
            if s["state"] == "completed":
                continue
            
            # Tenta converter startTime do schedule
            try:
                # Ex: 2026-03-12T20:00:00Z
                start_dt = datetime.strptime(s["start_time"], "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
                
                # Se começou a menos de 4 horas ou começa em 10 minutos
                if start_dt <= now + timedelta(minutes=10) and start_dt >= now - timedelta(hours=4):
                    # Validação final por placar no fallback:
                    # Se o schedule trouxer placar final (mesmo marcando unstarted ou inProgress), ignora
                    str_count = s.get("strategy", {}).get("count", 3)
                    win_threshold = 2 if str_count == 3 else 1
                    t1_wins = s["team_blue"].get("result", {}).get("gameWins", 0)
                    t2_wins = s["team_red"].get("result", {}).get("gameWins", 0)
                    
                    if t1_wins >= win_threshold or t2_wins >= win_threshold:
                        continue

                    logger.info(
                        f"Fallback de schedule acionado para match_id={s['match_id']} "
                        f"(start_time={s['start_time']})",
                        extra={"match_id": s["match_id"], "game_id": "-"}
                    )
                    result.append({
                        "match_id":    s["match_id"],
                        "game_id":     "unknown",
                        "game_number": 1,
                        "league":      s["league"],
                        "team_blue":   s["team_blue"],
                        "team_red":    s["team_red"],
                        "is_fallback": True
                    })
                    used_schedule_match_ids.add(s["match_id"])
            except:
                if s["state"] == "inProgress":
                    result.append({
                        "match_id":    s["match_id"],
                        "game_id":     "unknown",
                        "game_number": 1,
                        "league":      s["league"],
                        "team_blue":   s["team_blue"],
                        "team_red":    s["team_red"],
                    })
                    used_schedule_match_ids.add(s["match_id"])

        return result
    except Exception as e:
        logger.error(f"Erro ao buscar partidas ao vivo: {e}", exc_info=True)
        return []

async def get_schedule_today() -> list:
    """Retorna lista de todas as partidas agendadas para o dia de hoje (UTC)."""
    try:
        data = await _retry_system.async_fetch_with_retry(
            url=f"{API_URL_PERSISTED}/getSchedule",
            params={"hl": "pt-BR"},
            headers=HEADERS,
            timeout=10,
        )
        if not data: return []
        events = (data.get("data", {}) if "data" in data else data).get("schedule", {}).get("events", [])
        
        today = datetime.now(timezone.utc).date()
        result = []
        
        for ev in events:
            # Filtra apenas eventos de partidas (ignora showmatches sem times, etc)
            if not ev.get("match"):
                continue
            match = ev["match"]
            teams = match.get("teams", [])
            if len(teams) < 2:
                continue
            
            # Formato de data: "2024-03-22T17:00:00Z"
            start_time_str = ev.get("startTime", "")
            if not start_time_str:
                continue
                
            try:
                # Extrair YYYY-MM-DD
                event_date_str = start_time_str.split("T")[0]
                event_date = datetime.strptime(event_date_str, "%Y-%m-%d").date()
                if event_date != today:
                    continue
            except Exception:
                continue
            
            state = ev.get("state", "unstarted")
            
            result.append({
                "match_id":    match.get("id", ""),
                "state":       state,
                "league":      ev.get("league", {}).get("name", ""),
                "team_blue":   teams[0],
                "team_red":    teams[1],
                "start_time":  start_time_str,
                "strategy":    match.get("strategy", {}),
            })
            
        return result
    except Exception as e:
        logger.error(f"Erro ao buscar schedule de hoje: {e}", exc_info=True)
        return []


async def get_game_window(game_id: str):
    """Retorna o último frame de window (stats de time e jogadores) com cache e retry."""
    cache_key = f"window_{game_id}"
    cached = _cache_layer.get(cache_key)
    if cached:
        return cached

    # 1. Fetch with retry (Cache removido para live telemetry)
    try:
        date = get_iso_date_multiple_of_10()
        
        # Use RetrySystem.async_fetch_with_retry
        data = await _retry_system.async_fetch_with_retry(
            url=f"{API_URL_LIVE}/window/{game_id}",
            params={"hl": "pt-BR", "startingTime": date, "_": _get_cache_buster()},
            headers=HEADERS,
            timeout=10,
            retry_without_param="startingTime"  # Remove startingTime on 400 error
        )
        
        if not data:
            logger.warning(f"Falha ao buscar window {game_id} após todas as tentativas", extra={"game_id": game_id})
            return None
        
        # 3. Process response
        frames = data.get("frames", [])
        if not frames:
            logger.debug(f"Nenhum frame disponível para window {game_id}", extra={"game_id": game_id})
            return None
        
        result = {"frame": frames[-1], "metadata": data.get("gameMetadata")}
        _cache_layer.set(cache_key, result, ttl_seconds=1) # Set TTL to 1 second for live telemetry
        return result
        
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar window {game_id}: {e}", exc_info=True, extra={"game_id": game_id})
        return None


async def get_game_details(game_id: str, timestamp: str = None):
    """Retorna o último frame de details (items dos jogadores) com cache e retry."""
    cache_key = f"details_{game_id}_{timestamp}" if timestamp else f"details_{game_id}"
    cached = _cache_layer.get(cache_key)
    if cached:
        return cached

    # 1. Fetch with retry (Cache removido para live telemetry)
    try:
        params = {"hl": "pt-BR", "_": _get_cache_buster()}
        if timestamp:
            params["startingTime"] = timestamp
        
        # Use RetrySystem.async_fetch_with_retry
        data = await _retry_system.async_fetch_with_retry(
            url=f"{API_URL_LIVE}/details/{game_id}",
            params=params,
            headers=HEADERS,
            timeout=10,
            retry_without_param="startingTime"  # Remove startingTime on 400 error
        )
        
        if not data:
            logger.warning(f"Falha ao buscar details {game_id} após todas as tentativas", extra={"game_id": game_id})
            return None
        
        # 3. Process response
        frames = data.get("frames", [])
        
        # Fallback: Se retornou sucesso mas sem frames (comum se o startingTime for futuro), tenta sem startingTime
        if not frames and timestamp:
            logger.debug(f"Details {game_id} retornou vazio para timestamp {timestamp}, tentando sem startingTime.", extra={"game_id": game_id})
            data = await _retry_system.async_fetch_with_retry(
                url=f"{API_URL_LIVE}/details/{game_id}",
                params={"hl": "pt-BR", "_": _get_cache_buster()},
                headers=HEADERS,
                timeout=10
            )
            if data:
                frames = data.get("frames", [])

        if not frames:
            logger.debug(f"Nenhum frame disponível para details {game_id}", extra={"game_id": game_id})
            return None
        
        result = frames[-1]
        _cache_layer.set(cache_key, result, ttl_seconds=1) # Set TTL to 1 second for live telemetry
        return result
        
    except Exception as e:
        logger.error(f"Erro inesperado ao buscar details {game_id}: {e}", exc_info=True, extra=_ctx)
        return None


# ─── Helpers de formatação ────────────────────────────────────────────────────
def _fmt_gold(value: int) -> str:
    """Formata ouro com ponto como separador de milhar: 67510 → '67.510'"""
    return "{:,}".format(value).replace(",", ".")


def _gold_pct(blue: int, red: int):
    total = blue + red
    if total == 0:
        return 50.0, 50.0
    return round(blue / total * 100, 1), round(red / total * 100, 1)


_DRAGON_EMOJIS = {
    "ocean":    "🌊", "infernal": "🔥", "mountain": "🗻",
    "cloud":    "🌬️", "elder":    "🐲", "chemtech":  "☣️",
    "hextech":  "⚡",
}


def _dragon_icons(dragons: list) -> str:
    # Mapeamento para tooltips
    _DRAGON_NAMES = {
        "ocean": "Dragão do Oceano", "infernal": "Dragão Infernal", "mountain": "Dragão das Montanhas",
        "cloud": "Dragão das Nuvens", "elder": "Dragão Ancião", "chemtech": "Dragão Quimtec",
        "hextech": "Dragão Hextec"
    }
    html = []
    for d in dragons:
        d_lower = d.lower()
        emoji = _DRAGON_EMOJIS.get(d_lower, "🐉")
        name = _DRAGON_NAMES.get(d_lower, d)
        html.append(f'<span title="{name}" style="cursor:help;margin:0 2px;">{emoji}</span>')
    return " ".join(html)


def _health_bar(current: int, max_hp: int) -> str:
    pct = round(current / max_hp * 100) if max_hp > 0 else 0
    if pct > 60:
        bar_color = "#4ade80"
    elif pct > 30:
        bar_color = "#facc15"
    else:
        bar_color = "#f87171"
    cur_str = _fmt_gold(current)
    max_str = _fmt_gold(max_hp)
    return (
        '<div title="Vida: ' + cur_str + ' / ' + max_str + '" style="background:#1e293b;border-radius:4px;height:16px;width:100%;'
        'position:relative;overflow:hidden;border:1px solid #334155;cursor:help;">'
        '<div style="width:' + str(pct) + '%;height:100%;background:' + bar_color + ';'
        'border-radius:3px;transition:width 0.5s;"></div>'
        '<span style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);'
        'font-size:9px;color:#fff;white-space:nowrap;pointer-events:none;">' + cur_str + '/' + max_str + '</span>'
        '</div>'
    )


def _champ_img(champion_id: str) -> str:
    # ddragon usa nomes. Ex: K'Sante -> KSante, LeBlanc -> Leblanc (às vezes)
    # RFC: LoL Esports API retorna nomes como 'Caitlyn', 'MonkeyKing'
    name = champion_id.replace("'", "").replace(" ", "").replace(".", "")
    if name == "KogMaw": name = "KogMaw" # Já está ok
    # Fallback para o ícone padrão caso a imagem falhe
    return (
        '<img src="' + CHAMPIONS_URL + name + '.png" '
        'title="Campeão: ' + champion_id + '" '
        'style="width:30px;height:30px;border-radius:50%;border:1px solid #334155;cursor:help;" '
        'onerror="this.src=\'https://ddragon.leagueoflegends.com/cdn/16.5.1/img/profileicon/29.png\'" />'
    )


def _item_imgs(item_ids: list) -> str:
    parts = []
    for item_id in item_ids:
        if item_id and item_id != 0:
            parts.append(
                '<img src="' + ITEMS_URL + str(item_id) + '.png" '
                'style="width:22px;height:22px;border-radius:3px;margin:1px;border:1px solid #1e293b;" '
                'title="Item ID: ' + str(item_id) + '" '
                'onerror="this.style.display=\'none\'" />'
            )
    return "".join(parts)


def _team_logo(team: dict) -> str:
    img_url = team.get("image", "")
    if img_url:
        return (
            '<img src="' + img_url + '" '
            'style="width:44px;height:44px;object-fit:contain;border-radius:6px;" '
            'onerror="this.style.display=\'none\'" />'
        )
    return ""


# ─── Renderização da tabela de jogadores ─────────────────────────────────────
def _render_player_rows(participants: list, meta_parts: list,
                         detail_parts: list, opp_parts: list) -> str:
    rows = []
    for i, player in enumerate(participants):
        if i >= len(meta_parts):
            break
        meta      = meta_parts[i]
        champ_id  = meta.get("championId", "")
        summoner  = meta.get("summonerName", meta.get("esportsPlayerId", "—"))
        level     = player.get("level", 1)
        cur_hp    = player.get("currentHealth", 0)
        max_hp    = player.get("maxHealth", 1)
        cs        = player.get("creepScore", 0)
        kills     = player.get("kills", 0)
        deaths    = player.get("deaths", 0)
        assists   = player.get("assists", 0)
        gold      = player.get("totalGold", 0)

        opp_gold  = opp_parts[i].get("totalGold", 0) if i < len(opp_parts) else 0
        gdiff     = gold - opp_gold
        gdiff_str = ("+" if gdiff >= 0 else "") + _fmt_gold(gdiff)
        gdiff_col = "#4ade80" if gdiff > 0 else ("#f87171" if gdiff < 0 else "#94a3b8")

        items_html = ""
        if i < len(detail_parts):
            dp = detail_parts[i]
            # No Riot Live Stats, itens vem numa lista 'items'
            raw_items = dp.get("items", [])
            if not isinstance(raw_items, list): raw_items = []
            # Mantém 7 slots para o layout (6 itens + 1 trinket)
            item_ids = raw_items + [0] * (7 - len(raw_items))
            items_html = _item_imgs(item_ids)

        bar  = _health_bar(cur_hp, max_hp)
        cimg = _champ_img(champ_id)

        row = (
            '<tr style="border-bottom:1px solid #0f172a;">'
            '<td style="padding:6px 8px;">'
            '<div style="display:flex;align-items:center;gap:8px;">'
            '<div style="position:relative;display:inline-block;">'
            + cimg +
            '<span style="position:absolute;bottom:-3px;right:-3px;background:#0f172a;'
            'color:#94a3b8;font-size:9px;border-radius:9px;padding:0 3px;'
            'border:1px solid #334155;">' + str(level) + '</span>'
            '</div>'
            '<div style="display:flex;flex-direction:column;line-height:1.3;">'
            '<span style="font-weight:600;font-size:12px;color:#e2e8f0;">' + champ_id + '</span>'
            '<span style="font-size:10px;color:#64748b;">' + summoner + '</span>'
            '</div></div></td>'
            '<td style="padding:6px 8px;min-width:130px;">' + bar + '</td>'
            '<td style="padding:4px 8px;">' + items_html + '</td>'
            '<td style="padding:4px 8px;text-align:center;color:#cbd5e1;font-size:12px;">' + str(cs) + '</td>'
            '<td style="padding:4px 8px;text-align:center;color:#4ade80;font-size:13px;font-weight:700;">' + str(kills) + '</td>'
            '<td style="padding:4px 8px;text-align:center;color:#f87171;font-size:13px;font-weight:700;">' + str(deaths) + '</td>'
            '<td style="padding:4px 8px;text-align:center;color:#60a5fa;font-size:13px;font-weight:700;">' + str(assists) + '</td>'
            '<td style="padding:4px 8px;text-align:center;color:#e2e8f0;font-size:12px;">' + _fmt_gold(gold) + '</td>'
            '<td style="padding:4px 8px;text-align:center;color:' + gdiff_col + ';font-size:12px;font-weight:600;">' + gdiff_str + '</td>'
            '</tr>'
        )
        rows.append(row)
    return "\n".join(rows)


def _render_team_table(team_name: str, participants: list, meta_parts: list,
                        detail_parts: list, opp_parts: list) -> str:
    rows = _render_player_rows(participants, meta_parts, detail_parts, opp_parts)
    return (
        '<table style="width:100%;border-collapse:collapse;margin-bottom:16px;">'
        '<thead>'
        '<tr style="background:#0a1628;color:#64748b;font-size:11px;text-transform:uppercase;">'
        '<th style="padding:8px 10px;text-align:left;width:180px;">' + team_name.upper() + '</th>'
        '<th style="padding:8px 10px;text-align:left;width:145px;">VIDA</th>'
        '<th style="padding:8px 10px;text-align:left;">ITEMS</th>'
        '<th style="padding:8px 10px;text-align:center;width:45px;" title="Creep Score (Tropas)">CS</th>'
        '<th style="padding:8px 10px;text-align:center;width:35px;" title="Abates">K</th>'
        '<th style="padding:8px 10px;text-align:center;width:35px;" title="Mortes">D</th>'
        '<th style="padding:8px 10px;text-align:center;width:35px;" title="Assistências">A</th>'
        '<th style="padding:8px 10px;text-align:center;width:80px;" title="Ouro Total">Ouro</th>'
        '<th style="padding:8px 10px;text-align:center;width:70px;" title="Vantagem de Ouro sobre oponente">+/-</th>'
        '</tr>'
        '</thead>'
        '<tbody style="background:#16213e;">'
        + rows +
        '</tbody>'
        '</table>'
    )


# ─── Renderizador principal ───────────────────────────────────────────────────
async def render_live_match(game_info: dict) -> str:
    """Busca os dados mais recentes e retorna HTML completo da view ao vivo."""
    game_id   = game_info["game_id"]
    team_blue = game_info["team_blue"]
    team_red  = game_info["team_red"]
    league    = game_info["league"]

    window_data  = await get_game_window(game_id)
    
    # Busca detalhes (itens) usando o timestamp exato do frame
    ts = None
    if window_data and window_data.get("frame"):
        ts = window_data["frame"].get("rfc460Timestamp")
    
    details_data = await get_game_details(game_id, timestamp=ts)

    if not window_data or not window_data.get("frame"):
        return (
            '<div style="color:#f87171;text-align:center;padding:40px;">'
            '⚠️ Dados da partida ainda não disponíveis. Aguarde e clique em Atualizar.'
            '</div>'
        )

    frame    = window_data["frame"]
    metadata = window_data.get("metadata") or {}

    blue_frame = frame.get("blueTeam", {})
    red_frame  = frame.get("redTeam", {})

    blue_parts = blue_frame.get("participants", [])
    red_parts  = red_frame.get("participants", [])

    blue_meta = (metadata.get("blueTeamMetadata") or {}).get("participantMetadata", [])
    red_meta  = (metadata.get("redTeamMetadata") or {}).get("participantMetadata", [])

    detail_blue = []
    detail_red  = []
    if details_data:
        # Tenta pegar participants direto (flat list de 10) ou agrupado por time
        all_parts = details_data.get("participants", [])
        if all_parts and len(all_parts) >= 10:
            detail_blue = all_parts[:5]
            detail_red  = all_parts[5:]
        else:
            detail_blue = (details_data.get("blueTeam") or {}).get("participants", [])
            detail_red  = (details_data.get("redTeam") or {}).get("participants", [])

    # Stats do time
    blue_gold   = blue_frame.get("totalGold", 0)
    red_gold    = red_frame.get("totalGold", 0)
    blue_pct, red_pct = _gold_pct(blue_gold, red_gold)
    blue_kills  = blue_frame.get("totalKills", 0)
    red_kills   = red_frame.get("totalKills", 0)
    blue_towers = blue_frame.get("towers", 0)
    red_towers  = red_frame.get("towers", 0)
    blue_barons = blue_frame.get("barons", 0)
    red_barons  = red_frame.get("barons", 0)
    blue_inhibs = blue_frame.get("inhibitors", 0)
    red_inhibs  = red_frame.get("inhibitors", 0)
    blue_dragons = blue_frame.get("dragons", [])
    red_dragons  = red_frame.get("dragons", [])

    blue_code  = team_blue.get("code", "???")
    red_code   = team_red.get("code", "???")
    blue_name  = team_blue.get("name", blue_code)
    red_name   = team_red.get("name", red_code)
    blue_logo  = _team_logo(team_blue)
    red_logo   = _team_logo(team_red)

    game_state    = frame.get("gameState", "inProgress")
    state_display = "AO VIVO" if game_state == "inProgress" else game_state.upper()
    state_color   = "#ef4444" if game_state == "inProgress" else "#facc15"

    blue_drag_str = _dragon_icons(blue_dragons) or "—"
    red_drag_str  = _dragon_icons(list(reversed(red_dragons))) or "—"

    blue_table = _render_team_table(blue_name, blue_parts, blue_meta, detail_blue, red_parts)
    red_table  = _render_team_table(red_name,  red_parts,  red_meta,  detail_red,  blue_parts)

    html = (
        '<div style="font-family:\'Inter\',system-ui,sans-serif;background:#0f172a;border-radius:12px;'
        'padding:20px;border:1px solid #334155;color:#e2e8f0;">'

        # Liga
        '<div style="text-align:center;margin-bottom:12px;">'
        '<span style="font-size:11px;color:#64748b;text-transform:uppercase;letter-spacing:1px;">'
        + league +
        '</span></div>'

        # Header VS
        '<div style="display:flex;align-items:center;justify-content:center;gap:20px;margin-bottom:16px;">'

        # Blue team
        '<div style="display:flex;align-items:center;gap:10px;flex:1;justify-content:flex-end;">'
        '<span style="font-size:18px;font-weight:800;color:#60a5fa;">' + blue_code + '</span>'
        + blue_logo +
        '</div>'

        # VS + status
        '<div style="text-align:center;min-width:110px;">'
        '<div style="font-size:22px;font-weight:900;color:#e2e8f0;">VS</div>'
        '<div style="background:' + state_color + ';color:#fff;font-size:10px;font-weight:700;'
        'border-radius:99px;padding:2px 10px;letter-spacing:1px;margin-top:4px;display:inline-block;">'
        + state_display + '</div>'
        '</div>'

        # Red team
        '<div style="display:flex;align-items:center;gap:10px;flex:1;justify-content:flex-start;">'
        + red_logo +
        '<span style="font-size:18px;font-weight:800;color:#f87171;">' + red_code + '</span>'
        '</div>'
        '</div>'  # /header

        # Stats dos times
        '<div style="display:flex;justify-content:space-between;align-items:center;'
        'background:#1e293b;border-radius:10px;padding:10px 20px;margin-bottom:10px;gap:10px;">'

        # Blue stats
        '<div style="display:flex;gap:14px;align-items:center;flex:1;justify-content:flex-start;">'
        '<span title="Inibidores" style="display:flex;align-items:center;gap:4px;font-size:13px;">🏛️ <b>' + str(blue_inhibs) + '</b></span>'
        '<span title="Barões"     style="display:flex;align-items:center;gap:4px;font-size:13px;">🐉 <b>' + str(blue_barons) + '</b></span>'
        '<span title="Torres"     style="display:flex;align-items:center;gap:4px;font-size:13px;">🗼 <b>' + str(blue_towers) + '</b></span>'
        '<span title="Ouro"       style="display:flex;align-items:center;gap:4px;font-size:13px;color:#facc15;">💰 <b>' + _fmt_gold(blue_gold) + '</b></span>'
        '<span title="Kills"      style="display:flex;align-items:center;gap:4px;font-size:13px;color:#4ade80;">⚔️ <b>' + str(blue_kills) + '</b></span>'
        '</div>'

        # Red stats
        '<div style="display:flex;gap:14px;align-items:center;flex:1;justify-content:flex-end;">'
        '<span title="Kills"      style="display:flex;align-items:center;gap:4px;font-size:13px;color:#f87171;">⚔️ <b>' + str(red_kills) + '</b></span>'
        '<span title="Ouro"       style="display:flex;align-items:center;gap:4px;font-size:13px;color:#facc15;">💰 <b>' + _fmt_gold(red_gold) + '</b></span>'
        '<span title="Torres"     style="display:flex;align-items:center;gap:4px;font-size:13px;">🗼 <b>' + str(red_towers) + '</b></span>'
        '<span title="Barões"     style="display:flex;align-items:center;gap:4px;font-size:13px;">🐉 <b>' + str(red_barons) + '</b></span>'
        '<span title="Inibidores" style="display:flex;align-items:center;gap:4px;font-size:13px;">🏛️ <b>' + str(red_inhibs) + '</b></span>'
        '</div>'
        '</div>'  # /stats dos times

        # Barra de ouro
        '<div style="display:flex;height:10px;border-radius:5px;overflow:hidden;margin-bottom:4px;">'
        '<div style="flex:' + str(blue_pct) + ';background:linear-gradient(90deg,#3b82f6,#60a5fa);transition:flex 1s;"></div>'
        '<div style="flex:' + str(red_pct) + ';background:linear-gradient(90deg,#f87171,#ef4444);transition:flex 1s;"></div>'
        '</div>'
        '<div style="display:flex;justify-content:space-between;font-size:10px;color:#64748b;margin-bottom:14px;">'
        '<span>' + str(blue_pct) + '%</span>'
        '<span>Distribuição de Ouro</span>'
        '<span>' + str(red_pct) + '%</span>'
        '</div>'

        # Dragões
        '<div style="display:flex;justify-content:space-between;margin-bottom:16px;padding:0 4px;">'
        '<div style="font-size:20px;">' + blue_drag_str + '</div>'
        '<div style="font-size:11px;color:#64748b;align-self:center;">DRAGÕES</div>'
        '<div style="font-size:20px;">' + red_drag_str + '</div>'
        '</div>'

        # Tabelas
        '<div style="background:#0a1628;border-radius:10px;padding:12px;border:1px solid #1e293b;">'
        + blue_table + red_table +
        '</div>'

        '<div style="text-align:center;margin-top:10px;font-size:10px;color:#334155;">'
        '🔄 Dados atualizados automaticamente a cada 10 segundos'
        '</div>'
        '</div>'
    )
    return html


def render_live_dashboard(live_games: list, today_games: list, pandascore_matches: list = None) -> str:
    """HTML em grid exibindo 'LIVE ESPORTS' e 'JOGOS DO DIA'."""
    
    # Se recebemos a lista da Pandascore, usaremos ela prioritariamente para construir os cards
    cards_data = pandascore_matches if pandascore_matches is not None else today_games
    
    def render_card(game, is_live=False):
        league   = game.get("league", "League")
        blue     = game.get("team_blue", {})
        red      = game.get("team_red", {})
        
        b_name   = blue.get("name", blue.get("code", "Team 1"))
        r_name   = red.get("name", red.get("code", "Team 2"))
        
        # Formatando as logos para caberem nos quadradinhos de 36px
        def _get_bg_img(tm):
            img = tm.get("image")
            if img:
                return f"background-image:url('{img}');background-size:contain;background-repeat:no-repeat;background-position:center;"
            return "background:#2d3748;" # fallback escuro
            
        b_img_style = _get_bg_img(blue)
        r_img_style = _get_bg_img(red)
        
        # Badge AO VIVO (opcionalmente adicionado ao layout do print, ou um glow)
        border_glow = "border: 1px solid #e53e3e; box-shadow: 0 0 10px rgba(229,62,62,0.3);" if is_live else "border: 1px solid transparent;"
        
        # A API Aureom e a ponte JS precisam do Acronym exacto.
        b_code = blue.get("code", "???")
        r_code = red.get("code", "???")
        
        # Label oculto que fará o match em 'render_live_by_choice'
        label = f"{league}: {b_code} vs {r_code} (Agendado)"
        if is_live:
            label = f"{league}: {b_code} vs {r_code} (Ao Vivo)"
            
        label_escaped = label.replace("'", "\\'")

        # HTML baseado estritamente no print fornecido
        card = (
            '<div onclick="if(window.selectMatch) window.selectMatch(\'' + label_escaped + '\')" '
            'style="cursor:pointer; background:#181A20; border-radius:8px; display:flex; flex-direction:column; '
            'align-items:center; padding:16px; ' + border_glow + ' '
            'transition:transform 0.2s, background 0.2s;" '
            'onmouseover="this.style.background=\'#1A202C\'" onmouseout="this.style.background=\'#181A20\'">'
            
            # Liga (Top Center)
            '<div style="font-size:13px; font-weight:600; color:#90CDF4; margin-bottom:16px;">' + league + '</div>'
            
            '<div style="display:flex; justify-content:center; align-items:center; width:100%; gap:24px; margin-bottom:12px;">'
            
            # Blue logo
            '<div style="width:40px; height:40px; border-radius:6px; background:#1E222D; display:flex; justify-content:center; align-items:center; overflow:hidden;">'
            '<div style="width:34px; height:34px; ' + b_img_style + '"></div>'
            '</div>'
            
            # VS text
            '<div style="font-size:20px; font-weight:600; color:#A0AEC0;">VS</div>'
            
            # Red logo
            '<div style="width:40px; height:40px; border-radius:6px; background:#1E222D; display:flex; justify-content:center; align-items:center; overflow:hidden;">'
            '<div style="width:34px; height:34px; ' + r_img_style + '"></div>'
            '</div>'
            
            '</div>' # closes row
            
            # Nomes dos Times (Bottom row)
            '<div style="display:flex; justify-content:space-between; width:100%; gap:10px; margin-top:4px;">'
            '<div style="flex:1; text-align:center; font-size:12px; color:#90CDF4; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">' + b_name + '</div>'
            '<div style="flex:1; text-align:center; font-size:12px; color:#90CDF4; font-weight:500; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">' + r_name + '</div>'
            '</div>'
            
            '</div>'
        )
        return card
        
        # O logo no game list é menor e as fontes são menores
        b_logo = b_logo.replace("width:44px;height:44px", "width:40px;height:40px")
        r_logo = r_logo.replace("width:44px;height:44px", "width:40px;height:40px")
        
        # Badge AO VIVO se estiver rolando
        live_badge = ""
        if is_live:
            live_badge = (
                '<div style="background:#ef4444; color:#fff; font-size:9px; font-weight:700; '
                'padding:2px 8px; border-radius:10px; margin-top:10px; letter-spacing:1px; text-transform:uppercase;">AO VIVO</div>'
            )

        # Rótulo para selecionar via bridge JS - DEVE SER IGUAL AO DO app.py
        b_code = blue.get("code", "???")
        r_code = red.get("code", "???")
        if is_live:
            game_number = game.get("game_number", 1)
            label = f"{league}: {b_code} vs {r_code} (Jogo {game_number})"
        else:
            label = f"{league}: {b_code} vs {r_code} (Agendado)"
        
        # Escapa aspas simples para não quebrar o JS
        label_escaped = label.replace("'", "\\'")

        card = (
            '<div onclick="if(window.selectMatch) window.selectMatch(\'' + label_escaped + '\')" '
            'style="cursor:pointer; background:#151e2e; border-radius:8px; display:flex; flex-direction:column; '
            'align-items:center; padding:15px; border:1px solid ' + ('#3b82f6' if is_live else '#1e293b') + '; '
            'box-shadow:0 4px 6px rgba(0,0,0,0.1); transition:transform 0.2s, background 0.2s, border-color 0.2s;" '
            'onmouseover="this.style.background=\'#1e293b\'" onmouseout="this.style.background=\'#151e2e\'">'
            '<div style="font-size:12px; font-weight:700; color:#94a3b8; margin-bottom:15px; letter-spacing:0.5px;">' + league + '</div>'
            '<div style="display:flex; justify-content:center; align-items:center; width:100%; gap:20px; margin-bottom:12px;">'
            '<div style="display:flex; flex-direction:column; align-items:center; flex:1; gap:8px;">'
            + b_logo +
            '<span style="font-size:11px; color:#cbd5e1; text-align:center; max-width:100px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="' + b_name + '">' + b_name + '</span>'
            '</div>'
            '<div style="font-size:24px; font-weight:900; color:#475569;">VS</div>'
            '<div style="display:flex; flex-direction:column; align-items:center; flex:1; gap:8px;">'
            + r_logo +
            '<span style="font-size:11px; color:#cbd5e1; text-align:center; max-width:100px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;" title="' + r_name + '">' + r_name + '</span>'
            '</div>'
            '</div>'
            + live_badge +
            '</div>'
        )
        return card

    styles = (
        '<style>'
        '.livedashboard-grid { display:grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; margin-bottom: 30px; }'
        '.livedashboard-title { color:#cbd5e1; font-size:18px; font-weight:700; text-align:center; margin: 30px 0 20px 0; text-transform:uppercase; letter-spacing: 1px; }'
        '.livedashboard-hr { border:0; height:1px; background:#334155; margin:30px 0; }'
        '</style>'
    )
    
    html_parts = [
        '<div style="font-family:\'Inter\',system-ui,sans-serif; background:#0f172a; border-radius:12px; padding:30px; border:1px solid #334155;">',
        styles,
        '<div style="display:flex; flex-direction:column; align-items:center; margin-bottom:30px;">',
        '<div style="background:#1e293b; padding:15px; border-radius:50%; margin-bottom:10px; font-size:24px;">🏆</div>',
        '<div style="font-size:16px; font-weight:600; color:#f8fafc;">Live Esports</div>',
        '</div>'
    ]
    
    # "LIVE ESPORTS" - partidas ao vivo
    has_live = False
    live_cards = []
    
    # "JOGOS DO DIA" - completados ou agendados
    day_cards = []
    
    for game in cards_data:
        # Se veio da Riot get_live_games ou é um state inProgress da Pandascore
        is_currently_live = False
        
        # Checa pela PandaScore
        if game.get("state") == "inProgress":
            is_currently_live = True
            
        # Ref-check via memória da Riot (Aureom)
        for g in live_games:
            b = g["team_blue"].get("code", "")
            r = g["team_red"].get("code", "")
            if (b == game.get("team_blue", {}).get("code") and r == game.get("team_red", {}).get("code")) or \
               (r == game.get("team_blue", {}).get("code") and b == game.get("team_red", {}).get("code")):
                is_currently_live = True
                
        if is_currently_live:
            has_live = True
            live_cards.append(render_card(game, is_live=True))
        else:
            day_cards.append(render_card(game, is_live=False))

    if has_live:
        html_parts.append('<div class="livedashboard-grid">')
        html_parts.extend(live_cards)
        html_parts.append('</div>')
    else:
        html_parts.append('<div style="text-align:center; padding:30px; color:#64748b; font-size:14px; background:#0a1628; border-radius:8px; border:1px solid #1e293b;">NENHUM JOGO AO VIVO NO MOMENTO</div>')

    html_parts.append('<hr class="livedashboard-hr" />')
    html_parts.append('<div class="livedashboard-title">TODOS OS JOGOS</div>')
    
    if day_cards:
        html_parts.append('<div class="livedashboard-grid">')
        html_parts.extend(day_cards)
        html_parts.append('</div>')
    else:
        html_parts.append('<div style="text-align:center; padding:30px; color:#64748b; font-size:14px; background:#0a1628; border-radius:8px; border:1px solid #1e293b;">NENHUM OUTRO JOGO ENCONTRADO PARA HOJE</div>')

    html_parts.append('</div>')

    # Adiciona script JS para a ponte do Gradio
    scripts = """
    <script>
        window.selectMatch = window.selectMatch || function(matchLabel) {
            let wrapper = document.getElementById('hidden_match_choice');
            if (wrapper) {
                let inputEl = wrapper.querySelector('textarea');
                if (!inputEl) inputEl = wrapper.querySelector('input');
                if (inputEl) {
                    inputEl.value = matchLabel;
                    inputEl.dispatchEvent(new Event('input', { bubbles: true }));
                    setTimeout(function() {
                        let btn = document.getElementById('hidden_match_btn');
                        if (btn) btn.click();
                    }, 50);
                }
            } else {
                console.log("Variável escondida para seleção de partida não encontrada no DOM.");
            }
        };
    </script>
    """
    html_parts.append(scripts)
    
    return "".join(html_parts)

async def _render_scheduled_live_match(s: dict) -> str:
    """Busca o gameId real usando getEventDetails e tenta renderizar a partida."""
    match_id = s.get("match_id")
    if not match_id:
        return (
            '<div style="color:#f87171;text-align:center;padding:40px;">'
            '⚠️ ID da partida não encontrado.'
            '</div>'
        )
        
    try:
        data = await _retry_system.async_fetch_with_retry(
            url=f"{API_URL_PERSISTED}/getEventDetails",
            params={"hl": "pt-BR", "id": match_id},
            headers=HEADERS,
            timeout=10,
        )
        if not data: return "⚠️ Erro ao buscar detalhes"
        event_data = (data.get("data") or data).get("event", {})
        games = event_data.get("match", {}).get("games", [])
        
        game_id = None
        game_number = 1
        
        # 1. Tenta pegar o último jogo que já foi completed para mostrar o resultado lado-a-lado
        for g in reversed(games):
            if g.get("state") == "completed":
                game_id = g.get("id")
                game_number = g.get("number", 1)
                break
                
        # 2. Se não houver jogo completado, tenta achar o jogo em andamento/unstarted
        if not game_id:
            for g in games:
                if g.get("state") in ("inProgress", "unstarted"):
                    game_id = g.get("id")
                    game_number = g.get("number", 1)
                    break
                
        if not game_id:
             game_id = games[0].get("id") if games else "unknown"
             
        # Mock up a dict like the one get_live_games returns
        mock_game = {
            "match_id": match_id,
            "game_id": game_id,
            "game_number": game_number,
            "league": s["league"],
            "team_blue": s["team_blue"],
            "team_red": s["team_red"],
        }
        return await render_live_match(mock_game)
    except Exception as e:
        logger.error(f"Erro ao buscar detalhes da partida agendada {match_id}: {e}", exc_info=True,
                     extra={"match_id": match_id})
        return (
            '<div style="color:#f87171;text-align:center;padding:40px;">'
            '⚠️ Erro ao puxar dados ao vivo desta partida agendada. A partida pode não ter iniciado.'
            '</div>'
        )

# ─── Helpers para o app.py ────────────────────────────────────────────────────
async def render_live_by_choice(choice: str, live_cache: list, today_cache: list = None) -> str:
    """Dado o label selecionado, devolve o HTML da partida correspondente ou do dashboard."""
    if not choice or choice == "🌐 Visão Geral (Dashboard)":
        return render_live_dashboard(live_cache, today_cache or [])
        
    import re
    m = re.search(r':\s*(.+?)\s*vs\s*(.+?)\s*\(', choice)
    if not m:
        return render_live_dashboard(live_cache, today_cache or [])
        
    b_target = m.group(1).strip()
    r_target = m.group(2).strip()
        
    # 1. Tenta achar nos jogos ao vivo (Riot)
    for g in live_cache:
        b = g.get("team_blue", {}).get("code", "?")
        r = g.get("team_red", {}).get("code", "?")
        if (b == b_target and r == r_target) or (b == r_target and r == b_target):
            if g.get("game_id") == "unknown":
                return await _render_scheduled_live_match(g)
            return await render_live_match(g)
            
    # 2. Tenta puxar dos jogos agendados que não aparecem no feed live
    for s in (today_cache or []):
        b = s.get("team_blue", {}).get("code", "?")
        r = s.get("team_red", {}).get("code", "?")
        if (b == b_target and r == r_target) or (b == r_target and r == b_target):
            return await _render_scheduled_live_match(s)
            
    # Fallback final
    return render_live_dashboard(live_cache, today_cache or [])


# ─── Gerenciamento de Estado de Partidas ─────────────────────────────────────

def is_match_finished(game_data: dict) -> bool:
    """
    Verifica se uma partida terminou baseado nos dados do frame.

    Detecta finalizacao por tres criterios:
    1. gameState == "finished" no frame atual
    2. Todos os games da serie com estado "completed"
    3. Um time atingiu o numero de vitorias necessario (2 em BO3, 3 em BO5)

    Args:
        game_data: Dicionario com dados do frame (retorno de get_game_window)
                   ou dados de match (com campo "games" e "teams")

    Returns:
        True se a partida terminou, False caso contrario
    """
    if not game_data:
        return False

    # Criterio 1: gameState == "finished" no frame
    frame = game_data.get("frame", {})
    if frame.get("gameState") == "finished":
        return True

    # Criterio 2: Todos os games com estado "completed"
    games = game_data.get("games", [])
    if games and all(g.get("state") == "completed" for g in games):
        return True

    # Criterio 3: Um time atingiu vitorias necessarias
    strategy = game_data.get("strategy", {})
    series_count = strategy.get("count", 3)
    win_threshold = 2 if series_count == 3 else (3 if series_count == 5 else 1)

    teams = game_data.get("teams", [])
    if teams and any(
        t.get("result", {}).get("gameWins", 0) >= win_threshold
        for t in teams
    ):
        return True

    return False
async def get_match_data_by_id(match_id: str) -> dict | None:
    """
    Busca dados completos de uma partida pelo match_id usando getEventDetails.
    Funciona para partidas ao vivo, agendadas e finalizadas.
    """
    # Sempre passa por _fetch_match_from_event_details para ter state correto
    # Primeiro tenta enriquecer com dados do schedule (times, liga)
    try:
        today = await get_schedule_today()
        for s in today:
            if s.get("match_id") == match_id:
                return await _fetch_match_from_event_details(s)
    except Exception:
        pass
    
    # Fallback: busca direto no getEventDetails sem dados do schedule
    try:
        dummy = {"match_id": match_id, "league": "", "team_blue": {}, "team_red": {}}
        return await _fetch_match_from_event_details(dummy)
    except Exception:
        return None


async def _fetch_match_from_event_details(s: dict) -> dict | None:
    """Busca dados de uma partida via getEventDetails e enriquece com window data."""
    match_id = s.get("match_id")
    if not match_id:
        return None

    data = await _retry_system.async_fetch_with_retry(
        url=f"{API_URL_PERSISTED}/getEventDetails",
        params={"hl": "pt-BR", "id": match_id},
        headers=HEADERS,
        timeout=10,
    )
    if not data: return None
    event_data = (data.get("data") or data).get("event", {})
    match_data = event_data.get("match", {})
    games = match_data.get("games", [])
    teams = match_data.get("teams", [])
    inner_data = data.get("data") or data
    league_name = s.get("league") or inner_data.get("league", {}).get("name", "")

    # Se não há games, o match_id provavelmente não é da Riot API
    if not games and not teams:
        return None

    # Resolve times do evento se não vieram no schedule
    team_blue = s.get("team_blue") or (teams[0] if len(teams) > 0 else {})
    team_red = s.get("team_red") or (teams[1] if len(teams) > 1 else {})

    match_state = match_data.get("state", s.get("state", "unknown"))

    # Escolhe o game ativo: inProgress, ou próximo após completed
    game_id = "unknown"
    game_number = 1
    
    current_game = None
    for g in games:
        if g.get("state") == "inProgress":
            current_game = g
            break
    
    if not current_game:
        # Se nenhum em progresso, pega o próximo após os completados
        comp_count = sum(1 for g in games if g.get("state") == "completed")
        idx = min(comp_count, len(games) - 1) if games else 0
        if games:
            current_game = games[idx]
            
    if current_game:
        game_id = current_game.get("id", "unknown")
        game_number = current_game.get("number", 1)
    
    # Fallback heurístico caso o ID não tenha vindo no objeto game
    if game_id == "unknown" and match_id:
        game_id = str(int(match_id) + game_number)

    # Detecta se a série está finalizada pelos games (mais confiável que o campo state)
    strategy = match_data.get("strategy", {})
    series_count = strategy.get("count", 3)
    win_threshold = (series_count // 2) + 1  # BO3→2, BO5→3, BO1→1
    blue_wins = team_blue.get("result", {}).get("gameWins", 0) if isinstance(team_blue, dict) else 0
    red_wins = team_red.get("result", {}).get("gameWins", 0) if isinstance(team_red, dict) else 0

    is_unstarted = games and all(g.get("state") == "unstarted" for g in games)

    is_completed = (
        match_state == "completed"
        or (games and all(g.get("state") == "completed" for g in games))
        or blue_wins >= win_threshold
        or red_wins >= win_threshold
    )
    if is_completed:
        match_state = "completed"
    elif is_unstarted:
        match_state = "unstarted"

    game_info = {
        "match_id": match_id,
        "game_id": game_id,
        "game_number": game_number,
        "league": league_name,
        "team_blue": team_blue,
        "team_red": team_red,
        "state": match_state,
        "blue_wins": blue_wins,
        "red_wins": red_wins,
        "strategy": strategy,
    }

    # Even if unstarted, the match might already be 'in_game' in real-time.
    # Even if completed, we want final stats.
    enriched = await _enrich_match_with_window(game_info)
    
    # Se conseguimos dados em tempo real, confiamos mais no estado do frame
    if enriched.get("game_state") in ("in_game", "paused"):
        enriched["state"] = "inProgress"
    elif enriched.get("game_state") == "finished":
        enriched["state"] = "completed"
        
    return enriched


async def _enrich_match_with_window(game_info: dict) -> dict:
    """Adiciona dados de telemetria (kills, gold, campeões) ao dict da partida."""
    game_id = game_info.get("game_id", "unknown")
    result = dict(game_info)

    if game_id == "unknown":
        return result
    
    is_completed = game_info.get("state") == "completed"

    if is_completed:
        # Busca direto sem startingTime
        data = await _retry_system.async_fetch_with_retry(
            url=f"{API_URL_LIVE}/window/{game_id}",
            params={"hl": "pt-BR"},
            headers=HEADERS,
            timeout=10,
        )
    else:
        data = await _retry_system.async_fetch_with_retry(
            url=f"{API_URL_LIVE}/window/{game_id}",
            params={"hl": "pt-BR", "startingTime": get_iso_date_multiple_of_10(), "_": _get_cache_buster()},
            headers=HEADERS,
            timeout=10,
            retry_without_param="startingTime"
        )
        
        # Fallback
        if not data or not data.get("frames"):
            data = await _retry_system.async_fetch_with_retry(
                url=f"{API_URL_LIVE}/window/{game_id}",
                params={"hl": "pt-BR", "_": _get_cache_buster()},
                headers=HEADERS,
                timeout=10
            )

    if not data:
        return result

    frames = data.get("frames", [])
    if not frames:
        return result

    frame = frames[-1]
    metadata = data.get("gameMetadata") or {}

    blue_frame = frame.get("blueTeam", {})
    red_frame = frame.get("redTeam", {})
    blue_parts = blue_frame.get("participants", [])
    red_parts = red_frame.get("participants", [])
    
    # ─── Buscar Detalhes de Itens (Real-time) ───
    ts = frame.get("rfc460Timestamp")
    details_data = await get_game_details(game_id, timestamp=ts)
    detail_blue = []
    detail_red  = []
    if details_data:
        all_parts = details_data.get("participants", [])
        if all_parts and len(all_parts) >= 10:
            detail_blue = all_parts[:5]
            detail_red  = all_parts[5:]
        else:
            detail_blue = (details_data.get("blueTeam") or {}).get("participants", [])
            detail_red  = (details_data.get("redTeam") or {}).get("participants", [])

    metadata = data.get("gameMetadata") or {}
    blue_meta = (metadata.get("blueTeamMetadata") or {}).get("participantMetadata", [])
    red_meta = (metadata.get("redTeamMetadata") or {}).get("participantMetadata", [])

    def build_champs(parts, meta, details, opp_parts):
        champs = []
        for i, p in enumerate(parts):
            m = meta[i] if i < len(meta) else {}
            d = details[i] if i < len(details) else {}
            
            # Cálculo de Ouro +/- vs oponente direto na mesma posição
            opp_p = opp_parts[i] if i < len(opp_parts) else {}
            gold_diff = p.get("totalGold", 0) - opp_p.get("totalGold", 0)
            
            # Lista de IDs de Itens da API (geralmente uma lista no campo 'items')
            raw_items = d.get("items", [])
            if not isinstance(raw_items, list): raw_items = []
            # Garante 7 slots para o layout no Svelte
            items = raw_items + [0] * (7 - len(raw_items))

            champs.append({
                "champion": m.get("championId", ""),
                "summonerName": m.get("summonerName", m.get("esportsPlayerId", "")),
                "role": m.get("role", ""),
                "level": p.get("level", 1),
                "kills": p.get("kills", 0),
                "deaths": p.get("deaths", 0),
                "assists": p.get("assists", 0),
                "cs": p.get("creepScore", 0),
                "gold": p.get("totalGold", 0),
                "goldDiff": gold_diff,
                "currentHealth": p.get("currentHealth", 0),
                "maxHealth": p.get("maxHealth", 1),
                "items": items
            })
        return champs

    # Stats Gerais do Time
    result.update({
        "blue_kills":      blue_frame.get("totalKills", 0),
        "red_kills":       red_frame.get("totalKills", 0),
        "blue_gold":       blue_frame.get("totalGold", 0),
        "red_gold":        red_frame.get("totalGold", 0),
        "blue_towers":     blue_frame.get("towers", 0),
        "red_towers":      red_frame.get("towers", 0),
        "blue_barons":     blue_frame.get("barons", 0),
        "red_barons":      red_frame.get("barons", 0),
        "blue_heralds":    blue_frame.get("heralds", 0),
        "red_heralds":     red_frame.get("heralds", 0),
        "blue_inhibitors": blue_frame.get("inhibitors", 0),
        "red_inhibitors":  red_frame.get("inhibitors", 0),
        "blue_dragons":    blue_frame.get("dragons", []),
        "red_dragons":     red_frame.get("dragons", []),
        "blue_champs":     build_champs(blue_parts, blue_meta, detail_blue, red_parts),
        "red_champs":      build_champs(red_parts, red_meta, detail_red, blue_parts),
        "game_state":      frame.get("gameState", "inProgress"),
        "frame_timestamp": ts
    })

    return result


def create_polling_service(game_id: str, match_id: str):
    """
    Cria um PollingService para um game especifico com verificacao de estado.

    O callback do polling:
    1. Verifica o estado atual da partida
    2. Para o polling se a partida finalizou
    3. Limpa o cache das chaves window_* e details_* quando finaliza

    Args:
        game_id: ID do game a ser monitorado
        match_id: ID da serie/match

    Returns:
        PollingService configurado (nao iniciado)
    """
    from interface.polling_service import PollingService

    _ctx = {"game_id": game_id, "match_id": match_id}

    # Referencia mutavel para o servico (preenchida apos criacao)
    service_ref = [None]

    async def _polling_callback():
        """Callback que verifica estado e para polling quando partida finaliza."""
        # Busca dados atuais do game
        window_data = await get_game_window(game_id)

        if window_data is None:
            logger.debug(
                f"Polling: sem dados para game {game_id}",
                extra=_ctx
            )
            return

        # Verifica se a partida terminou
        if is_match_finished(window_data):
            logger.info(
                f"Partida {game_id} finalizada detectada pelo polling. Limpando cache e parando.",
                extra=_ctx
            )

            # Limpa cache das chaves relacionadas ao game
            _cache_layer.delete(f"window_{game_id}")
            _cache_layer.delete(f"details_{game_id}")

            # Para o polling
            svc = service_ref[0]
            if svc is not None:
                await svc.stop()

    service = PollingService(
        fetch_callback=_polling_callback,
        interval_seconds=10,
        logger=logger,
    )
    service_ref[0] = service
    return service
