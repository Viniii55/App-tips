import time
import os
import sys
from datetime import datetime
from updater import fetch_games

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    print("""
    ╔══════════════════════════════════════════════════╗
    ║        SUPERTIPS AI - AUTO MONITOR V2.0          ║
    ║        Monitorando Mercados Globais...           ║
    ╠══════════════════════════════════════════════════╣
    ║  [Status] : ONLINE                               ║
    ║  [Mode]   : HIGH FREQUENCY SCANNING              ║
    ║  [Update] : Cada 10 Minutos                      ║
    ╚══════════════════════════════════════════════════╝
    """)

def run_robot():
    cycle_count = 1
    
    while True:
        clear_screen()
        print_banner()
        
        current_time = datetime.now().strftime("%H:%M:%S")
        print(f"\n>>> INICIANDO CICLO #{cycle_count} | Hora: {current_time}")
        print(">>> Conectando aos satélites de odds...")
        
        try:
            # Chama a função principal do seu script updater.py
            fetch_games()
            
            print(f"\n[SUCESSO] Base de dados sincronizada com sucesso.")
            print(f"[NEXT] Próxima atualização em 10 minutos.")
            print("Pressione Ctrl+C para encerrar o robô.")
            
        except Exception as e:
            print(f"\n[ERRO CRÍTICO] Falha no ciclo: {e}")
        
        # Countdown visual (simples)
        # Espera 600 segundos (10 minutos)
        try:
            time.sleep(600)
            cycle_count += 1
        except KeyboardInterrupt:
            print("\n\n>>> ROBÔ DESLIGADO PELO USUÁRIO. Até mais!")
            sys.exit()

if __name__ == "__main__":
    run_robot()
