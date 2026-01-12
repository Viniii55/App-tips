import requests
import json
from datetime import datetime

# --- CONFIGURAÇÃO ---
# Pegue sua chave GRÁTIS em: https://the-odds-api.com
API_KEY = "6233584194563674038ed0c9cd6fed8d" 

# Região 'eu' (Europa) costuma ter odds decimais (1.50) padrão Brasil
REGION = 'eu'
MARKETS = 'h2h,totals' # PEGA ODDS DE VENCEDOR E GOLS (OVER/UNDER)

# Lista de Ligas Focadas em Volume de Apostas
# Lista Expandida de Esportes (Foco no que está rolando agora)
SPORTS_INTEREST = [
    'soccer_brazil_campeonato',
    'soccer_epl',             # Premier League
    'soccer_spain_la_liga',   # La Liga
    'soccer_germany_bundesliga', # Bundesliga (Nova)
    'soccer_italy_serie_a',      # Serie A (Nova)
    'soccer_france_ligue_one',   # Ligue 1 (Nova)
    'soccer_portugal_primeira_liga', # Portugal (Nova)
    'soccer_netherlands_eredivisie', # Holanda (Nova)
    'soccer_uefa_champs_league',
    'basketball_nba',
    'americanfootball_nfl', 
    'icehockey_nhl',        
    'mma_mixed_martial_arts', 
    'tennis_atp_aus_open_singles'
]

# --- SIMULADOR DE PROPS & ESTRELAS ---
STAR_PLAYERS = {
    "Manchester City": "Haaland",
    "Liverpool": "Salah",
    "Real Madrid": "Vini Jr",
    "Barcelona": "Lewandowski",
    "Bayern Munich": "Kane",
    "Paris Saint-Germain": "Dembélé",
    "Flamengo": "Pedro",
    "Atletico Mineiro": "Hulk",
    "Palmeiras": "Estêvão",
    "Al-Nassr": "C. Ronaldo",
    "Inter Miami": "Messi",
    "Botafogo": "Luiz Henrique",
    "São Paulo": "Lucas Moura",
    "Arsenal": "Saka",
    "Chelsea": "Palmer"
}

def calculate_smart_probability(market_type, odd):
    """Calcula probabilidade ajustada baseada na 'segurança' do mercado"""
    try:
        base_prob = (1 / float(odd)) * 100
        
        # Boosters de inteligência (Simula análise de dados históricos)
        if "Dupla Chance" in market_type:
            return min(int(base_prob + 15), 96) # Muito seguro
        elif "Over 1.5" in market_type:
            return min(int(base_prob + 12), 94)
        elif "Escanteios" in market_type or "Cartões" in market_type:
            return 90 + int(odd * 2) # Fixo alto, mercados de volume
        else:
            # Vencedor simples
            if base_prob > 60:
                return min(int(base_prob * 1.1), 98)
            else:
                return int(base_prob)
    except:
        return 75

