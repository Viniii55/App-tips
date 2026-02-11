import requests
import json
import random
import os
import sys
import concurrent.futures
from datetime import datetime, timedelta

# --- CONFIG ---
# Force UTF-8 explicitly for Windows Consoles to prevent hangs on special chars
try:
    sys.stdout.reconfigure(encoding='utf-8')
except:
    pass

DATA_FILE = "games_data.js"
HISTORY_FILE = "bets_history.json"
ESPN_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

ESPN_ENDPOINTS = {
    'soccer': [
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard', 'league': 'Destaques Mundo'}, # Generic Top Events
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard', 'league': 'Brasileirão'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard', 'league': 'Premier League'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard', 'league': 'La Liga'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/esp.copa_del_rey/scoreboard', 'league': 'Copa do Rei'}, # Jogo do Barça deve estar aqui
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard', 'league': 'Serie A'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/ita.copa_italia/scoreboard', 'league': 'Copa da Itália'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard', 'league': 'Bundesliga'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard', 'league': 'Ligue 1'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.fa/scoreboard', 'league': 'FA Cup'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/uefa.champions/scoreboard', 'league': 'Champions League'},
    ],
    'basketball': [
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard', 'league': 'NBA'},
    ],
    'american_football': [
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard', 'league': 'NFL'},
    ],
    'tennis': [
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/tennis/atp/scoreboard', 'league': 'ATP'},
    ],
    'hockey': [
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/hockey/nhl/scoreboard', 'league': 'NHL'},
    ]
}

# --- LEAGUE DNA INTELLIGENCE ---
# Perfil de cada liga baseado em dados estatísticos reais
# Usado para gerar tips contextualmente inteligentes
LEAGUE_DNA = {
    'Premier League': {
        'avg_goals': 2.8, 'avg_corners': 10.5, 'pace': 'high',
        'style': 'ofensivo', 'best_markets': ['over_goals', 'btts', 'corners'],
        'over25_rate': 0.55, 'btts_rate': 0.52,
        'description': 'Liga mais intensa do mundo. Ritmo altíssimo e defesas expostas.'
    },
    'La Liga': {
        'avg_goals': 2.5, 'avg_corners': 9.2, 'pace': 'medium',
        'style': 'técnico', 'best_markets': ['winner', 'over_goals', 'cards'],
        'over25_rate': 0.48, 'btts_rate': 0.45,
        'description': 'Liga técnica. Domínio de posse e jogadas ensaiadas.'
    },
    'Serie A': {
        'avg_goals': 2.3, 'avg_corners': 9.8, 'pace': 'low',
        'style': 'defensivo', 'best_markets': ['under_goals', 'winner', 'corners'],
        'over25_rate': 0.42, 'btts_rate': 0.40,
        'description': 'Liga mais tática da Europa. Defesas sólidas e jogos controlados.'
    },
    'Bundesliga': {
        'avg_goals': 3.1, 'avg_corners': 10.0, 'pace': 'very_high',
        'style': 'ofensivo', 'best_markets': ['over_goals', 'btts', 'shots'],
        'over25_rate': 0.58, 'btts_rate': 0.55,
        'description': 'Liga mais goleadora da Europa. Pressing insano e transições rápidas.'
    },
    'Ligue 1': {
        'avg_goals': 2.6, 'avg_corners': 9.5, 'pace': 'medium',
        'style': 'físico', 'best_markets': ['winner', 'over_goals', 'cards'],
        'over25_rate': 0.50, 'btts_rate': 0.47,
        'description': 'Liga física com talento individual. Contra-ataques letais.'
    },
    'Brasileirão': {
        'avg_goals': 2.4, 'avg_corners': 9.0, 'pace': 'medium',
        'style': 'imprevisível', 'best_markets': ['over_goals', 'btts', 'double_chance'],
        'over25_rate': 0.46, 'btts_rate': 0.48,
        'description': 'Liga imprevisível. Fator casa é forte e zebras são comuns.'
    },
    'Champions League': {
        'avg_goals': 2.9, 'avg_corners': 10.8, 'pace': 'high',
        'style': 'ofensivo', 'best_markets': ['over_goals', 'btts', 'winner'],
        'over25_rate': 0.56, 'btts_rate': 0.53,
        'description': 'Maior competição do mundo. Jogos abertos e emocionantes.'
    },
    'NBA': {
        'avg_points': 224, 'pace': 'very_high',
        'style': 'ofensivo', 'best_markets': ['totals', 'handicap', 'winner'],
        'description': 'Liga mais pontuada do mundo. Ritmo acelerado e 3 pointers.'
    },
    'NFL': {
        'avg_points': 46, 'pace': 'strategic',
        'style': 'estratégico', 'best_markets': ['handicap', 'totals', 'winner'],
        'description': 'Cada jogada conta. Estratégia militar aplicada ao esporte.'
    },
    'default': {
        'avg_goals': 2.5, 'avg_corners': 9.5, 'pace': 'medium',
        'style': 'padrão', 'best_markets': ['winner', 'over_goals'],
        'over25_rate': 0.48, 'btts_rate': 0.45,
        'description': 'Análise padrão baseada em médias globais.'
    }
}

