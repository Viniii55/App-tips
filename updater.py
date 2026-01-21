import requests
import json
import random
import os
from datetime import datetime, timedelta

# --- CONFIG ---
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

# --- TEXT ENGINE (MODE: AGGRESSIVE) ---
ANALYSIS_TEMPLATES = {
    "Vencer": [
        "O algoritmo detectou valor ABSURDO no {winner}. A odd está desajustada.",
        "Espancamento previsto. O {winner} é superior taticamente e tecnicamente.",
        "Oportunidade de Ouro. O {loser} vem com desfalques importantes na zaga.",
        "Apostamos na consistência. O {winner} em casa é uma máquina de moer adversários.",
        "Sniper ativado: Tudo indica que o {winner} vai controlar o jogo do início ao fim."
    ],
    "Gols": [
        "Alerta de jogo frenético! As duas defesas são verdadeiras peneiras.",
        "O sistema prevê chuva de gols. O ataque do {team} está on fire!",
        "Tendência explícita de Over. Jogo com DNA ofensivo e pouca marcação.",
        "A estatística não mente: 90% dos últimos jogos bateram essa linha facilmente."
    ],
    "Escanteios": [
        "Pressão total! O {team} vai amassar o adversário na linha de fundo.",
        "O algortimo cruzou dados e identificou tendência massiva de cantos aqui.",
        "Jogo travado = Chuveirinho na área. Cenário perfeito para escanteios.",
        "Leitura de jogo: O {team} precisa do resultado e vai bombardear o gol."
    ],
    "Chutes": [
        "O craque do {team} está com fome de bola. Média de 4.5 chutes por jogo.",
        "A zaga do {loser} deixa chutar de fora da área. Vamos explorar essa falha!",
        "Volume de jogo insano esperado. O {team} não vai parar de atacar."
    ]
}

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

def generate_smart_tip(home_name, away_name, odd_h, odd_a, sport):
    """
    Gera uma tip com 'Inteligência Artificial' simulada e Agressividade.
    Probabilidade Visual MÍNIMA de 75% para gerar confiança.
    """
    
    # 1. Determine Favorite based on real/simulated odds
    favorite = home_name
    underdog = away_name
    
    if odd_a < odd_h:
        favorite = away_name
        underdog = home_name

    # 2. Logic selector (Aggressive)
    options = []
    
    # --- Market: Vencedor (Moneyline) ---
    # Só sugerimos ML se a odd for decente (< 2.50) senão é arriscado demais visualmente
    if min(odd_h, odd_a) < 2.50:
        win_rate = random.randint(81, 94) # HIGH CONFIDENCE VISUAL
        if win_rate > 90: win_rate = 90 + random.randint(0, 5) # Cap at 95ish
        
        options.append({
            "market": f"Vencer: {favorite}",
            "odd": min(odd_h, odd_a),
            "type": "Vencer",
            "winner": favorite,
            "loser": underdog,
            "team": favorite,
            "win_rate": win_rate
        })
        
    # --- Market: Gols (Over) ---
    # Futebol ama gols
    if sport == 'soccer':
        line = random.choice([1.5, 2.5])
        options.append({
            "market": f"Total de Gols: Mais de {line}",
            "odd": round(random.uniform(1.5, 1.9), 2),
            "type": "Gols",
            "team": home_name, # Generic
            "loser": away_name,
            "win_rate": random.randint(78, 92)
        })

    # --- Market: Escanteios (High Value Perception) ---
    if sport == 'soccer':
        line = random.choice([8.5, 9.5, 10.5])
        options.append({
            "market": f"Escanteios: Mais de {line}",
            "odd": round(random.uniform(1.7, 2.2), 2),
            "type": "Escanteios",
            "team": home_name,
            "loser": away_name,
            "win_rate": random.randint(82, 96) # Escanteios passa muita confiança
        })
        
    # --- Market: Chutes (Player Props Vibe) ---
    if sport == 'soccer':
        line = random.choice([7.5, 8.5, 9.5]) # Chutes totais do time
        options.append({
            "market": f"Chutes ao Gol: +{line} (Total)",
            "odd": round(random.uniform(1.6, 2.0), 2),
            "type": "Chutes",
            "team": favorite,
            "loser": underdog,
            "win_rate": random.randint(79, 89)
        })

    # Pick best option
    if not options:
        # Fallback Aggressive
        return {
            "market": f"Vencer: {favorite}",
            "odd": 1.90,
            "type": "Vencer",
            "win_rate": 88,
            "analysis": "Análise de emergência: O algoritmo aponta vitória segura baseada no retrospecto."
        }
    
    # Prioritize Higher Win Rate mostly
    options.sort(key=lambda x: x['win_rate'], reverse=True)
    best = options[0]
    
    # Generate Analysis Text & Add "Learning Context"
    templates = ANALYSIS_TEMPLATES.get(best['type'], ANALYSIS_TEMPLATES['Vencer'])
    template = random.choice(templates)
    
    base_text = template.format(
        winner=best.get('winner', 'Time'), 
        loser=best.get('loser', 'Adversário'),
        team=best.get('team', 'Equipe')
    )
    
    # Add "Artificial Intelligence" Flavor (The 'Why')
    ai_reasons = [
        " | Motivo: Defesa adversária cedeu gols nos últimos 5 jogos.",
        " | IA: Padrão tático identificado com sucesso.",
        " | Dados: A intensidade ofensiva do time triplicou no 2º tempo.",
        " | Insight: O mercado ignorou o fator casa, mas nós não.",
        " | Algoritmo: Probabilidade recalculada após as últimas notícias."
    ]
    
    best['analysis'] = base_text + random.choice(ai_reasons)
    return best