def analyze_match_depth(home, away, outcomes, bookies_data):
    """
    O CEREBRO DO APP: Escolhe a melhor tip baseada no cenário.
    """
    import random
    
    # 1. Identifica as Odds H2H
    home_odd = 2.50
    draw_odd = 3.00
    away_odd = 2.50
    
    for o in outcomes:
        if o['name'] == home: home_odd = o['price']
        elif o['name'] == away: away_odd = o['price']
        elif o['name'].lower() == 'draw': draw_odd = o['price']

    # 2. Estratégia: SUPER FAVORITO (Odd < 1.55)
    # Se tem um time muito forte, vamos de vitória seca ou gol do craque
    heavy_favorite = None
    if home_odd < 1.55: heavy_favorite = home
    if away_odd < 1.55: heavy_favorite = away
    
    if heavy_favorite:
        # 30% de chance de mandar um PROP de Jogador se tiver estrela
        if random.random() < 0.30 and heavy_favorite in STAR_PLAYERS:
            player = STAR_PLAYERS[heavy_favorite]
            return {
                "market": f"Gol a Qualquer Momento: {player}",
                "odd": 1.85, # Odd média de gol
                "win_rate": random.randint(82, 95)
            }
        # Senão vai de vitória simples (Safe)
        return {
            "market": f"Vencer: {heavy_favorite}",
            "odd": min(home_odd, away_odd),
            "win_rate": calculate_smart_probability("Winner", min(home_odd, away_odd))
        }

    # 3. Estratégia: JOGO EQUILIBRADO (Odds Altas)
    # Evita "Vencer Time" pq a chance é baixa (<50%).
    # Vamos buscar mercados alternativos.
    
    strategies = []
    
    # A) Dupla Chance (Super Seguro)
    # Se Casa é levemente favorito ou jogo parelho
    if home_odd < away_odd:
        safe_bet = f"{home} ou Empate"
        calc_odd = 1 / ((1/home_odd) + (1/draw_odd)) # Calc odd combinada aprox
    else:
        safe_bet = f"{away} ou Empate"
        calc_odd = 1 / ((1/away_odd) + (1/draw_odd))
        
    strategies.append({
        "market": f"Dupla Chance: {safe_bet}",
        "odd": round(calc_odd, 2),
        "win_rate": calculate_smart_probability("Dupla Chance", calc_odd)
    })
    
    # B) Gols (Over 1.5 é muito comum bater)
    strategies.append({
        "market": "Total de Gols: Over 1.5",
        "odd": 1.35,
        "win_rate": 88
    })
    
    # C) Mercados de Volume (Simulados para variedade)
    strategies.append({
        "market": "Escanteios: Mais de 8.5",
        "odd": 1.65,
        "win_rate": 91
    })
    
    if "Brasileirão" in str(bookies_data) or "Libertadores" in str(bookies_data):
        strategies.append({
            "market": "Total de Cartões: Over 3.5",
            "odd": 1.50,
            "win_rate": 94
        })

    # Escolhe a estratégia com MAIOR Win Rate para o usuário ficar feliz
    best_strat = sorted(strategies, key=lambda x: x['win_rate'], reverse=True)[0]
    return best_strat


def generate_marketing_tip(home, away, outcomes, sport_key):
    """Wrapper para chamar a análise profunda"""
    tip = analyze_match_depth(home, away, outcomes, sport_key)
    
    # Garante que não venha % baixa
    if tip['win_rate'] < 60:
        tip['win_rate'] = 71 # Correção mínima de calibração
        
    return tip

# --- FIM LOGICA NOVA ---

def calculate_probability(odd):
    """
    Converte Odd em Porcentagem de "Confiança".
    Formula: (1 / odd) * 100.
    Marketing Boost: Aumenta levemente a percepção para parecer 'Inteligência Artificial'.
    """
    try:
        real_prob = (1 / float(odd)) * 100
        # Boost de Marketing: Se for favorito (>60%), dá um boost de 10-15% para parecer "Green Certo"
        # Se for zebra (<30%), mantém real.
        if real_prob > 60:
            marketing_prob = real_prob * 1.15
        else:
            marketing_prob = real_prob
            
        # Teto máximo de 98% (pra não parecer fraude completa)
        final_prob = min(int(marketing_prob), 98)
        return final_prob
    except:
        return 50