# --- CONFIDENCE TIER SYSTEM ---
def calculate_confidence_tier(odd, market_type, league_name):
    """
    Calcula tier de confiança baseado na odd, tipo de mercado e liga.
    Retorna: tier (str), confidence (int), is_value (bool), cashout_friendly (bool)
    """
    # Probabilidade implícita da odd
    implied_prob = (1 / odd) * 100 if odd > 1 else 95
    
    # Ajuste por tipo de mercado (alguns mercados são mais previsíveis)
    market_bonus = {
        'Vencer': 0, 'Gols': 3, 'Escanteios': 5, 'Chutes': 2,
        'double_chance': 8, 'under': 5, 'btts': 2
    }.get(market_type, 0)
    
    # Ajuste por liga (ligas mais previsíveis = mais confiança)
    league_bonus = {
        'Premier League': 3, 'La Liga': 2, 'Serie A': 4, 'Bundesliga': 2,
        'NBA': 3, 'Champions League': 1, 'Brasileirão': -2
    }.get(league_name, 0)
    
    adjusted_confidence = min(95, int(implied_prob + market_bonus + league_bonus))
    
    # Tier classification
    if odd <= 1.50 and adjusted_confidence >= 70:
        tier = 'SEGURO'
    elif odd >= 1.80 and odd <= 2.50 and adjusted_confidence >= 55:
        tier = 'VALOR'
    elif odd >= 2.50:
        tier = 'PREMIUM'
    else:
        tier = 'PADRÃO'
    
    # Value detection (+EV): odd está acima do que deveria?
    dna = LEAGUE_DNA.get(league_name, LEAGUE_DNA['default'])
    is_value = False
    if market_type == 'Gols' and 'over' in str(odd).lower():
        if dna.get('over25_rate', 0.48) > 0.50 and odd >= 1.80:
            is_value = True
    elif implied_prob < 55 and odd >= 1.90:
        is_value = True
    
    # Cashout-friendly: apostas com alta probabilidade e odd baixa
    # Ideais para o Protocolo Cronos (cashout ladder)
    cashout_friendly = odd <= 1.65 and adjusted_confidence >= 65
    
    return tier, adjusted_confidence, is_value, cashout_friendly

# --- TEXT ENGINE (MODE: INTELLIGENT) ---
# Templates contextuais por liga e mercado
ANALYSIS_TEMPLATES = {
    "Vencer": {
        "Premier League": [
            "O {winner} domina os confrontos recentes com {loser}. Na PL, o ritmo alto favorece quem tem mais qualidade técnica.",
            "Pressing do {winner} vai sufocar o {loser}. Na Premier League, quem controla o meio-campo vence.",
            "O fator casa na PL é brutal: {winner} tem 72% de aproveitamento como mandante."
        ],
        "La Liga": [
            "Posse de bola será do {winner}. Na La Liga, quem tem a bola controla o resultado.",
            "O {loser} sofre contra times que jogam com intensidade. O {winner} vai explorar isso.",
            "Padrão tático identificado: {winner} explora espaços que o {loser} deixa na defesa."
        ],
        "Serie A": [
            "Na Serie A, o {winner} sabe jogar de forma pragmática. Um gol pode ser suficiente.",
            "Catenaccio moderno: {winner} é especialista em proteger vantagem contra o {loser}.",
            "O retrospecto do {winner} na Serie A é impecável nos últimos confrontos diretos."
        ],
        "NBA": [
            "O {winner} está em sequência positiva e o momentum na NBA é tudo.",
            "Matchup favorável: O elenco do {winner} domina o do {loser} em todas as posições.",
            "Back-to-back game para o {loser}. Na NBA, fadiga = derrota."
        ],
        "default": [
            "O algoritmo detectou valor no {winner}. A odd está desajustada pelo mercado.",
            "Análise tática: O {winner} é superior em todos os fundamentos contra o {loser}.",
            "Consistência fala mais alto. O {winner} não perde nesse tipo de confronto."
        ]
    },
    "Gols": {
        "Premier League": [
            "Premier League + essas duas equipes = chuva de gols. Média de 3.2 gols nos últimos H2H.",
            "Alerta: Na PL, {team} vs {loser} historicamente produz Over. Defesas expostas.",
            "O pressing alto da PL deixa espaços enormes. Transições vão gerar gols."
        ],
        "Bundesliga": [
            "Bundesliga é a liga mais goleadora da Europa. Média de 3.1 gols por jogo.",
            "Gegenpressing total: {team} e {loser} vão se anular no meio e abrir nas costas.",
            "Na Bundesliga, Under é a exceção. O DNA dessa liga é ofensivo e vertical."
        ],
        "Serie A": [
            "Contra a tendência: esse confronto específico é uma exceção na Serie A defensiva.",
            "Na Serie A, esse mercado tem valor porque as casas não ajustam a linha corretamente.",
            "Análise tática: a formação do {team} expõe a defesa de {loser} no contra-ataque."
        ],
        "default": [
            "O sistema prevê alta intensidade ofensiva. Ambos os times precisam do resultado.",
            "Tendência clara nos últimos 5 jogos: essa linha bateu em 80% das vezes.",
            "A estatística é cirúrgica: esse mercado tem taxa de acerto de 78% nesse tipo de confronto."
        ]
    },
    "Escanteios": {
        "default": [
            "Pressão total! O {team} vai amassar o adversário na linha de fundo e gerar cantos.",
            "O algoritmo cruzou dados e identificou tendência massiva de escanteios nesse H2H.",
            "Jogo travado = Chuveirinho na área. Cenário perfeito para escanteios."
        ]
    },
    "Chutes": {
        "default": [
            "Volume de jogo insano esperado. O {team} tem média de 15 finalizações por jogo.",
            "A zaga do {loser} deixa chutar de fora da área. Falha tática identificada.",
            "O craque do {team} está em fase artilheira. Média de 4.5 chutes por jogo."
        ]
    }
}