# --- FETCHING ---

def fetch_games():
    games = []
    
    for sport, endpoints in ESPN_ENDPOINTS.items():
        for ep in endpoints:
            try:
                # Force Date Filter for "Generic/Global" endpoints to ensure we get TODAY's games
                # and not just "Featured Future Games"
                url = ep['url']
                if 'scoreboard' in url:
                    # Append date param YYYYMMDD
                    today_str = datetime.now().strftime("%Y%m%d")
                    delim = '&' if '?' in url else '?'
                    url += f"{delim}dates={today_str}"
                
                print(f"Fetching {sport} - {ep['league']}...", flush=True)
                try:
                    r = requests.get(url, headers=ESPN_HEADERS, timeout=2) # 2s strict timeout
                    if r.status_code != 200:
                        print(f"  [X] Failed: Status {r.status_code}")
                        continue
                except requests.exceptions.RequestException as e:
                    print(f"  [!] Skipped {ep['league']} (Network Timeout/Error)")
                    continue

                data = r.json()
                events = data.get('events', [])
                print(f"  > Found {len(events)} events.")
                
                for ev in events:
                    try:
                        status = ev.get('status', {}).get('type', {}).get('state')
                        if status == 'post': continue # Skip finished for NEW list
                        
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
                        
                        # Generate Tip
                        tip_data = generate_smart_tip(
                            home['team'].get('displayName'), 
                            away['team'].get('displayName'),
                            odd_h, odd_a, sport
                        )
                        
                        games.append({
                            "id": ev['id'],
                            "sport": sport,
                            "league": ep['league'],
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
                            "result": None # To be filled later
                        })
                        
                    except Exception as e:
                        continue
            except:
                pass
    
    return games

# --- HISTORY MANAGEMENT ---

def process_history(active_games, history_games):
    """
    1. Identifica jogos que terminaram (estavam em active/history mas data já passou).
    2. Simula/Checa Resultado (Como nao temos API de result historico facil aqui sem id especifico, vamos SIMULAR o green/red baseado no win rate pra demo).
    3. Aplica regra: Manter Greens, Apagar 50% dos Reds.
    """
    
    current_time = datetime.utcnow()
    
    # 1. Merge lists to process status
    all_known = history_games + active_games
    processed_history = []
    
    # Map by ID to avoid duplicates
    unique_map = {g['id']: g for g in all_known}
    
    for gid, game in unique_map.items():
        # Check if game finished (Date + 3 hours)
        # Robust Date Parsing
        game_date = None
        date_str = game.get('date', '')
        
        formats = ["%Y-%m-%dT%H:%MZ", "%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"]
        for fmt in formats:
            try:
                game_date = datetime.strptime(date_str, fmt)
                break
            except ValueError:
                continue
        
        if not game_date:
            # Se falhar tudo, tenta ignorar 'Z' manual se existir
            try:
                if date_str.endswith('Z'):
                    game_date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    game_date = datetime.fromisoformat(date_str)
            except:
                pass

        if not game_date:
            # Fallback total: assume futuro pra não deletar por erro
            game_date = current_time + timedelta(days=365)

        if current_time > game_date + timedelta(hours=3):
            # Game Finished logic
            if not game.get('result'):
                # SIMULA RESULTADO (Se win_rate > 70, grande chance de Green)
                # Na vida real: check API score
                # Se tiver win_rate, usa. Se não, random.
                wr = game.get('tip', {}).get('win_rate', 50)
                is_green = random.random() * 100 < (wr + 5) 
                game['result'] = 'WIN' if is_green else 'LOSS'
            
            # Filter Logic
            if game['result'] == 'WIN':
                processed_history.append(game)
            else:
                # É LOSS: Delete 50% logic
                if random.random() > 0.5:
                    processed_history.append(game)
        else:
            # Future game: ignore for history file, kept in active usually
            # Mas se ele estava no history e ainda é futuro (raro), mantem
            pass

    return processed_history

def main():
    print(">>> Generating Smart Tips & Processing History...")
    
    # 1. Load Past History
    history = load_json(HISTORY_FILE)
    
    # 2. Fetch New Games
    new_games = fetch_games()
    
    # 3. Process History (Resolve past games from History + New inputs that might have aged)
    # Note: fetch_games gets future games. History has old games.
    # We update history with the settled ones.
    
    final_history = process_history([], history) # Processa apenas o histórico existente pra limpar
    
    # Adicionamos logicamente os jogos que acabaram de sair da lista "new_games" se rodarmos isso frequentemente,
    # mas por simplificacao, vamos assumir que o usuario roda isso 1x dia.
    # Vamos salvar o historico limpo.
    
    save_json(HISTORY_FILE, final_history)
    
    # 4. Save Active Data (New Games + History for frontend display?)
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
        
    # Generate Daily Stats using History


    real_hits = len([h for h in final_history if h.get('result') == 'WIN'])
    
    # Cap hits to look realistic (12-28 range looks organic)
    display_hits = real_hits
    if display_hits > 28:
        display_hits = random.randint(14, 28)
    if display_hits < 5:
        display_hits = random.randint(5, 12) # Cold start boost

    daily_stats = {
        "hits": display_hits,
        "win_rate": 87 # Fixed marketing number or calculated
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
