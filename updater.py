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
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/bra.1/scoreboard', 'league': 'Brasileirão'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/eng.1/scoreboard', 'league': 'Premier League'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/esp.1/scoreboard', 'league': 'La Liga'},
        {'url': 'https://site.api.espn.com/apis/site/v2/sports/soccer/ita.1/scoreboard', 'league': 'Serie A'},
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
    ]
}

# --- TEXT ENGINE ---
ANALYSIS_TEMPLATES = {
    "Vencer": [
        "O {winner} vem de uma sequência forte de vitórias e domina o confronto direto.",
        "A fase do {winner} é superior, com ataque eficiente nos últimos 5 jogos.",
        "Jogado em casa, o {winner} tem aproveitamento de 80% na temporada.",
        "A defesa do {loser} tem falhado consistentemente, favorecendo o {winner}."
    ],
    "Gols": [
        "Ambos os times possuem ataques agressivos, tendência alta de gols.",
        "A média de gols nos confrontos entre estas equipes é superior a 3.",
        "O {team} tem um dos melhores ataques do campeonato, promessa de jogo aberto."
    ],
    "Escanteios": [
        "O {team} tem média de 7 escanteios por jogo quando joga em casa.",
        "Jogo com tendência de pressão nas laterais, favorecendo escanteios.",
        "Historicamente, confrontos entre estes times superam a linha de cantos."
    ],
    "Chutes": [
        "O atacante do {team} tem média de 3.5 chutes certos por partida.",
        "A defesa do {loser} permite muitos chutes de longa distância.",
        "Jogo aberto deve proporcionar muitas finalizações para ambos os lados."
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
    Gera uma tip mais elaborada: Vencedor, Gols, Escanteios ou Chutes.
    """
    options = []
    
    # 1. Match Winner (Base)
    if odd_h > 0 and odd_a > 0:
        if odd_h < odd_a and odd_h < 1.90:
            options.append({
                "market": f"Vencer: {home_name}",
                "odd": odd_h,
                "type": "Vencer",
                "winner": home_name,
                "loser": away_name,
                "win_rate": calculate_win_rate(odd_h)
            })
        elif odd_a < odd_h and odd_a < 1.90:
            options.append({
                "market": f"Vencer: {away_name}",
                "odd": odd_a,
                "type": "Vencer",
                "winner": away_name,
                "loser": home_name,
                "win_rate": calculate_win_rate(odd_a)
            })
    
    # 2. Goals (Simulated based on odds tightness)
    if sport == 'soccer':
        # Se odds próximas, jogo disputado -> Over gols ou BTTS
        if abs(odd_h - odd_a) < 1.0:
            options.append({
                "market": "Total de Gols: Mais de 2.5",
                "odd": round(random.uniform(1.7, 2.1), 2),
                "type": "Gols",
                "team": home_name, # Placeholder for template
                "win_rate": random.randint(55, 75)
            })
            options.append({
                "market": "Ambos Marcam: Sim",
                "odd": round(random.uniform(1.6, 1.95), 2),
                "type": "Gols",
                "team": away_name,
                "win_rate": random.randint(58, 72)
            })
        
        # 3. Corners (Simulated - "Escanteios")
        # Randomly add corner tips for variety
        if random.random() > 0.6:
            line = random.choice([8.5, 9.5, 10.5])
            options.append({
                "market": f"Escanteios: Mais de {line}",
                "odd": round(random.uniform(1.5, 1.9), 2),
                "type": "Escanteios",
                "team": home_name if odd_h < odd_a else away_name,
                "win_rate": random.randint(60, 80)
            })

        # 4. Shots (Simulated - "Chutes")
        if random.random() > 0.7:
             line = random.choice([7.5, 8.5, 9.5]) # Chutes totais ou times
             options.append({
                "market": f"Chutes ao Gol: +{line} (Total)",
                "odd": round(random.uniform(1.6, 2.0), 2),
                "type": "Chutes",
                "team": home_name if odd_h < odd_a else away_name,
                "loser": away_name,
                "win_rate": random.randint(55, 78)
            })

    # Pick best option (highest winrate or random weighted)
    if not options:
        # Fallback
        return {
            "market": f"Vencer: {home_name}",
            "odd": 1.90,
            "win_rate": 50,
            "analysis": "Jogo equilibrado, mas o fator casa deve prevalecer."
        }
    
    # Sort by Win Rate and pick top
    options.sort(key=lambda x: x['win_rate'], reverse=True)
    best = options[0]
    
    # Generate Analysis Text
    templates = ANALYSIS_TEMPLATES.get(best['type'], ANALYSIS_TEMPLATES['Vencer'])
    template = random.choice(templates)
    
    analysis_text = template.format(
        winner=best.get('winner', 'Time'), 
        loser=best.get('loser', 'Adversário'),
        team=best.get('team', 'Equipe')
    )
    
    best['analysis'] = analysis_text
    return best

# --- FETCHING ---

def fetch_games():
    games = []
    
    for sport, endpoints in ESPN_ENDPOINTS.items():
        for ep in endpoints:
            try:
                r = requests.get(ep['url'], headers=ESPN_HEADERS, timeout=5)
                data = r.json()
                events = data.get('events', [])
                
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
    
    # Find highlight
    highlights = [g for g in new_games if g['tip']['win_rate'] >= 80]
    highlight = highlights[0] if highlights else (new_games[0] if new_games else None)
    
    daily_stats = {
        "hits": len([h for h in final_history if h.get('result') == 'WIN']),
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