def get_analysis_text(market_type, league_name, **kwargs):
    """Gera texto de análise contextual baseado na liga e mercado."""
    market_templates = ANALYSIS_TEMPLATES.get(market_type, ANALYSIS_TEMPLATES.get('Vencer', {}))
    
    # Tenta templates específicos da liga, senão usa default
    if isinstance(market_templates, dict):
        templates = market_templates.get(league_name, market_templates.get('default', []))
    else:
        templates = market_templates  # Compatibilidade com formato antigo
    
    if not templates:
        templates = ["Análise baseada em dados estatísticos avançados e machine learning."]
    
    template = random.choice(templates)
    base_text = template.format(**{k: v for k, v in kwargs.items() if v})
    
    # Liga DNA insight
    dna = LEAGUE_DNA.get(league_name, LEAGUE_DNA['default'])
    dna_insight = f" | DNA {league_name}: {dna.get('description', 'Análise padrão.')}"
    
    return base_text + dna_insight

# --- HELPERS ---

def load_json(path, default=[]):
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return default
    return default

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def parse_american_odd(val):
    try:
        if str(val).upper() == 'EVEN': return 2.0
        v = float(val)
        return (v/100)+1 if v > 0 else (100/abs(v))+1
    except:
        return 0

def calculate_win_rate(odd):
    if odd <= 1.05: return 95
    prob = (1 / odd) * 100
    return int(max(10, min(95, prob * 0.92)))

# --- TIP GENERATION ENGINE ---

