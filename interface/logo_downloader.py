
import os
import httpx
import re
import asyncio
from pathlib import Path
from bs4 import BeautifulSoup

LOGO_DIR = Path(__file__).parent.parent / "data" / "logos"
LOGO_DIR.mkdir(parents=True, exist_ok=True)

# User-Agent rigoroso seguindo as regras da Liquipedia
LIQUIPEDIA_USER_AGENT = "AI_LoL_Predictor/1.1 (https://github.com/philipesantos136/AI_LOL_Predictor; philipe.santos@example.com)"

async def download_team_logo_liquipedia(team_name: str) -> bool:
    """
    Tenta baixar a logo do time via Liquipedia API (Search + Scraping) e salva localmente.
    """
    clean_name = team_name.replace(" ", "_")
    output_path = LOGO_DIR / f"{clean_name}.png"
    
    if output_path.exists():
        return True

    headers = {
        "User-Agent": LIQUIPEDIA_USER_AGENT,
        "Accept-Encoding": "gzip"
    }
    
    async def get_team_page_via_search(name: str, client: httpx.AsyncClient) -> tuple[str, str]:
        """Usa API de busca para encontrar o nome correto e URL da página do time."""
        async def _search(q: str):
            try:
                url = f"https://liquipedia.net/leagueoflegends/api.php?action=opensearch&search={q}&limit=5&format=json"
                res = await client.get(url, timeout=10)
                if res.status_code == 200:
                    data = res.json()
                    titles, urls = data[1], data[3]
                    for i, title in enumerate(titles):
                        if q.lower() in title.lower(): return title, urls[i]
                    if urls: return titles[0], urls[0]
            except: pass
            return None, None

        # 1. Tenta nome completo
        title, url = await _search(name)
        if title: return title, url

        # 2. Tenta sem "Team" no início
        if name.lower().startswith("team "):
            title, url = await _search(name[5:])
            if title: return title, url

        # 3. Tenta apenas as duas primeiras palavras
        parts = name.split()
        if len(parts) > 2:
            title, url = await _search(" ".join(parts[:2]))
            if title: return title, url
            
        return None, None

    try:
        async with httpx.AsyncClient(headers=headers, follow_redirects=True) as client:
            print(f"🔍 Buscando {team_name} via API Liquipedia...")
            
            # Estratégia 1: Busca Direta via Opensearch
            team_title, team_page_url = await get_team_page_via_search(team_name, client)
            
            # Estratégia 2: Fallback para Portal:Teams (já usa API de parse)
            if not team_title:
                print(f"⚠️ Busca falhou para {team_name}. Tentando portal de times...")
                portal_url = "https://liquipedia.net/leagueoflegends/api.php?action=parse&page=Portal:Teams&format=json"
                response = await client.get(portal_url, timeout=20)
                
                if response.status_code == 200:
                    html_content = response.json().get('parse', {}).get('text', {}).get('*', '')
                    soup = BeautifulSoup(html_content, 'html.parser')
                    team_link = soup.find('a', title=re.compile(f"^{re.escape(team_name)}$", re.I))
                    if not team_link:
                        team_link = soup.find('a', string=re.compile(f"^{re.escape(team_name)}$", re.I))
                    
                    if team_link:
                        team_title = team_link.get('title')
                        # Se não tiver title, tenta extrair do href
                        if not team_title:
                            team_title = team_link['href'].split('/')[-1]

            if not team_title:
                print(f"❌ Time {team_name} não encontrado na Liquipedia.")
                return False
            
            # AGORA: Uso da API action=parse para pegar o conteúdo da página do time sem 403
            print(f"🔍 Parseando página do time via API: {team_title}")
            parse_url = f"https://liquipedia.net/leagueoflegends/api.php?action=parse&page={team_title}&format=json"
            parse_response = await client.get(parse_url, timeout=20)
            
            if parse_response.status_code != 200:
                print(f"❌ Falha ao parsear API para {team_title} (Status {parse_response.status_code})")
                return False
                
            html_content = parse_response.json().get('parse', {}).get('text', {}).get('*', '')
            if not html_content:
                print(f"❌ Conteúdo vazio na API de parse para {team_title}")
                return False

            team_soup = BeautifulSoup(html_content, 'html.parser')
            infobox = team_soup.find('div', class_='infobox-image') or team_soup.find('table', class_='infobox')
            
            if not infobox:
                print(f"❌ Infobox não encontrada (via API) na página de {team_name}")
                return False
                
            logo_img = infobox.find('img')
            if not logo_img:
                print(f"❌ Logo não encontrada na infobox de {team_name}")
                return False
            
            logo_src = logo_img.get('src') or logo_img.get('data-src')
            if not logo_src:
                return False

            logo_url = f"https://liquipedia.net{logo_src}" if logo_src.startswith('/') else logo_src
            
            # Limpa URL de thumbnail para pegar a original
            if '/thumb/' in logo_url:
                logo_url = logo_url.replace('/thumb/', '/')
                logo_url = '/'.join(logo_url.split('/')[:-1])

            print(f"⬇️ Baixando logo final: {logo_url}")
            img_res = await client.get(logo_url, timeout=20)
            img_res.raise_for_status()
            
            with open(output_path, "wb") as f:
                f.write(img_res.content)
            
            print(f"✅ Logo de {team_name} salva com sucesso!")
            return True
            
    except Exception as e:
        print(f"❌ Erro ao baixar da Liquipedia: {e}")
        return False