def fetch_games():
    print(">> Buscando jogos de TUDO (Futebol, Basquete, MMA, Tênis)...")
    
    all_matches = []

    # Carrega cache de logos existente ou inicia vazio
    FORCE_REFRESH_LOGOS = False # Cache reativado para velocidade máxima!
    try:
        if FORCE_REFRESH_LOGOS:
            logo_cache = {}
        else:
            with open("logos_cache.json", "r") as f:
                logo_cache = json.load(f)
    except:
        logo_cache = {}

    # --- DICIONÁRIO DE ELITE (Logos Garantidos) ---
    KNOWN_LOGOS = {
        # Premier League
        "Arsenal": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg",
        "Aston Villa": "https://upload.wikimedia.org/wikipedia/en/f/f9/Aston_Villa_FC_crest_%282016%29.svg",
        "Bournemouth": "https://upload.wikimedia.org/wikipedia/en/e/e5/AFC_Bournemouth_%282013%29.svg",
        "Brentford": "https://upload.wikimedia.org/wikipedia/en/2/2a/Brentford_FC_crest.svg",
        "Brighton & Hove Albion": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_FC_logo.svg", # Brighton
        "Brighton": "https://upload.wikimedia.org/wikipedia/en/f/fd/Brighton_%26_Hove_Albion_FC_logo.svg",
        "Chelsea": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg",
        "Crystal Palace": "https://upload.wikimedia.org/wikipedia/en/a/a2/Crystal_Palace_FC_logo_%282022%29.svg",
        "Everton": "https://upload.wikimedia.org/wikipedia/en/7/7c/Everton_FC_logo.svg",
        "Fulham": "https://upload.wikimedia.org/wikipedia/en/e/eb/Fulham_FC_%28shield%29.svg",
        "Leeds United": "https://upload.wikimedia.org/wikipedia/en/5/54/Leeds_United_F.C._logo.svg", # Leeds
        "Leicester City": "https://upload.wikimedia.org/wikipedia/en/2/2d/Leicester_City_crest.svg",
        "Liverpool": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg",
        "Manchester City": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg",
        "Manchester United": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg",
        "Newcastle United": "https://upload.wikimedia.org/wikipedia/en/5/56/Newcastle_United_Logo.svg",
        "Nottingham Forest": "https://upload.wikimedia.org/wikipedia/en/e/e5/Nottingham_Forest_F.C._logo.svg",
        "Southampton": "https://upload.wikimedia.org/wikipedia/en/c/c9/FC_Southampton.svg",
        "Tottenham Hotspur": "https://upload.wikimedia.org/wikipedia/en/b/b4/Tottenham_Hotspur.svg",
        "West Ham United": "https://upload.wikimedia.org/wikipedia/en/c/c2/West_Ham_United_FC_logo.svg",
        "Wolverhampton Wanderers": "https://upload.wikimedia.org/wikipedia/en/f/fc/Wolverhampton_Wanderers.svg",
        
        # Gigantes Europa & Correções
        "Real Madrid": "https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg",
        "Barcelona": "https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg",
        "Paris Saint-Germain": "https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg",
        "Bayern Munich": "https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg",
        "Deportivo Alavés": "https://upload.wikimedia.org/wikipedia/en/2/2e/Deportivo_Alaves_logo.svg", # Correção
        "Alavés": "https://upload.wikimedia.org/wikipedia/en/2/2e/Deportivo_Alaves_logo.svg", # Variação
        "Sevilla": "https://upload.wikimedia.org/wikipedia/en/3/3b/Sevilla_FC_logo.svg", # Correção
        "Sporting CP": "https://upload.wikimedia.org/wikipedia/en/e/e1/Sporting_Clube_de_Portugal_%28Logo%29.svg", # Correção
        "Sporting Lisbon": "https://upload.wikimedia.org/wikipedia/en/e/e1/Sporting_Clube_de_Portugal_%28Logo%29.svg", # Variação
        "Benfica": "https://upload.wikimedia.org/wikipedia/en/a/a2/SL_Benfica_logo.svg", # Correção
        
        # Brasileirão
        "Flamengo": "https://upload.wikimedia.org/wikipedia/commons/2/2e/Flamengo_braz_logo.svg",
        "Palmeiras": "https://upload.wikimedia.org/wikipedia/commons/1/10/Palmeiras_logo.svg",
        "São Paulo": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6f/Brasao_do_Sao_Paulo_Futebol_Clube.svg/240px-Brasao_do_Sao_Paulo_Futebol_Clube.svg.png",
        "Corinthians": "https://upload.wikimedia.org/wikipedia/en/5/5a/Sport_Club_Corinthians_Paulista_crest.svg",
        "Atlético Mineiro": "https://upload.wikimedia.org/wikipedia/en/5/5f/Clube_Atl%C3%A9tico_Mineiro_crest.svg",
        "Atletico Mineiro": "https://upload.wikimedia.org/wikipedia/en/5/5f/Clube_Atl%C3%A9tico_Mineiro_crest.svg",

        # NBA
        "Los Angeles Lakers": "https://upload.wikimedia.org/wikipedia/commons/3/3c/Los_Angeles_Lakers_logo.svg",
        "Golden State Warriors": "https://upload.wikimedia.org/wikipedia/en/0/01/Golden_State_Warriors_logo.svg",
        "Boston Celtics": "https://upload.wikimedia.org/wikipedia/en/8/8f/Boston_Celtics.svg",
    }

    def get_real_logo(name, sport_type):
        """Busca logo (Prioridade: Manual VIP > Wiki File Search > Fallback)"""
        
        # 0. Limpeza básica do nome
        clean_name = name.strip()
        
        # 1. Verifica Dicionário VIP
        if clean_name in KNOWN_LOGOS:
            return KNOWN_LOGOS[clean_name]
        
        # Check cache
        if clean_name in logo_cache and 'ui-avatars' not in logo_cache[clean_name]:
             return logo_cache[clean_name]
        
        # 2. Busca Inteligente na Wikimedia (Focado em ARQUIVOS de imagem)
        try:
            # Remove sufixos comuns que atrapalham a busca exata
            search_query = clean_name.replace(" FC", "").replace(" FK", "").strip()
            
            # Se for tenis/mma, busca mais generica, se for futebol busca "crest/logo"
            if sport_type in ['tennis', 'mma']:
                term = f"{search_query} {sport_type} profile"
            else:
                term = f"{search_query} logo"

            search_url = "https://en.wikipedia.org/w/api.php"
            params = {
                "action": "query",
                "format": "json",
                "list": "search",
                "srsearch": f"File:{term}", # PREFIDE FILE: para buscar arquivos de imagem
                "srnamespace": "6", # Namespace 6 = Arquivos (Images/Media)
                "srlimit": 1
            }
            headers = {'User-Agent': 'SportsTipBot/2.0 (vinicius_smart_search)'}
            
            r = requests.get(search_url, params=params, headers=headers, timeout=3)
            data = r.json()
            
            if data['query']['search']:
                # Achou um arquivo de imagem!
                file_title = data['query']['search'][0]['title']
                
                # Pega a URL real dessa imagem
                img_params = {
                    "action": "query",
                    "format": "json",
                    "prop": "imageinfo",
                    "iiprop": "url",
                    "titles": file_title
                }
                r_img = requests.get(search_url, params=img_params, headers=headers, timeout=3)
                data_img = r_img.json()
                
                pages = data_img['query']['pages']
                for k, v in pages.items():
                    if 'imageinfo' in v:
                        img_url = v['imageinfo'][0]['url']
                        logo_cache[clean_name] = img_url
                        return img_url

        except Exception:
            pass

        # 3. Fallback UI Avatars
        def get_color(n):
            return hex(hash(n) & 0xFFFFFF)[2:].zfill(6)
            
        fallback = f"https://ui-avatars.com/api/?name={requests.utils.quote(clean_name)}&background={get_color(clean_name)}&color=fff&size=128&bold=true&font-size=0.4"
        logo_cache[clean_name] = fallback 
        return fallback

    # Salva cache atualizado no final
    def save_cache():
        with open("logos_cache.json", "w") as f:
            json.dump(logo_cache, f)

    for sport_key in SPORTS_INTEREST:
        # Busca sem filtros de data (pega tudo que a API der)
        url = f'https://api.the-odds-api.com/v4/sports/{sport_key}/odds'
        params = {
            'apiKey': API_KEY,
            'regions': REGION,
            'markets': MARKETS,
            'oddsFormat': 'decimal',
            'commenceTimeFrom': datetime.now().strftime("%Y-%m-%dT%H:%M:%SZ") # A partir de AGORA
        }

        try:
            # MODO REAL ATIVADO
            response = requests.get(url, params=params)
            data = response.json()
            
            # Verificação de erro da API (ex: Quota excedida)
            if isinstance(data, dict) and 'message' in data:
                print(f"!! Erro API ({sport_key}): {data['message']}")
                continue

            if isinstance(data, list):
                print(f"   > Processando {sport_key}...")
                for game in data:
                    if not game['bookmakers']: continue
                        
                    # Pega odds do primeiro bookie disponível
                    bookmaker = game['bookmakers'][0] 
                    outcomes = bookmaker['markets'][0]['outcomes']
                    
                    # Gera a Tip focada em Conversão (Agora com IA de Mercados)
                    tip = generate_marketing_tip(game['home_team'], game['away_team'], outcomes, sport_key)
                    
                    if 'basketball' in sport_key:
                        sport_type = 'basketball'
                    elif 'americanfootball' in sport_key:
                        sport_type = 'american_football'
                    elif 'icehockey' in sport_key:
                        sport_type = 'hockey'
                    elif 'mma' in sport_key:
                        sport_type = 'mma'
                    elif 'tennis' in sport_key:
                        sport_type = 'tennis'
                    else:
                        sport_type = 'football'

                    # Busca Logos Reais
                    logo_a = get_real_logo(game['home_team'], sport_type)
                    logo_b = get_real_logo(game['away_team'], sport_type)

                    match_obj = {
                        "id": game['id'],
                        "sport": sport_type,
                        "league": format_league_name(sport_key),
                        "date": game['commence_time'],
                        "teamA": {"name": game['home_team'], "logo": logo_a},
                        "teamB": {"name": game['away_team'], "logo": logo_b},
                        "tip": tip
                    }
                    all_matches.append(match_obj)
            else:
                print(f"!! Limite de API ou erro em {sport_key}")

        except Exception as e:
            print(f"XX Erro Tecnico: {e}")

    save_cache()
    save_to_js(all_matches)