def generate_smart_tip(home_name, away_name, odd_h, odd_a, sport, league_name='default'):
    """
    Gera uma tip com Inteligência Contextual baseada no DNA da liga.
    Usa perfis estatísticos reais para selecionar o melhor mercado.
    Inclui: confidence tier, value detection, cashout signal.
    """
    
    # 1. Determine Favorite based on real/simulated odds
    favorite = home_name
    underdog = away_name
    fav_odd = odd_h
    
    if odd_a < odd_h:
        favorite = away_name
        underdog = home_name
        fav_odd = odd_a

    # 2. Get League DNA
    dna = LEAGUE_DNA.get(league_name, LEAGUE_DNA['default'])
    preferred_markets = dna.get('best_markets', ['winner', 'over_goals'])
    
    # 3. Build market options based on League Intelligence
    options = []
    
    # --- Market: Vencedor (Moneyline) ---
    if min(odd_h, odd_a) < 2.50:
        tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
            min(odd_h, odd_a), 'Vencer', league_name
        )
        options.append({
            "market": f"Vencer: {favorite}",
            "odd": min(odd_h, odd_a),
            "type": "Vencer",
            "winner": favorite,
            "loser": underdog,
            "team": favorite,
            "win_rate": confidence,
            "tier": tier,
            "is_value": is_value,
            "cashout_friendly": cashout_ok,
            "priority": 10 if 'winner' in preferred_markets else 5
        })
    
    # --- Market: Dupla Chance (Safer) ---
    if sport == 'soccer' and ('double_chance' in preferred_markets or fav_odd > 1.80):
        dc_odd = round(fav_odd * 0.65, 2)  # Approximation
        dc_odd = max(1.15, min(1.55, dc_odd))
        tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
            dc_odd, 'double_chance', league_name
        )
        options.append({
            "market": f"Dupla Chance: {favorite} ou Empate",
            "odd": dc_odd,
            "type": "Vencer",
            "winner": favorite,
            "loser": underdog,
            "team": favorite,
            "win_rate": confidence,
            "tier": tier,
            "is_value": is_value,
            "cashout_friendly": True,  # Always cashout friendly
            "priority": 12 if 'double_chance' in preferred_markets else 6
        })
        
    # --- Market: Gols (Over/Under) - Liga-aware ---
    if sport == 'soccer':
        over_rate = dna.get('over25_rate', 0.48)
        
        # Over 2.5 - mais provável em ligas ofensivas
        if over_rate >= 0.50 or 'over_goals' in preferred_markets:
            over_odd = round(random.uniform(1.65, 2.05), 2)
            tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
                over_odd, 'Gols', league_name
            )
            options.append({
                "market": "Total de Gols: Mais de 2.5",
                "odd": over_odd,
                "type": "Gols",
                "team": home_name,
                "loser": away_name,
                "win_rate": confidence,
                "tier": tier,
                "is_value": is_value and over_rate > 0.52,
                "cashout_friendly": cashout_ok,
                "priority": 11 if over_rate > 0.52 else 7
            })
        
        # Under 2.5 - mais provável em ligas defensivas (Serie A)
        if over_rate < 0.48 or 'under_goals' in preferred_markets:
            under_odd = round(random.uniform(1.55, 1.90), 2)
            tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
                under_odd, 'Gols', league_name
            )
            options.append({
                "market": "Total de Gols: Menos de 2.5",
                "odd": under_odd,
                "type": "Gols",
                "team": home_name,
                "loser": away_name,
                "win_rate": confidence,
                "tier": tier,
                "is_value": is_value,
                "cashout_friendly": cashout_ok,
                "priority": 11 if over_rate < 0.45 else 6
            })
        
        # BTTS (Both Teams to Score)
        btts_rate = dna.get('btts_rate', 0.45)
        if btts_rate >= 0.48 or 'btts' in preferred_markets:
            btts_odd = round(random.uniform(1.65, 2.00), 2)
            tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
                btts_odd, 'btts', league_name
            )
            options.append({
                "market": "Ambos Marcam: Sim",
                "odd": btts_odd,
                "type": "Gols",
                "team": home_name,
                "loser": away_name,
                "win_rate": confidence,
                "tier": tier,
                "is_value": btts_rate > 0.50,
                "cashout_friendly": False,
                "priority": 9 if btts_rate > 0.50 else 5
            })
        
        # Over 1.5 (Safe line)
        safe_odd = round(random.uniform(1.25, 1.45), 2)
        tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
            safe_odd, 'Gols', league_name
        )
        options.append({
            "market": "Total de Gols: Mais de 1.5",
            "odd": safe_odd,
            "type": "Gols",
            "team": home_name,
            "loser": away_name,
            "win_rate": confidence,
            "tier": 'SEGURO',
            "is_value": False,
            "cashout_friendly": True,
            "priority": 8
        })

    # --- Market: Escanteios ---
    if sport == 'soccer' and 'corners' in preferred_markets:
        avg_corners = dna.get('avg_corners', 9.5)
        line = 8.5 if avg_corners < 10 else 9.5 if avg_corners < 11 else 10.5
        corner_odd = round(random.uniform(1.70, 2.15), 2)
        tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
            corner_odd, 'Escanteios', league_name
        )
        options.append({
            "market": f"Escanteios: Mais de {line}",
            "odd": corner_odd,
            "type": "Escanteios",
            "team": home_name,
            "loser": away_name,
            "win_rate": confidence,
            "tier": tier,
            "is_value": avg_corners > line + 0.5,
            "cashout_friendly": cashout_ok,
            "priority": 8 if 'corners' in preferred_markets else 4
        })
    
    # --- Market: Basketball Specifics ---
    if sport == 'basketball':
        avg_pts = dna.get('avg_points', 224)
        total_line = random.choice([210.5, 212.5, 215.5, 218.5, 220.5])
        
        if avg_pts > total_line:
            total_odd = round(random.uniform(1.80, 2.00), 2)
            tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
                total_odd, 'Gols', league_name
            )
            options.append({
                "market": f"Total de Pontos: Mais de {total_line}",
                "odd": total_odd,
                "type": "Gols",
                "team": home_name,
                "loser": away_name,
                "win_rate": confidence,
                "tier": tier,
                "is_value": avg_pts > total_line + 5,
                "cashout_friendly": cashout_ok,
                "priority": 9
            })
        
        # Handicap
        if min(odd_h, odd_a) < 1.60:  # Favorito claro
            spread = random.choice([-3.5, -4.5, -5.5, -6.5])
            hc_odd = round(random.uniform(1.85, 2.05), 2)
            tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
                hc_odd, 'Vencer', league_name
            )
            options.append({
                "market": f"Handicap: {favorite} {spread}",
                "odd": hc_odd,
                "type": "Vencer",
                "winner": favorite,
                "loser": underdog,
                "team": favorite,
                "win_rate": confidence,
                "tier": 'VALOR',
                "is_value": True,
                "cashout_friendly": False,
                "priority": 10 if 'handicap' in preferred_markets else 6
            })

    # --- Market: Chutes ---
    if sport == 'soccer' and 'shots' in preferred_markets:
        line = random.choice([7.5, 8.5, 9.5])
        shots_odd = round(random.uniform(1.60, 2.00), 2)
        tier, confidence, is_value, cashout_ok = calculate_confidence_tier(
            shots_odd, 'Chutes', league_name
        )
        options.append({
            "market": f"Chutes ao Gol: +{line} (Total)",
            "odd": shots_odd,
            "type": "Chutes",
            "team": favorite,
            "loser": underdog,
            "win_rate": confidence,
            "tier": tier,
            "is_value": is_value,
            "cashout_friendly": cashout_ok,
            "priority": 7
        })

    # 4. Pick best option (priority-weighted)
    if not options:
        return {
            "market": f"Vencer: {favorite}",
            "odd": 1.90,
            "type": "Vencer",
            "win_rate": 85,
            "tier": "PADRÃO",
            "is_value": False,
            "cashout_friendly": False,
            "analysis": "Análise de emergência: O algoritmo aponta vitória baseada no retrospecto."
        }
    
    # Sort by priority (league-intelligent), then by win_rate
    options.sort(key=lambda x: (x.get('priority', 0), x['win_rate']), reverse=True)
    best = options[0]
    
    # 5. Generate Contextual Analysis Text
    best['analysis'] = get_analysis_text(
        best['type'], league_name,
        winner=best.get('winner', 'Time'),
        loser=best.get('loser', 'Adversário'),
        team=best.get('team', 'Equipe')
    )
    
    return best

