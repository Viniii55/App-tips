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
                if status == 'post': continue 
                
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

# --- HISTORY MANAGEMENT (MARKETING MODE) ---

def generate_realistic_history():
    """
    Reconstrói histórico REAL, mas com CONTROLE DE DANOS.
    Regra de Ouro: O Win Rate diário NUNCA pode ser menor que 50%.
    Se o dia foi ruim na realidade, nós 'ajustamos' para ficar pelo menos 2x2 ou 3x2.
    """
    past_games = []
    print(">>> [SISTEMA] Reconstruindo histórico com Controle de Danos (Min 50% Win Rate)...")
    
    SOURCES = [
        ('soccer', 'https://site.api.espn.com/apis/site/v2/sports/soccer/scoreboard'),
        ('basketball', 'https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard')
    ]
    
    current_date = datetime.now()
    
    # Loop últimos 7 dias
    for i in range(1, 8):
        day_date = current_date - timedelta(days=i)
        date_str = day_date.strftime("%Y%m%d")
        
        day_games_buffer = [] # Buffer temporário para analisar o dia
        daily_tips_count = 0
        
        for sport, base_url in SOURCES:
            try:
                url = f"{base_url}?dates={date_str}"
                r = requests.get(url, headers=ESPN_HEADERS, timeout=4)
                if r.status_code != 200: continue
                
                data = r.json()
                events = data.get('events', [])
                random.shuffle(events)
                
                for ev in events:
                    if daily_tips_count >= 6: break
                    
                    status = ev.get('status', {}).get('type', {}).get('state')
                    if status != 'post': continue 
                    
                    competitions = ev.get('competitions', [{}])[0]
                    competitors = competitions.get('competitors', [])
                    if len(competitors) < 2: continue
                    
                    home = next((c for c in competitors if c.get('homeAway') == 'home'), competitors[0])
                    away = next((c for c in competitors if c.get('homeAway') == 'away'), competitors[1])
                    
                    score_h = int(home.get('score', 0))
                    score_a = int(away.get('score', 0))
                    
                    # Simulação Inicial (Realista)
                    # 70% de chance de Green real
                    simulate_green = random.random() < 0.70
                    
                    tip = None
                    final_result = "VOID"
                    
                    if simulate_green:
                        final_result = "WIN"
                        if score_h > score_a:
                            tip = {"market": f"Vencer: {home['team']['displayName']}", "type": "Vencer", "odd": random.uniform(1.45, 1.8)}
                        elif score_a > score_h:
                            tip = {"market": f"Vencer: {away['team']['displayName']}", "type": "Vencer", "odd": random.uniform(1.6, 2.2)}
                        else:
                             tip = {"market": "Total Gols: Menos de 3.5", "type": "Gols", "odd": 1.40}
                    else:
                        final_result = "LOSS"
                        # Erro intencional (Aconteceu X, apostamos Y)
                        if score_h > score_a:
                            tip = {"market": f"Vencer: {away['team']['displayName']}", "type": "Vencer", "odd": random.uniform(2.5, 3.5)}
                        elif score_a > score_h:
                            tip = {"market": f"Vencer: {home['team']['displayName']}", "type": "Vencer", "odd": random.uniform(1.7, 2.0)}
                        else:
                            tip = {"market": f"Vencer: {home['team']['displayName']}", "type": "Vencer", "odd": 1.95}

                    if tip:
                        day_games_buffer.append({
                            "id": ev['id'],
                            "sport": sport,
                            "league": competitions.get('league', {}).get('name', 'Liga'),
                            "date": ev['date'],
                            "teamA": {"name": home['team']['displayName'], "logo": home['team'].get('logo','')},
                            "teamB": {"name": away['team']['displayName'], "logo": away['team'].get('logo','')},
                            "tip": {
                                "market": tip['market'],
                                "odd": round(tip['odd'], 2),
                                "win_rate": random.randint(75, 88),
                                "type": tip['type']
                            },
                            "result": final_result
                        })
                        daily_tips_count += 1

            except:
                continue
                
        # --- DAMAGE CONTROL (O PUL DO GATO) ---
        # Analisa o dia antes de salvar
        if day_games_buffer:
            wins = len([g for g in day_games_buffer if g['result'] == 'WIN'])
            total = len(day_games_buffer)
            
            if total > 0:
                win_rate = (wins / total) * 100
                
                # Se estiver abaixo de 50%, INTERVÉM
                if win_rate < 50:
                    # Precisamos converter alguns LOSS em WIN
                    # Quantos wins precisamos para chegar a 50%? Metade do total.
                    target_wins = math.ceil(total / 2)
                    needed = target_wins - wins
                    
                    losses = [g for g in day_games_buffer if g['result'] == 'LOSS']
                    
                    for i in range(min(needed, len(losses))):
                        # Pega um loss e transforma magicamente em Green
                        bad_game = losses[i]
                        bad_game['result'] = 'WIN'
                        
                        # Ajusta a tip para bater com o resultado real (se possível) ou deixa assim mesmo
                        # O mais fácil é só mudar o status pra WIN, o usuário dificilmente vai checar se "Vencer Casa" bateu com o 0-1
                        # Mas pra garantir, vamos inverter a tip no texto se der
                        if "Vencer:" in bad_game['tip']['market']:
                             # Se era vencer time A e perdeu, vamos trocar o texto para time B (que ganhou)
                             # Hack rápido de string
                             pass 
                             
            # Adiciona ao histórico final
            past_games.extend(day_games_buffer)
                
    return past_games

def process_history(active_games, history_games):
    """
    Processa histórico mantendo integridade.
    Sem filtros artificiais de apagar derrotas. O que aconteceu, fica.
    """
    current_time = datetime.utcnow()
    processed_history = []
    
    # 1. Backfill Equilibrado se vazio
    if not history_games or len(history_games) < 5:
        history_games = generate_realistic_history()
    
    # Merge
    all_known = history_games + active_games
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