def format_league_name(key):
    """Deixa o nome da liga bonito para o usuário"""
    names = {
        'soccer_brazil_campeonato': 'Brasileirão Série A',
        'soccer_epl': 'Premier League',
        'soccer_spain_la_liga': 'La Liga',
        'basketball_nba': 'NBA'
    }
    return names.get(key, key.replace('_', ' ').title())

def generate_mock_data(sport):
    """Dados falsos apenas para demonstração do script"""
    from datetime import timedelta
    now = datetime.now()
    
    if 'soccer' in sport:
        return [
            {
                "id": "match_1",
                "commence_time": now.isoformat(),
                "home_team": "Manchester City",
                "away_team": "Burnley",
                "bookmakers": [{
                   "markets": [{"outcomes": [{"name": "Manchester City", "price": 1.15}, {"name": "Burnley", "price": 15.0}]}]
                }]
            },
            {
                "id": "match_2",
                "commence_time": (now + timedelta(hours=2)).isoformat(),
                "home_team": "Real Madrid",
                "away_team": "Getafe",
                "bookmakers": [{
                   "markets": [{"outcomes": [{"name": "Real Madrid", "price": 1.30}, {"name": "Getafe", "price": 9.50}]}]
                }]
            }
        ]
    return []

def save_to_js(matches):
    print(f">> Gerando {len(matches)} oportunidades de CPA...")
    js_content = f"window.LIVE_GAMES = " + json.dumps(matches, indent=4) + ";"
    with open("games_data.js", "w", encoding="utf-8") as f:
        f.write(js_content)
    print(">> Banco de Dados Atualizado! As odds estao alinhadas com o mercado.")

if __name__ == "__main__":
    fetch_games()