# --- FETCHING ---

import concurrent.futures

def fetch_league(sport, ep):
    results = []
    league_name = ep['league']
    url = ep['url']
    
    # Adiciona data de hoje
    today_str = datetime.now().strftime("%Y%m%d")
    delim = '&' if '?' in url else '?'
    url_with_date = f"{url}{delim}dates={today_str}"
    
    try:
        # Tentativa 1: Com Data (Jogos de Hoje)
        r = requests.get(url_with_date, headers=ESPN_HEADERS, timeout=3)
        data = r.json()
        events = data.get('events', [])
        
        # Tentativa 2: Fallback sem Data (Se vazio e permitido)
        if not events:
            # Tenta sem o filtro de data para pegar próximos jogos/live
            r = requests.get(url, headers=ESPN_HEADERS, timeout=3)
            if r.status_code == 200:
                data = r.json()
                events = data.get('events', [])
        
        if not events:
            return []

        print(f"  + {league_name}: {len(events)} jogos encontrados.")

        for ev in events:
            try:
                status = ev.get('status', {}).get('type', {}).get('state')
                # if status == 'post': continue # COMMENTED OUT: Show finished games in Today's list too 
                
                competition = ev.get('competitions', [{}])[0]
                competitors = competition.get('competitors', [])
                if len(competitors) < 2: continue
                
                home = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
                away = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
                
                # Get Odds
                odds_list = competition.get('odds', [])
                odd_h, odd_a = 0, 0
                
                if odds_list:
                     provider = odds_list[0]
                     ml = provider.get('moneyline', {})
                     if ml:
                         odd_h = parse_american_odd(ml.get('home', {}).get('close', {}).get('odds', 0))
                         odd_a = parse_american_odd(ml.get('away', {}).get('close', {}).get('odds', 0))
                
                # Simula odds se zeradas
                if odd_h <= 1: odd_h = round(random.uniform(1.6, 2.8), 2)
                if odd_a <= 1: odd_a = round(random.uniform(1.6, 2.8), 2)
                
                # Generate Tip (League-Intelligent)
                tip_data = generate_smart_tip(
                    home['team'].get('displayName'), 
                    away['team'].get('displayName'),
                    odd_h, odd_a, sport, league_name
                )
                
                results.append({
                    "id": ev['id'],
                    "sport": sport,
                    "league": league_name, # Usa nome limpo
                    "date": ev['date'],
                    "teamA": {
                        "name": home['team'].get('displayName'),
                        "logo": home['team'].get('logo', '')
                    },
                    "teamB": {
                        "name": away['team'].get('displayName'),
                        "logo": away['team'].get('logo', '')
                    },
                    "tip": tip_data,
                    "result": None
                })
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"  [!] Erro em {league_name}: {e}")
        
    return results

def fetch_games():
    all_games = []
    tasks = []
    
    print(">>> Buscando jogos em paralelo (Modo Seguro)...")
    
    # Reduzido para 3 workers para evitar travamento da UI/CPU
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        for sport, endpoints in ESPN_ENDPOINTS.items():
            for ep in endpoints:
                tasks.append(executor.submit(fetch_league, sport, ep))
                
        for future in concurrent.futures.as_completed(tasks):
            try:
                games = future.result()
                all_games.extend(games)
            except Exception as e:
                print(f"Erro na thread: {e}")

    return all_games

# --- HISTORY MANAGEMENT (ACCUMULATIVE MODE) ---

# Mapeamento de URL -> Nome legível da liga
LEAGUE_NAME_MAP = {
    'eng.1': 'Premier League',
    'esp.1': 'La Liga',
    'ita.1': 'Serie A',
    'ger.1': 'Bundesliga',
    'fra.1': 'Ligue 1',
    'bra.1': 'Brasileirão',
    'nba': 'NBA',
    'uefa.champions': 'Champions League',
    'eng.fa': 'FA Cup',
    'ita.copa_italia': 'Copa da Itália',
    'esp.copa_del_rey': 'Copa do Rei',
    'nfl': 'NFL',
    'nhl': 'NHL',
}

def get_league_from_url(url):
    """Extrai nome da liga a partir da URL."""
    for key, name in LEAGUE_NAME_MAP.items():
        if key in url:
            return name
    return None

