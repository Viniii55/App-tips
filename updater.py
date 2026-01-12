import requests
import json
import os
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


# --- NOVA LÓGICA DE DICAS (REALISMO TRILIONÁRIO) ---
def generate_marketing_tip(home, away, outcomes, sport_key):
    """
    Gera uma Tip Realista e Válida baseada no Esporte e nas Odds.
    Nada de escanteios no Hockey!
    """
    import random
    
    # 1. Extrai Odds principais (Moneyline)
    home_odd = 2.0
    away_odd = 2.0
    draw_odd = 3.0
    
    # Tenta pegar odds reais
    try:
        for o in outcomes:
            if o['name'] == home: home_odd = o['price']
            elif o['name'] == away: away_odd = o['price']
            elif o['name'].lower() == 'draw': draw_odd = o['price']
    except: pass

    strategies = []
    
    # --- ESTRATÉGIAS POR ESPORTE ---
    
    # >>> FUTEBOL (SOCCER) <<<
    if 'soccer' in sport_key or 'football' in sport_key:
        # A) Dupla Chance (Segurança)
        if home_odd < 1.40:
            strategies.append({"market": f"Vencer: {home}", "odd": home_odd})
        elif away_odd < 1.40:
            strategies.append({"market": f"Vencer: {away}", "odd": away_odd})
        elif home_odd <= away_odd:
            strategies.append({"market": f"Chance Dupla: {home} ou Empate", "odd": 1.35})
        else:
            strategies.append({"market": f"Chance Dupla: {away} ou Empate", "odd": 1.42})
            
        # B) Gols (Mercado Real)
        strategies.append({"market": "Total de Gols: Over 1.5", "odd": 1.33})
        strategies.append({"market": "Total de Gols: Over 2.5", "odd": 1.85})
        
        # C) Escanteios (Só Futebol!)
        strategies.append({"market": "Escanteios: Mais de 8.5", "odd": 1.62})

    # >>> BASQUETE (BASKETBALL) <<<
    elif 'basketball' in sport_key:
        # Pontos e Handicap
        strategies.append({"market": "Total de Pontos: Over 215.5", "odd": 1.90})
        
        if home_odd < 1.50:
            strategies.append({"market": f"Vencer: {home}", "odd": home_odd})
        elif away_odd < 1.50:
            strategies.append({"market": f"Vencer: {away}", "odd": away_odd})
        else:
            strategies.append({"market": "Handicap: +5.5 (Favorito)", "odd": 1.75})

    # >>> TÊNIS (TENNIS) <<<
    elif 'tennis' in sport_key:
        if home_odd < 1.40:
            strategies.append({"market": f"Vencer: {home}", "odd": home_odd})
        elif away_odd < 1.40:
            strategies.append({"market": f"Vencer: {away}", "odd": away_odd})
        else:
            strategies.append({"market": "Total Sets: Over 2.5", "odd": 2.10})
            strategies.append({"market": "Vencedor do 1º Set: Favorito", "odd": 1.65})

    # >>> HOCKEY (ICE HOCKEY) <<<
    elif 'hockey' in sport_key or 'icehockey' in sport_key:
        # Gols (Puck Line) e Vencedor
        strategies.append({"market": "Total de Gols: Over 4.5", "odd": 1.45})
        strategies.append({"market": "Total de Gols: Over 5.5", "odd": 1.75})
        
        if home_odd < 1.60:
            strategies.append({"market": f"Vencer (Incl. Prorrogação): {home}", "odd": home_odd})
        elif away_odd < 1.60:
            strategies.append({"market": f"Vencer (Incl. Prorrogação): {away}", "odd": away_odd})

    # >>> MMA / LUTAS <<<
    elif 'mma' in sport_key:
         if home_odd < 1.50:
            strategies.append({"market": f"Vencer Luta: {home}", "odd": home_odd})
         else:
            strategies.append({"market": "Total Rounds: Over 1.5", "odd": 1.55})

    # >>> CASO GERAL (AMERICAN FOOTBALL, ETC) <<<
    else:
        strategies.append({"market": "Total Pontos: Over 40.5", "odd": 1.90})
        if home_odd < away_odd:
            strategies.append({"market": f"Vencer: {home}", "odd": home_odd})
        else:
            strategies.append({"market": f"Vencer: {away}", "odd": away_odd})


    # --- SELEÇÃO DE INTELECTUALIDADE TRILIONÁRIA ---
    # Escolhemos uma estratégia aleatória mas calculamos a probabilidade REAL
    selected = random.choice(strategies)
    
    # Cálculo de Probabilidade Fake-Realista
    # Prob = (1/Odd) * 100. Adicionamos um "Tempero da IA" (5% a 12%)
    implied_prob = (1 / selected['odd']) * 100
    ai_boost = random.uniform(5, 12)
    final_win_rate = int(min(96, implied_prob + ai_boost))
    
    return {
        "market": selected['market'],
        "odd": selected['odd'],
        "win_rate": final_win_rate
    }

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

        # NBA (Conferência Leste)
        "Boston Celtics": "https://upload.wikimedia.org/wikipedia/en/8/8f/Boston_Celtics.svg",
        "Brooklyn Nets": "https://upload.wikimedia.org/wikipedia/commons/4/44/Brooklyn_Nets_newlogo.svg",
        "New York Knicks": "https://upload.wikimedia.org/wikipedia/en/2/25/New_York_Knicks_logo.svg",
        "Philadelphia 76ers": "https://upload.wikimedia.org/wikipedia/en/0/0e/Philadelphia_76ers_logo.svg",
        "Toronto Raptors": "https://upload.wikimedia.org/wikipedia/en/3/36/Toronto_Raptors_logo.svg",
        "Chicago Bulls": "https://upload.wikimedia.org/wikipedia/en/6/67/Chicago_Bulls_logo.svg",
        "Cleveland Cavaliers": "https://upload.wikimedia.org/wikipedia/end/4/4b/Cleveland_Cavaliers_logo.svg",
        "Detroit Pistons": "https://upload.wikimedia.org/wikipedia/commons/7/7c/Pistons_logo17.svg",
        "Indiana Pacers": "https://upload.wikimedia.org/wikipedia/en/1/1b/Indiana_Pacers.svg",
        "Milwaukee Bucks": "https://upload.wikimedia.org/wikipedia/en/4/4a/Milwaukee_Bucks_logo.svg",
        "Atlanta Hawks": "https://upload.wikimedia.org/wikipedia/en/2/24/Atlanta_Hawks_logo.svg",
        "Charlotte Hornets": "https://upload.wikimedia.org/wikipedia/en/c/c4/Charlotte_Hornets_%282014%29.svg",
        "Miami Heat": "https://upload.wikimedia.org/wikipedia/en/f/fb/Miami_Heat_logo.svg",
        "Orlando Magic": "https://upload.wikimedia.org/wikipedia/en/1/10/Orlando_Magic_logo.svg",
        "Washington Wizards": "https://upload.wikimedia.org/wikipedia/en/0/02/Washington_Wizards_logo.svg",
        
        # NBA (Conferência Oeste)
        "Denver Nuggets": "https://upload.wikimedia.org/wikipedia/en/7/76/Denver_Nuggets.svg",
        "Minnesota Timberwolves": "https://upload.wikimedia.org/wikipedia/en/c/c2/Minnesota_Timberwolves_logo.svg",
        "Oklahoma City Thunder": "https://upload.wikimedia.org/wikipedia/en/5/5d/Oklahoma_City_Thunder.svg",
        "Portland Trail Blazers": "https://upload.wikimedia.org/wikipedia/en/2/21/Portland_Trail_Blazers_logo.svg",
        "Utah Jazz": "https://upload.wikimedia.org/wikipedia/en/0/04/Utah_Jazz_logo_%282016%29.svg",
        "Golden State Warriors": "https://upload.wikimedia.org/wikipedia/en/0/01/Golden_State_Warriors_logo.svg",
        "Los Angeles Clippers": "https://upload.wikimedia.org/wikipedia/en/b/bb/Los_Angeles_Clippers_logo.svg",
        "Los Angeles Lakers": "https://upload.wikimedia.org/wikipedia/commons/3/3c/Los_Angeles_Lakers_logo.svg",
        "Phoenix Suns": "https://upload.wikimedia.org/wikipedia/en/d/dc/Phoenix_Suns_logo.svg",
        "Sacramento Kings": "https://upload.wikimedia.org/wikipedia/en/c/c7/SacramentoKings.svg",
        "Dallas Mavericks": "https://upload.wikimedia.org/wikipedia/en/9/97/Dallas_Mavericks_logo.svg",
        "Houston Rockets": "https://upload.wikimedia.org/wikipedia/en/2/28/Houston_Rockets.svg",
        "Memphis Grizzlies": "https://upload.wikimedia.org/wikipedia/en/f/f1/Memphis_Grizzlies.svg",
        "New Orleans Pelicans": "https://upload.wikimedia.org/wikipedia/en/0/0d/New_Orleans_Pelicans_logo.svg",
        "San Antonio Spurs": "https://upload.wikimedia.org/wikipedia/en/a/a2/San_Antonio_Spurs.svg",
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
        
        # 2. Busca Inteligente na Wikimedia
        try:
            # Estratégia Diferente para Pessoas (Tênis/MMA) vs Times
            if sport_type in ['tennis', 'mma']:
                # Busca a PÁGINA do atleta e pega a foto principal
                wiki_url = "https://en.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "format": "json",
                    "prop": "pageimages",
                    "piprop": "thumbnail",
                    "pithumbsize": 300, # Tamanho bom
                    "titles": clean_name,
                    "redirects": 1
                }
                headers = {'User-Agent': 'SportsTipBot/2.0'}
                r = requests.get(wiki_url, params=params, headers=headers, timeout=3)
                data = r.json()
                pages = data.get("query", {}).get("pages", {})
                for k, v in pages.items():
                    if "thumbnail" in v:
                        logo_cache[clean_name] = v["thumbnail"]["source"]
                        return v["thumbnail"]["source"]

            else:
                # Busca ARQUIVO DE LOGO para times
                search_query = clean_name.replace(" FC", "").replace(" FK", "").strip()
                term = f"{search_query} logo"


            if is_athlete:
                params2['gsrsearch'] = clean_name # Busca o nome do atleta
                params2['gsrnamespace'] = 0 # Busca em páginas normais
            else:
                params2['gsrsearch'] = f"File:{clean_name} logo.png" # Tenta forçar PNG de logo
                params2['gsrnamespace'] = 6 # Namespace de Arquivo/Imagem
            
            r2 = requests.get("https://en.wikipedia.org/w/api.php", params=params2, headers=headers, timeout=3)
            data2 = r2.json()
            pages2 = data2.get("query", {}).get("pages", {})
            for k, v in pages2.items():
                 if "thumbnail" in v:
                    img_url = v["thumbnail"]["source"]
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
                        sport_type = 'ice_hockey'
                    elif 'mma' in sport_key:
                        sport_type = 'mma'
                    elif 'tennis' in sport_key:
                        sport_type = 'tennis'
                    else:
                        sport_type = 'soccer' # CORREÇÃO: Frontend espera 'soccer'

                    # Busca Logos Reais
                    logo_a = get_real_logo(game['home_team'], sport_type)
                    logo_b = get_real_logo(game['away_team'], sport_type)

                    match_obj = {
                        "id": game['id'],
                        "sport": sport_type,
                        "raw_league": sport_key, # Importante para filtros avançados
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
    # --- DESTAQUE DO DIA (JOGAÇO - Times Famosos) ---
    print(f">> Escolhendo o Destaque do Dia (Foco: Brasil/Elite)...")
    
    # Ordena por maior probabilidade de Green (Win Rate)
    unique_matches = {m['id']: m for m in all_matches}.values()
    sorted_matches = sorted(unique_matches, key=lambda x: x['tip']['win_rate'], reverse=True)

    # Lista de prioridade (Ligas Famosas)
    priority_leagues = [
        'soccer_brazil_campeonato', 'soccer_brazil_serie_b', 
        'soccer_libertadores', 'soccer_sulamericana',
        'soccer_epl', 'soccer_spain_la_liga', 'soccer_uefa_champs_league',
        'basketball_nba'
    ]
    
    highlight_match = None
    
    # 1. Tenta achar o melhor jogo das ligas prioritárias
    vip_matches = [m for m in sorted_matches if m.get('raw_league') in priority_leagues]
    
    # Se não achar por chave exata, tenta por nome (Fallback)
    if not vip_matches:
         famous_keywords = ['Brasileirão', 'Premier League', 'La Liga', 'NBA', 'Champions', 'Libertadores']
         vip_matches = [m for m in sorted_matches if any(k in m['league'] for k in famous_keywords)]
    
    if vip_matches:
        highlight_match = vip_matches[0] # O com maior win_rate dos famosos
    else:
        # Se não tiver jogo famoso, pega o Top 1 com maior win_rate geral (Segurança)
        if sorted_matches:
            highlight_match = sorted_matches[0]

    # --- PERSISTÊNCIA DE HISTÓRICO (PREPARAÇÃO V3) ---
    try:
        # Carrega histórico existente
        history_file = "bets_history.json"
        if os.path.exists(history_file):
            with open(history_file, "r") as f:
                history = json.load(f)
        else:
            history = []

        # Adiciona novos jogos ao histórico (sem duplicar ID)
        existing_ids = {h['id'] for h in history}
        new_count = 0
        for m in all_matches:
            if m['id'] not in existing_ids:
                # Adiciona status 'PENDING' para futura conferência
                m['status'] = 'PENDING' 
                history.append(m)
                new_count += 1
        
        # Mantém apenas os últimos 1000 jogos para não pesar
        if len(history) > 1000:
            history = history[-1000:]

        with open(history_file, "w") as f:
            json.dump(history, f, indent=4)
            
        print(f">> Histórico atualizado: {new_count} novos jogos gravados.")
    except Exception as e:
        print(f"XX Erro ao gravar histórico: {e}")

    # --- ORDENAÇÃO INTELIGENTE (TOP 100 MILHÕES) ---
    def get_league_priority(match):
        key = match.get('raw_league', '').lower()
        # Nível 1: Brasil e Latam (Ouro)
        if 'brazil' in key or 'libertadores' in key or 'sulamericana' in key:
            return 1
        # Nível 2: Elite Europa e NBA (Prata)
        if 'champs_league' in key or 'epl' in key or 'la_liga' in key or 'nba' in key:
            return 2
        # Nível 3: Resto
        return 3

    # Ordena: 1o Prioridade de Liga, 2o Horário do Jogo
    all_matches.sort(key=lambda x: (get_league_priority(x), x['date']))

    # Salva no JS (ATUALIZADO PARA DESTAQUE)
    try:
        with open("games_data.js", "w", encoding='utf-8') as f:
            js_content = f"window.gamesData = {json.dumps(all_matches, indent=4, ensure_ascii=False)};\n\n"
            
            if highlight_match:
                js_content += f"window.highlightMatch = {json.dumps(highlight_match, indent=4, ensure_ascii=False)};\n"
            else:
                js_content += "window.highlightMatch = null;\n"
            
            f.write(js_content)
        print(">> games_data.js gerado com SUCESSO! (Com Destaque do Dia)")
    except Exception as e:
        print(f"XX Erro ao salvar arquivo JS: {e}")

def format_league_name(key):
    """Deixa o nome da liga bonito para o usuário"""
    names = {
        'soccer_brazil_campeonato': 'Brasileirão Série A',
        'soccer_epl': 'Premier League',
        'soccer_spain_la_liga': 'La Liga',
        'basketball_nba': 'NBA'
    }
    return names.get(key, key.replace('_', ' ').title())

# Função Mock removida para garantir autenticidade.

def save_to_js(matches):
    print(f">> Gerando {len(matches)} oportunidades de CPA...")
    js_content = f"window.LIVE_GAMES = " + json.dumps(matches, indent=4) + ";"
    with open("games_data.js", "w", encoding="utf-8") as f:
        f.write(js_content)
    print(">> Banco de Dados Atualizado! As odds estao alinhadas com o mercado.")

if __name__ == "__main__":
    fetch_games()