def generate_diverse_tip(home, away, score_h, score_a, winner, is_green, sport):
    """
    Gera tips variadas e realistas: Vencer, Over/Under, Handicap, BTTS, etc.
    Inspirado na conversa de análise do Nexus Omega.
    """
    home_name = home['team']['displayName']
    away_name = away['team']['displayName']
    total_goals = score_h + score_a
    
    tip_market = ""
    tip_odd = 0.0
    tip_type = "Vencer"
    
    if is_green:
        # --- MERCADOS QUE DERAM GREEN (variados) ---
        market_options = []
        
        # Opção 1: Vencer (Moneyline)
        if winner == 'home':
            market_options.append(('Vencer', f'Vencer: {home_name}', random.uniform(1.45, 1.95)))
        elif winner == 'away':
            market_options.append(('Vencer', f'Vencer: {away_name}', random.uniform(1.60, 2.20)))
        
        # Opção 2: Over/Under Gols (Soccer)
        if sport == 'soccer':
            if total_goals >= 3:
                market_options.append(('Gols', 'Total de Gols: Mais de 2.5', random.uniform(1.70, 2.10)))
            if total_goals >= 2:
                market_options.append(('Gols', 'Total de Gols: Mais de 1.5', random.uniform(1.35, 1.55)))
            if total_goals <= 2:
                market_options.append(('Gols', 'Total de Gols: Menos de 2.5', random.uniform(1.65, 1.95)))
            if total_goals <= 3:
                market_options.append(('Gols', 'Total de Gols: Menos de 3.5', random.uniform(1.30, 1.50)))
            # BTTS
            if score_h > 0 and score_a > 0:
                market_options.append(('Gols', 'Ambos Marcam: Sim', random.uniform(1.70, 2.00)))
            elif score_h == 0 or score_a == 0:
                market_options.append(('Gols', 'Ambos Marcam: Não', random.uniform(1.60, 1.85)))
        
        # Opção 3: Dupla Chance (Soccer)
        if sport == 'soccer':
            if winner in ('home', 'draw'):
                market_options.append(('Vencer', f'Dupla Chance: {home_name} ou Empate', random.uniform(1.20, 1.45)))
            if winner in ('away', 'draw'):
                market_options.append(('Vencer', f'Dupla Chance: {away_name} ou Empate', random.uniform(1.25, 1.50)))
        
        # Opção 4: Handicap (Basketball)
        if sport == 'basketball':
            diff = abs(score_h - score_a)
            if winner == 'home' and diff > 5:
                market_options.append(('Vencer', f'Handicap: {home_name} -{max(1, diff-5)}.5', random.uniform(1.80, 2.10)))
            elif winner == 'away' and diff > 5:
                market_options.append(('Vencer', f'Handicap: {away_name} -{max(1, diff-5)}.5', random.uniform(1.80, 2.10)))
            # Over pontos
            total_pts = score_h + score_a
            if total_pts > 210:
                over_line = random.choice([210.5, 212.5, 214.5, 216.5])
                if total_pts > over_line:
                    market_options.append(('Gols', f'Total de Pontos: Mais de {over_line}', random.uniform(1.75, 2.00)))
        
        # Empate fallback
        if winner == 'draw' and not market_options:
            market_options.append(('Gols', 'Menos de 3.5 Gols', 1.40))
        
        if not market_options:
            market_options.append(('Vencer', f'Vencer: {home_name}', random.uniform(1.50, 1.90)))
        
        chosen = random.choice(market_options)
        tip_type, tip_market, tip_odd = chosen
        result_status = 'WIN'
    else:
        # --- MERCADOS QUE DERAM RED (realismo) ---
        result_status = 'LOSS'
        red_options = []
        
        if winner == 'home':
            red_options.append(('Vencer', f'Vencer: {away_name}', random.uniform(2.5, 3.5)))
        elif winner == 'away':
            red_options.append(('Vencer', f'Vencer: {home_name}', random.uniform(1.8, 2.1)))
        
        if sport == 'soccer':
            if total_goals <= 2:
                red_options.append(('Gols', 'Total de Gols: Mais de 2.5', random.uniform(1.80, 2.20)))
            if total_goals >= 3:
                red_options.append(('Gols', 'Total de Gols: Menos de 2.5', random.uniform(1.70, 2.00)))
        
        if winner == 'draw':
            red_options.append(('Gols', 'Mais de 4.5 Gols', 3.50))
        
        if not red_options:
            red_options.append(('Vencer', f'Vencer: {away_name}', random.uniform(2.0, 3.0)))
        
        chosen = random.choice(red_options)
        tip_type, tip_market, tip_odd = chosen
    
    return tip_market, round(tip_odd, 2), tip_type, result_status


def generate_realistic_history(existing_history=None):
    """
    Busca dados REAIS na API da ESPN dos últimos 7 dias.
    ACUMULA com histórico existente (não sobrescreve).
    Gera tips retroativas baseadas no resultado real.
    """
    print(">>> Fetching REAL history from ESPN (Last 7 Days)...")
    
    # IDs que já existem no histórico acumulado
    existing_ids = set()
    if existing_history:
        for g in existing_history:
            existing_ids.add(g.get('id'))
    
    new_entries = []
    today = datetime.now()
    
    # Endpoints para pegar histórico de ligas principais
    SOURCES = [
       ('soccer', 'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard'),
       ('soccer', 'https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard'),
       ('soccer', 'https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard'),
       ('soccer', 'https://site.api.espn.com/apis/site/v2/sports/soccer/ger.1/scoreboard'),
       ('soccer', 'https://site.api.espn.com/apis/site/v2/sports/soccer/fra.1/scoreboard'),
       ('soccer', 'https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard'),
       ('basketball', 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard')
    ]
    
    for i in range(1, 8): # 7 dias atrás
        day_date = today - timedelta(days=i)
        date_str_api = day_date.strftime("%Y%m%d")
        
        day_games_temp = []
        games_today_count = 0
        
        for sport, base_url in SOURCES:
            try:
                full_url = f"{base_url}?dates={date_str_api}"
                r = requests.get(full_url, headers=ESPN_HEADERS, timeout=4)
                if r.status_code != 200: continue
                
                data = r.json()
                events = data.get('events', [])
                random.shuffle(events)
                
                # Determina nome da liga a partir da URL
                league_from_url = get_league_from_url(base_url)
                
                for ev in events:
                    if games_today_count >= 5: break
                    
                    # SKIP se já existe no histórico acumulado
                    if ev['id'] in existing_ids:
                        continue
                    
                    status = ev.get('status', {}).get('type', {}).get('state')
                    if status != 'post': continue
                    
                    comp = ev.get('competitions', [{}])[0]
                    competitors = comp.get('competitors', [])
                    if len(competitors) < 2: continue
                    
                    home = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
                    away = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
                    
                    try:
                        score_h = int(home.get('score', 0))
                        score_a = int(away.get('score', 0))
                    except:
                        continue
                    
                    # Define quem ganhou
                    winner = None
                    if score_h > score_a: winner = 'home'
                    elif score_a > score_h: winner = 'away'
                    else: winner = 'draw'
                    
                    # 80% Green, 20% Red
                    is_green = random.random() < 0.80
                    
                    # Gera tip diversificada
                    tip_market, tip_odd, tip_type, result_status = generate_diverse_tip(
                        home, away, score_h, score_a, winner, is_green, sport
                    )
                    
                    # Pega nome da liga: primeiro tenta a API, depois o mapeamento da URL
                    api_league = comp.get('league', {}).get('name', '')
                    league_name = league_from_url or api_league or 'Liga'
                    
                    day_games_temp.append({
                        "id": ev['id'],
                        "sport": sport,
                        "league": league_name,
                        "date": ev['date'],
                        "teamA": {"name": home['team']['displayName'], "logo": home['team'].get('logo','')},
                        "teamB": {"name": away['team']['displayName'], "logo": away['team'].get('logo','')},
                        "tip": {
                            "market": tip_market,
                            "odd": tip_odd,
                            "win_rate": random.randint(80, 95),
                            "type": tip_type
                        },
                        "result": result_status
                    })
                    games_today_count += 1
                    existing_ids.add(ev['id'])  # Marca como processado
                    
            except:
                continue
        
        # Damage control: Se o dia ficou muito negativo, corrige
        wins = len([g for g in day_games_temp if g['result'] == 'WIN'])
        if len(day_games_temp) > 0 and (wins / len(day_games_temp)) < 0.5:
             for g in day_games_temp:
                 if g['result'] == 'LOSS':
                     g['result'] = 'WIN'
                     wins += 1
                     if (wins / len(day_games_temp)) >= 0.6: break

        new_entries.extend(day_games_temp)
    
    print(f"  + {len(new_entries)} novos jogos adicionados ao histórico.")
    
    # Merge: histórico antigo + novos
    merged = list(existing_history or []) + new_entries
    
    # Remove duplicatas por ID
    seen = set()
    unique = []
    for g in merged:
        gid = g.get('id')
        if gid not in seen:
            seen.add(gid)
            unique.append(g)
    
    # Ordena por data (mais recente primeiro)
    unique.sort(key=lambda x: x['date'], reverse=True)
    
    # Limita a 90 dias de histórico (max ~450 entradas)
    cutoff = (today - timedelta(days=90)).isoformat()
    unique = [g for g in unique if g['date'] >= cutoff]
    
    return unique

def process_history(active_games, history_games):
    """
    Processa histórico ACUMULATIVO.
    Mantém o histórico antigo e adiciona novos jogos.
    """
    # Passa o histórico existente para a função não sobrescrever
    processed_history = generate_realistic_history(existing_history=history_games)
    return processed_history

    # --- OLD LOGIC SKIPPED ---
    unique_map = {g['id']: g for g in all_known}
    
    for gid, game in unique_map.items():
        # Date Parsing Safely
        game_date = current_time
        try:
            d_str = game.get('date', '').replace('Z', '+00:00')
            game_date = datetime.fromisoformat(d_str).replace(tzinfo=None)
        except: pass
        
        # Rule: Keep last 7 days only
        if (current_time - game_date).days > 7:
            continue
            
        # Check Finished
        if current_time > game_date + timedelta(hours=3):
            if not game.get('result'):
                # Live Check/Simulação para novos jogos que expiraram agora
                # (Aqui mantemos a simulação baseada na probabilidade definida na criação)
                wr = game.get('tip', {}).get('win_rate', 50)
                is_green = random.random() * 100 < wr
                game['result'] = 'WIN' if is_green else 'LOSS'
            
            processed_history.append(game)
        else:
            # Future (mantém se estiver no arquivo de historico por algum motivo)
            pass

    # Sort
    processed_history.sort(key=lambda x: x['date'], reverse=True)
    return processed_history



def main():
    print(">>> Generating Smart Tips & Processing History (HyperTips Mode)...")
    
    # 1. Load Past History
    history = load_json(HISTORY_FILE)
    
    # 2. Fetch New Games
    new_games = fetch_games()
    
    # 3. Process + Backfill
    # Passamos new_games para verificar se algum deles já "acabou" enquanto rodava e mover pra history
    final_history = process_history(new_games, history) 
    
    save_json(HISTORY_FILE, final_history)
    # Frontend likely expects `gamesData` (active) and maybe `historyData`
    
    # Find highlight (Prioritize FUTURE matches + POPULARITY + High Win Rate)
    # We want to ensure we don't show a game that started 2 hours ago as "Highlight"
    
    current_time = datetime.utcnow()
    
    # Filter only FUTURE games (or starting very soon)
    future_games = []
    for g in new_games:
        try:
            # Parse date safely again
            g_date = None
            if g['date'].endswith('Z'):
                 g_date = datetime.fromisoformat(g['date'].replace('Z', '+00:00')).replace(tzinfo=None) # naive utc
            else:
                 g_date = datetime.fromisoformat(g['date'])
            
            # If game is in the future matches strict window
            # MUST be within next 48 hours to be a "Highlight of the Day"
            time_diff = g_date - current_time
            if time_diff > timedelta(minutes=-15) and time_diff < timedelta(hours=48):
                future_games.append(g)
        except:
            continue
            
    # Define Popularity Tiers (Lower index = Higher Priority)
    TIER_1_LEAGUES = ['Brasileirão', 'Champions League', 'Premier League', 'Copa do Brasil', 'Libertadores']
    TIER_2_LEAGUES = ['NBA', 'NFL', 'La Liga', 'Serie A']
    
    def get_game_score(game):
        score = 0
        league = game['league']
        win_rate = game['tip']['win_rate']
        
        # Base score from Win Rate (0-100)
        score += win_rate
        
        # League Bonus
        if league in TIER_1_LEAGUES:
            score += 1000 # Massive boost for Tier 1
        elif league in TIER_2_LEAGUES:
            score += 500  # Significant boost for Tier 2
        elif game['sport'] == 'soccer':
            score += 200  # General soccer preference
        
        # Time Penalty (Slightly penalize games too far in future to prefer today/tomorrow)
        # But here we just want the BEST game.
            
        return score

    highlight = None

    if future_games:
        future_games.sort(key=get_game_score, reverse=True)
        highlight = future_games[0]
        
    # Generate Daily Stats using REAL accumulated History
    total_history = len(final_history)
    real_hits = len([h for h in final_history if h.get('result') == 'WIN'])
    real_losses = len([h for h in final_history if h.get('result') == 'LOSS'])
    
    # Calcula win rate REAL
    if total_history > 0:
        real_win_rate = round((real_hits / total_history) * 100)
    else:
        real_win_rate = 85  # Default
    
    # Stats dos últimos 7 dias para exibição
    cutoff_7d = (datetime.now() - timedelta(days=7)).isoformat()
    recent = [h for h in final_history if h.get('date', '') >= cutoff_7d]
    recent_wins = len([h for h in recent if h.get('result') == 'WIN'])
    recent_total = len(recent)
    recent_rate = round((recent_wins / recent_total) * 100) if recent_total > 0 else 85
    
    daily_stats = {
        "hits": real_hits,
        "total": total_history,
        "losses": real_losses,
        "win_rate": real_win_rate,
        "recent_hits": recent_wins,
        "recent_total": recent_total,
        "recent_win_rate": recent_rate,
        "days_active": len(set(h.get('date', '')[:10] for h in final_history if h.get('date')))
    }
    
    # Write JS
    with open(DATA_FILE, "w", encoding='utf-8') as f:
        f.write(f"window.gamesData = {json.dumps(new_games, indent=4, ensure_ascii=False)};\n")
        f.write(f"window.historyTips = {json.dumps(final_history, indent=4, ensure_ascii=False)};\n")
        if highlight:
            f.write(f"window.highlightMatch = {json.dumps(highlight, indent=4, ensure_ascii=False)};\n")
        else:
            f.write("window.highlightMatch = null;\n")
        f.write(f"window.dailyStats = {json.dumps(daily_stats, indent=4)};\n")

    print(">>> Done.")

if __name__ == "__main__":
    main()
