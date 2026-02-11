// --- FUNCTION: Show Super Odds View ---
window.showSuperOdds = function () {
    // Remove active class from tabs
    dom.tabs.forEach(t => t.classList.remove('active'));

    // Set state
    state.activeFilter = 'superodds';

    // Render
    renderFeed();

    // Scroll to feed
    if (dom.feed) dom.feed.scrollIntoView({ behavior: 'smooth' });
}

// Global scope for History as well
window.showHistory = function () {
    dom.tabs.forEach(t => t.classList.remove('active'));
    state.activeFilter = 'history';
    renderFeed();
    if (dom.feed) dom.feed.scrollIntoView({ behavior: 'smooth' });
}
// ProTips Hub Logic
// --- PWA & INSTALL LOGIC ---
let deferredPrompt;

// Register SW
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('sw.js').then(reg => console.log('SW Reg', reg));
    });
}

// Capture Install Prompt
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    console.log('Install Prompt CAUGHT');
});

// --- DRAG SCROLL FOR DESKTOP ---
function enableDragScroll(selector) {
    const el = document.querySelector(selector);
    if (!el) return;
    let isDown = false;
    let startX;
    let scrollLeft;
    el.addEventListener('mousedown', (e) => {
        isDown = true;
        el.style.cursor = 'grabbing';
        startX = e.pageX - el.offsetLeft;
        scrollLeft = el.scrollLeft;
    });
    el.addEventListener('mouseleave', () => { isDown = false; el.style.cursor = 'grab'; });
    el.addEventListener('mouseup', () => { isDown = false; el.style.cursor = 'grab'; });
    el.addEventListener('mousemove', (e) => {
        if (!isDown) return;
        e.preventDefault();
        const x = e.pageX - el.offsetLeft;
        const walk = (x - startX) * 2;
        el.scrollLeft = scrollLeft - walk;
    });
    el.style.cursor = 'grab';
}

// Global App Init
document.addEventListener('DOMContentLoaded', () => {
    initFilters();

    // Enable Drag
    enableDragScroll('.banners-carousel');
    enableDragScroll('.sports-nav');

    // ... Bell Button Logic ...
    const installBtn = document.querySelector('.btn-icon'); // Bell Icon
    if (installBtn) {
        installBtn.addEventListener('click', () => {

            // 1. If Native Prompt available (Android mostly)
            if (deferredPrompt) {
                deferredPrompt.prompt();
                deferredPrompt.userChoice.then((choiceResult) => {
                    if (choiceResult.outcome === 'accepted') {
                        console.log('User accepted install');
                    }
                    deferredPrompt = null;
                });
                return;
            }

            // 2. If iOS or Manual mode needed
            const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent) && !window.MSStream;
            const modal = document.getElementById('install-modal');
            const instructions = document.getElementById('install-instructions');

            if (modal) {
                if (isIOS) {
                    instructions.innerHTML = `
                        Para instalar no iPhone:<br><br>
                        1. Toque no botão <strong>Compartilhar</strong> (quadrado com seta) abaixo.<br>
                        2. Role para cima e toque em <strong>"Adicionar à Tela de Início"</strong>.
                    `;
                } else {
                    instructions.innerHTML = `
                        Para instalar o App:<br><br>
                        1. Toque no menu do navegador (três pontos).<br>
                        2. Selecione <strong>"Instalar aplicativo"</strong> ou <strong>"Adicionar à tela inicial"</strong>.
                    `;
                }
                modal.classList.remove('hidden');
            }
        });
    }
});
// ----------------------------

const state = {
    activeFilter: 'all',
    superodds: [],
    affiliateLink: "https://brsuperbet.com/registro_4903",
    dateFormat: new Intl.DateTimeFormat('pt-BR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long'
    }),
    isVerified: localStorage.getItem('platform_verified') === 'true', // Persistência básica
    matchData: []
};

// DOM Elements
const dom = {
    feed: document.getElementById('games-feed'),
    tabs: document.querySelectorAll('.nav-icon-item'),    // Onboarding Elements
    onboardingModal: document.getElementById('onboarding-modal'),
    check18: document.getElementById('check-18'),
    checkTerms: document.getElementById('check-terms'),
    btnFinishOnboarding: document.getElementById('btn-finish-onboarding'),
    btnCreateAccount: document.getElementById('btn-create-account-onboarding'),
    highlightCard: document.getElementById('highlight-card'),
    parlayCard: document.getElementById('parlay-card'),
    parlayItems: document.getElementById('parlay-items-container'),
    parlayOdd: document.getElementById('parlay-total-odd')
};

function initFilters() {
    dom.tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            // Remove active class
            dom.tabs.forEach(t => t.classList.remove('active'));
            // Add active (Encontra o elemento pai .nav-icon-item se clicou no filho)
            const target = e.target.closest('.nav-icon-item');
            if (target) {
                target.classList.add('active');
                // Update State
                state.activeFilter = target.dataset.sport;
                // Rerender
                renderFeed();
            }
        });
    });
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    // Check if onboarding is done
    const onboarded = localStorage.getItem('protips_onboarding_v2');
    if (!onboarded) {
        if (dom.onboardingModal) {
            dom.onboardingModal.classList.remove('hidden');
            setupOnboarding();
        }
    } else {
        state.isVerified = true;
    }

    if (window.gamesData) {
        state.matchData = window.gamesData;
    } else if (window.LIVE_GAMES) {
        state.matchData = window.LIVE_GAMES;
    } else {
        state.matchData = [];
    }

    // --- NORMALIZAÇÃO DE DADOS (Blindagem 100M) ---
    // Garante que chaves antigas ('football') virem 'soccer' para bater com o filtro
    if (state.matchData && state.matchData.length > 0) {
        state.matchData.forEach(m => {
            if (m.sport === 'football') m.sport = 'soccer';
            if (m.sport === 'hockey') m.sport = 'ice_hockey';
        });
        renderHighlight();
    }

    // --- RENDER STATS (Placar de Confiança) ---
    renderStats();

    initFilters();
    renderFeed();

    // --- INTERSTITIAL LOGIC (TRAVA DE SEGURANÇA) ---
    const betReminderModal = document.getElementById('bet-reminder-modal');
    const btnConfirmBet = document.getElementById('btn-confirm-bet');
    const btnCancelBet = document.getElementById('btn-cancel-bet');
    let pendingAffiliateLink = null;

    if (betReminderModal && btnConfirmBet && btnCancelBet) {
        // Delegação de evento para pegar cliques em QUALQUER botão de aposta dinâmico
        document.addEventListener('click', (e) => {
            // Verifica se clicou num botão de aposta (mas não nos botões do próprio modal ou onboarding)
            const btn = e.target.closest('.btn-action, .card-header-cta, .odd-button');

            if (btn) {
                // Check if it's already an internal modal action
                if (btn.id === 'btn-confirm-bet' || btn.id === 'btn-cancel-bet' || btn.id === 'btn-finish-onboarding') return;

                // Se estiver no onboarding, não mostra o lembrete de aposta
                if (e.target.closest('#onboarding-modal')) return;

                e.preventDefault(); // PARE!

                // Salva os dados do jogo para copiar ao confirmar
                const gameCard = e.target.closest('.game-card, .parlay-card');
                if (gameCard && gameCard.dataset.match) {
                    try {
                        window.pendingMatchToCopy = JSON.parse(gameCard.dataset.match);
                    } catch (err) { console.error("Erro ao ler dados do jogo"); }
                }

                // Pega o link original
                pendingAffiliateLink = btn.href || state.affiliateLink;

                // Mostra o alerta
                betReminderModal.classList.remove('hidden');
            }
        });

        // Ação Confirmar
        btnConfirmBet.addEventListener('click', () => {
            betReminderModal.classList.add('hidden');
            if (pendingAffiliateLink) {
                // Se tivermos dados de aposta pendentes, copia antes de abrir
                if (window.pendingMatchToCopy) {
                    window.copySingleTip(window.pendingMatchToCopy);
                    // Pequeno delay para garantir o copy antes do redirect se for mesma aba (mas aqui é _blank)
                    setTimeout(() => {
                        window.open(pendingAffiliateLink, '_blank');
                        window.pendingMatchToCopy = null;
                    }, 100);
                } else {
                    window.open(pendingAffiliateLink, '_blank');
                }
            }
        });

        // Ação Cancelar
        btnCancelBet.addEventListener('click', () => {
            betReminderModal.classList.add('hidden');
        });
    }

});

function setupOnboarding() {
    if (!dom.btnCreateAccount || !dom.btnFinishOnboarding) return;

    // Logic: Enable BOTH buttons only if checks are valid
    function checkValidity() {
        if (dom.check18.checked && dom.checkTerms.checked) {
            // Habilita Botão Finalizar
            dom.btnFinishOnboarding.removeAttribute('disabled');
            dom.btnFinishOnboarding.style.color = '#333';
            dom.btnFinishOnboarding.style.cursor = 'pointer';

            // Habilita Botão Criar Conta
            dom.btnCreateAccount.style.pointerEvents = 'auto';
            dom.btnCreateAccount.style.opacity = '1';
        } else {
            // Desabilita Botão Finalizar
            dom.btnFinishOnboarding.setAttribute('disabled', 'true');
            dom.btnFinishOnboarding.style.color = '#ccc';
            dom.btnFinishOnboarding.style.cursor = 'not-allowed';

            // Desabilita Botão Criar Conta
            dom.btnCreateAccount.style.pointerEvents = 'none';
            dom.btnCreateAccount.style.opacity = '0.5';
        }
    }

    // Estado Inicial: Forçar bloqueio ao carregar
    dom.btnCreateAccount.style.pointerEvents = 'none';
    dom.btnCreateAccount.style.opacity = '0.5';

    if (dom.check18) dom.check18.addEventListener('change', checkValidity);
    if (dom.checkTerms) dom.checkTerms.addEventListener('change', checkValidity);

    // Setup Affiliate Link on the Big Button
    dom.btnCreateAccount.href = state.affiliateLink;

    // Finish Action (Close Modal)
    dom.btnFinishOnboarding.addEventListener('click', () => {
        localStorage.setItem('protips_onboarding_v2', 'true');
        dom.onboardingModal.classList.add('hidden');
        state.isVerified = true;
        renderFeed();
    });
}

// --- FUNCTION: Render "Múltiplas Populares" Combo Card ---
// --- FUNCTION: Render "Múltiplas Populares" Combo Card ---
// Replaces the original renderHighlight with the new Parlay Card logic
// --- FUNCTION: Render "Destaque do Dia" ---
function renderHighlight() {
    const card = dom.highlightCard;
    if (!card) return;

    const match = window.highlightMatch;

    // Se não tiver destaque, esconde
    if (!match) {
        card.classList.add('hidden');
        return;
    }

    // Se tiver, mostra e preenche
    card.classList.remove('hidden');
    card.style.display = 'block';

    const content = document.getElementById('highlight-content');
    if (!content) return;

    // Formata Data
    const dateObj = new Date(match.date);
    const timeStr = dateObj.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });

    content.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:15px;">
            
            <!-- Times -->
            <div style="display:flex; justify-content:space-between; align-items:center; padding:0 10px;">
                <div style="display:flex; flex-direction:column; align-items:center; gap:5px; width:30%;">
                    <img src="${match.teamA.logo}" style="width:50px; height:50px; object-fit:contain;">
                    <span style="font-size:0.8rem; font-weight:700; color:#333; text-align:center; line-height:1.2;">${match.teamA.name}</span>
                </div>

                <div style="font-size:1.5rem; font-weight:900; color:#ddd;">VS</div>

                <div style="display:flex; flex-direction:column; align-items:center; gap:5px; width:30%;">
                    <img src="${match.teamB.logo}" style="width:50px; height:50px; object-fit:contain;">
                    <span style="font-size:0.8rem; font-weight:700; color:#333; text-align:center; line-height:1.2;">${match.teamB.name}</span>
                </div>
            </div>

            <!-- Tip Box -->
            <div style="background:#f8f9fa; border:1px dashed #e90029; border-radius:8px; padding:12px;">
                <div style="font-size:0.75rem; color:#666; margin-bottom:5px;">${match.league} • ${timeStr}</div>
                <div style="font-size:0.9rem; font-weight:700; color:#e90029; margin-bottom:5px;">${match.tip.market}</div>
                
                 <div style="display:flex; align-items:center; justify-content:center; gap:10px;">
                    <span style="color:#2ecc71; font-weight:900; font-size:1.1rem;">${match.tip.win_rate}% Probabilidade</span>
                </div>
            </div>

            <!-- Botão -->
            <a href="${state.affiliateLink}" target="_blank" class="btn-action">
                APOSTAR AGORA 🚀
            </a>
        </div>
    `;

    // Atribui os dados do jogo para o destaque também copiar
    card.dataset.match = JSON.stringify(match);
}

// Override (Ensure it runs)
window.renderHighlight = renderHighlight;

function copySingleTip(matchIndex) {
    // Acha o match pelo ID ou Index (simplificado aqui passamos o objeto direto no onclick se possivel, mas stringify é ruim)
    // Vamos reconstruir no frontend
    // Implementação simplificada:
    alert("Código copiado! (Simulação)");
}

function getSportIcon(sportKey) {
    const icons = {
        'soccer': '⚽',
        'football': '⚽', // Fallback
        'basketball': '🏀',
        'tennis': '🎾',
        'mma': '🥊',
        'american_football': '🏈',
        'ice_hockey': '🏒',
        'hockey': '🏒', // Fallback
        'default': '📅'
    };
    return icons[sportKey] || icons['default'];
}

// --- GLOBAL EXPORTS ---
window.showSuperOdds = function () {
    dom.tabs.forEach(t => t.classList.remove('active'));
    state.activeFilter = 'superodds';
    renderFeed();
    if (dom.feed) dom.feed.scrollIntoView({ behavior: 'smooth' });
}

// --- FUNÇÃO DE RENDERIZAÇÃO AGRUPADA POR LIGA ---
// --- FUNÇÃO DE RENDERIZAÇÃO AGRUPADA POR LIGA ---
function renderFeed(filterSport) {
    try {
        const currentFilter = filterSport || state.activeFilter;
        const container = dom.feed;
        if (!container) return;

        // --- UPDATE SECTION TITLE ---
        const titleEl = document.getElementById('feed-title');
        if (titleEl) {
            if (currentFilter === 'history') {
                titleEl.textContent = 'Histórico Diário 📜';
            } else {
                titleEl.textContent = 'Jogos de HOJE 🔥';
            }
        }

        container.innerHTML = '';

        // --- HISTORY VIEW (LAST 7 DAYS) ---
        if (currentFilter === 'history') {
            const historyData = window.historyTips || [];

            // 1. Render Filters
            const filterContainer = document.createElement('div');
            filterContainer.style.cssText = `
                display: flex; gap: 8px; padding-bottom: 15px; overflow-x: auto;
                margin-bottom: 10px; scrollbar-width: none;
             `;

            // Default state if undefined
            if (!state.historyFilter) state.historyFilter = 'all';

            const sports = [
                { id: 'all', label: 'Tudo', icon: '🔥' },
                { id: 'soccer', label: 'Futebol', icon: '⚽' },
                { id: 'basketball', label: 'Basquete', icon: '🏀' }
            ];

            sports.forEach(s => {
                const isActive = state.historyFilter === s.id;
                const btn = document.createElement('button');
                btn.innerHTML = `${s.icon} ${s.label}`;

                // Style Logic
                const activeStyle = `background: #002b5c; color: white; border-color: #002b5c; box-shadow: 0 2px 5px rgba(0,43,92,0.2);`;
                const inactiveStyle = `background: white; color: #555; border-color: #eee;`;

                btn.style.cssText = `
                    border: 1px solid; padding: 8px 16px; border-radius: 20px; 
                    font-size: 0.8rem; font-weight: 700; cursor: pointer; white-space: nowrap;
                    ${isActive ? activeStyle : inactiveStyle}
                `;

                btn.onclick = () => {
                    state.historyFilter = s.id;
                    renderFeed('history');
                };

                filterContainer.appendChild(btn);
            });

            container.appendChild(filterContainer);

            // 2. Filter Data
            let filteredHistory = historyData;
            if (state.historyFilter !== 'all') {
                filteredHistory = historyData.filter(m => m.sport === state.historyFilter);
            }



            // Group by Date
            const grouped = {};

            filteredHistory.forEach(match => {
                try {
                    const d = new Date(match.date);
                    // Key: YYYY-MM-DD
                    const key = d.toISOString().split('T')[0];
                    if (!grouped[key]) grouped[key] = [];
                    grouped[key].push(match);
                } catch (e) { }
            });

            const dates = Object.keys(grouped).sort().reverse(); // Newest first

            if (dates.length === 0) {
                container.innerHTML += `<div style="text-align:center; padding:40px; color:#999; font-style:italic;">
                    Nenhum resultado de ${state.historyFilter === 'all' ? 'jogos' : state.historyFilter} encontrado.
                </div>`;
                return;
            }

            // --- OVERALL STATS SUMMARY BANNER ---
            const totalWins = filteredHistory.filter(g => g.result === 'WIN').length;
            const totalGames = filteredHistory.length;
            const overallRate = totalGames > 0 ? Math.round((totalWins / totalGames) * 100) : 0;

            // Calculate current win streak
            let streak = 0;
            const sortedHistory = [...filteredHistory].sort((a, b) => new Date(b.date) - new Date(a.date));
            for (const g of sortedHistory) {
                if (g.result === 'WIN') streak++;
                else break;
            }

            const summaryBanner = document.createElement('div');
            summaryBanner.style.cssText = `
                background: linear-gradient(135deg, #002b5c 0%, #004085 100%);
                color: white; border-radius: 10px; padding: 15px;
                margin-bottom: 15px; display: flex; justify-content: space-around;
                text-align: center; box-shadow: 0 3px 10px rgba(0,43,92,0.2);
            `;
            summaryBanner.innerHTML = `
                <div>
                    <div style="font-size:0.6rem; opacity:0.7; text-transform:uppercase;">Greens</div>
                    <div style="font-size:1.3rem; font-weight:900; color:#2ecc71;">${totalWins}</div>
                </div>
                <div>
                    <div style="font-size:0.6rem; opacity:0.7; text-transform:uppercase;">Win Rate</div>
                    <div style="font-size:1.3rem; font-weight:900; color:#ff5e00;">${overallRate}%</div>
                </div>
                <div>
                    <div style="font-size:0.6rem; opacity:0.7; text-transform:uppercase;">Sequência</div>
                    <div style="font-size:1.3rem; font-weight:900; color:#f1c40f;">${streak > 0 ? '🔥' + streak : '-'}</div>
                </div>
                <div>
                    <div style="font-size:0.6rem; opacity:0.7; text-transform:uppercase;">Total</div>
                    <div style="font-size:1.3rem; font-weight:900;">${totalGames}</div>
                </div>
            `;
            container.appendChild(summaryBanner);

            // Render Groups
            dates.forEach(dateKey => {
                const dayGames = grouped[dateKey];

                // Formata Data Legível (Hoje, Ontem, etc)
                const d = new Date(dateKey);
                // Ajuste de fuso para exibir dia correto
                d.setMinutes(d.getMinutes() + d.getTimezoneOffset());

                const now = new Date();
                now.setHours(0, 0, 0, 0);

                // Diff in days
                const diffTime = Math.abs(now - d);
                const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

                let label = d.toLocaleDateString('pt-BR');
                if (diffDays === 0) label = "Hoje 🟢";
                else if (diffDays === 1) label = "Ontem";

                // Header do Dia
                const groupHeader = document.createElement('div');
                groupHeader.style.cssText = `
                    background: #f1f3f5; color: #555; font-weight: 800; font-size: 0.85rem;
                    padding: 8px 15px; border-radius: 6px; margin: 15px 0 10px 0;
                    display: flex; justify-content: space-between; align-items: center;
                `;

                // Calculate Win Rate for this day
                const wins = dayGames.filter(g => g.result === 'WIN').length;
                const total = dayGames.length;
                const dailyRate = total > 0 ? Math.round((wins / total) * 100) : 0;

                // Visual performance bar
                const barWidth = dailyRate;
                const barColor = dailyRate >= 80 ? '#2ecc71' : dailyRate >= 60 ? '#f39c12' : '#e74c3c';

                groupHeader.innerHTML = `
                    <span>📅 ${label}</span>
                    <div style="display:flex; align-items:center; gap:8px;">
                        <div style="width:40px; height:4px; background:#e0e0e0; border-radius:2px; overflow:hidden;">
                            <div style="width:${barWidth}%; height:100%; background:${barColor}; border-radius:2px;"></div>
                        </div>
                        <span style="color:${dailyRate >= 80 ? '#2ecc71' : '#666'}; font-size:0.8rem;">${wins}/${total}</span>
                    </div>
                `;

                container.appendChild(groupHeader);

                // Render Games
                dayGames.forEach(match => {
                    container.appendChild(createHistoryRow(match));
                });
            });

            // Hide Highlight on History Tab
            if (dom.highlightCard) dom.highlightCard.classList.add('hidden');
            return;
        }

        // --- SUPER ODDS VIEW (BEST TIPS TODAY & UPCOMING) ---
        if (currentFilter === 'superodds') {
            const allGames = state.matchData || [];

            // 1. Tenta pegar jogos de HOJE com Win Rate >= 80%
            const now = new Date();
            now.setHours(0, 0, 0, 0); // Zera hora para comparar datas

            let superGames = allGames.filter(g => {
                const d = new Date(g.date);
                // Verifica se é hoje ou futuro próximo
                const isFutureOrToday = d >= now;
                return isFutureOrToday && g.tip.win_rate >= 80;
            });

            // Se encontrar, ordena por Data (mais próximo) e depois por Win Rate
            superGames.sort((a, b) => {
                // Se dias forem diferentes, prioriza o mais cedo
                const dateA = new Date(a.date);
                const dateB = new Date(b.date);
                if (dateA.toDateString() !== dateB.toDateString()) {
                    return dateA - dateB;
                }
                // Se for mesmo dia, prioriza win rate maior
                return b.tip.win_rate - a.tip.win_rate;
            });

            // Header
            const header = document.createElement('div');
            header.innerHTML = `
                <div style="padding: 15px; margin-bottom: 20px; background: linear-gradient(135deg, #ff5e00 0%, #ff9100 100%); border-radius: 12px; color: white; text-align: center; box-shadow: 0 4px 15px rgba(255, 94, 0, 0.3);">
                     <h2 style="margin:0; font-size:1.5rem; font-weight:900; font-style:italic;">SUPER ODDS 🔥</h2>
                     <p style="margin:5px 0 0 0; font-size:0.9rem; opacity:0.9;">As melhores oportunidades selecionadas a dedo.</p>
                </div>
            `;
            container.appendChild(header);

            if (superGames.length === 0) {
                container.innerHTML += `
                    <div style="text-align:center; padding:40px; color:#999;">
                        <div style="font-size:2rem; margin-bottom:10px;">😴</div>
                        Nenhuma Super Odd encontrada para as próximas horas.<br>O mercado está fechado no momento.
                    </div>`;
                if (dom.highlightCard) dom.highlightCard.classList.add('hidden');
                return;
            }

            superGames.forEach(game => {
                container.appendChild(createMatchRow(game));
            });

            if (dom.highlightCard) dom.highlightCard.classList.add('hidden');
            return;
        }

        // --- NORMAL FEED VIEW ---
        if (dom.highlightCard && window.highlightMatch) dom.highlightCard.classList.remove('hidden');

        const allGames = state.matchData || [];

        // 1. Filtra os jogos
        let filtered = allGames.filter(g => {
            const gDate = new Date(g.date);
            const now = new Date();

            // Melhoria na Lógica de Data (Timezone Safe)
            const diffMs = gDate - now;
            const diffHours = diffMs / (1000 * 60 * 60);

            // Aceita jogos de 24h atrás (pra pegar resultados de hoje cedo) até 48h pra frente (agenda)
            const isRelevant = diffHours > -24 && diffHours < 48;

            // Na aba TUDO: mostra apenas jogos relevantes (hoje/agora)
            if (currentFilter === 'all') {
                return isRelevant;
            }

            // Nas abas de Esporte: também filtra por relevância
            return g.sport === currentFilter && isRelevant;
        });

        // 2. Classifica por Data (Jogos de hoje primeiro)
        filtered.sort((a, b) => new Date(a.date) - new Date(b.date));

        if (filtered.length === 0) {
            container.innerHTML = '<div style="text-align:center; padding:20px; color:#999;">Nenhum jogo encontrado.</div>';
            return;
        }

        // 3. Agrupa por Liga
        const groups = {};

        filtered.forEach(game => {
            // Usa o nome da liga já formatado pelo Python (ex: "Brasileirão Série A")
            // Se não tiver, usa o raw e dá uma limpada básica
            let displayLeague = game.league || game.raw_league || 'Outros';

            if (!groups[displayLeague]) {
                groups[displayLeague] = {
                    games: [],
                    sport: game.sport,
                    hasToday: false
                };
            }
            groups[displayLeague].games.push(game);

            // Verifica se é hoje (UTC safe check simplificado para UX local)
            const gDate = new Date(game.date);
            const now = new Date();
            // Compara dia/mes/ano
            if (gDate.getDate() === now.getDate() && gDate.getMonth() === now.getMonth() && gDate.getFullYear() === now.getFullYear()) {
                groups[displayLeague].hasToday = true;
            }
        });

        // 4. Ordenação das Ligas
        const priorityLeagues = [
            'Brasileirão', 'Serie A', 'Copa do Brasil',
            'Libertadores', 'Sudamericana', 'Champions',
            'Premier League', 'La Liga', 'Bundesliga',
            'Ligue 1', 'NBA', 'UFC'
        ];

        const sortedLeagues = Object.keys(groups).sort((a, b) => {
            const groupA = groups[a];
            const groupB = groups[b];

            // 1. Prioridade Absoluta: Tem jogo hoje? (Aberto vs Fechado)
            if (groupA.hasToday && !groupB.hasToday) return -1;
            if (!groupA.hasToday && groupB.hasToday) return 1;

            // 2. Prioridade de Familiaridade
            // Verifica se o nome da liga CONTÉM alguma palavra chave (ex: "Brasileirão Série B" contains "Brasileirão")
            const getRank = (name) => {
                const idx = priorityLeagues.findIndex(p => name.includes(p));
                return idx === -1 ? 999 : idx;
            };

            return getRank(a) - getRank(b);
        });

        // 5. Renderiza
        sortedLeagues.forEach(leagueName => {
            const group = groups[leagueName];
            const isOpen = group.hasToday; // Só abre se tiver jogo hoje

            // Wrapper
            const wrapper = document.createElement('div');
            wrapper.className = 'league-wrapper'; // Classe para CSS futuro se precisar
            wrapper.style.marginBottom = '12px';

            // Header
            const header = document.createElement('div');
            header.style.cssText = `
                display: flex; justify-content: space-between; align-items: center;
                padding: 10px 5px; cursor: pointer; border-bottom: 1px solid #eee;
            `;

            const headerColor = isOpen ? '#111' : '#888';
            const arrowRot = isOpen ? '90deg' : '0deg';
            const badge = isOpen ? `<span style="background:#e90029; color:white; font-size:0.6rem; padding:2px 6px; border-radius:4px; font-weight:700; margin-left:8px;">HOJE</span>` : '';

            header.innerHTML = `
                <div style="display:flex; align-items:center;">
                    <span style="font-size:1.2rem; margin-right:8px;">${getSportIcon(group.sport)}</span>
                    <span style="font-weight:800; color:${headerColor}; font-size:0.95rem;">${leagueName}</span>
                    ${badge}
                </div>
                <div class="arrow" style="transition:0.3s; transform: rotate(${arrowRot}); color:#ccc; font-size:1.2rem;">›</div>
            `;

            // Lista
            const list = document.createElement('div');
            list.style.display = isOpen ? 'block' : 'none';
            list.style.paddingTop = '5px';

            group.games.forEach(game => {
                list.appendChild(createMatchRow(game));
            });

            // Click Interaction
            header.addEventListener('click', () => {
                const isHidden = list.style.display === 'none';
                list.style.display = isHidden ? 'block' : 'none';
                const arrow = header.querySelector('.arrow');
                if (arrow) arrow.style.transform = isHidden ? 'rotate(90deg)' : 'rotate(0deg)';
                header.querySelector('span[style*="font-weight:800"]').style.color = isHidden ? '#111' : '#888';
            });

            wrapper.appendChild(header);
            wrapper.appendChild(list);
            container.appendChild(wrapper);
        });

    } catch (e) {
        console.error("Erro renderFeed:", e);
        if (dom.feed) dom.feed.innerHTML = '<div style="padding:20px; text-align:center;">Erro ao carregar jogos. Tente recarregar.</div>';
    }
}

// Helper para Histórico Clean
function createHistoryRow(match) {
    const el = document.createElement('div');
    el.style.cssText = `
        background: #fff;
        border-radius: 8px;
        padding: 12px;
        margin-bottom: 10px;
        border: 1px solid #eee;
        display: flex;
        align-items: center;
        justify-content: space-between;
    `;

    const isWin = match.result === 'WIN';
    const resultColor = isWin ? '#2ecc71' : '#e74c3c';
    const resultIcon = isWin ? '✅ GREEN' : '❌ RED';
    const bgBadge = isWin ? '#eafaf1' : '#fdedec';

    // Normalize team names handling
    const teamA = match.teamA ? match.teamA.name : (match.match_name ? match.match_name.split(' x ')[0] : 'Time A');
    const teamB = match.teamB ? match.teamB.name : (match.match_name ? match.match_name.split(' x ')[1] : 'Time B');

    // Date
    let dateStr = "Finalizado";
    try {
        const d = new Date(match.date);
        dateStr = `${d.getDate()}/${d.getMonth() + 1}`;
    } catch (e) { }

    // Market type badge com cores distintas
    let marketIcon = '🎯';
    let marketColor = '#333';
    const market = (match.tip.market || '').toLowerCase();
    const tipType = match.tip.type || 'Vencer';

    if (market.includes('gol') || market.includes('mais de') || market.includes('menos de') || market.includes('pontos')) {
        marketIcon = '⚽'; marketColor = '#2980b9';
    } else if (market.includes('ambos marcam') || market.includes('btts')) {
        marketIcon = '🔥'; marketColor = '#8e44ad';
    } else if (market.includes('dupla chance')) {
        marketIcon = '🛡️'; marketColor = '#27ae60';
    } else if (market.includes('handicap')) {
        marketIcon = '📊'; marketColor = '#d35400';
    } else if (market.includes('escanteio') || market.includes('canto')) {
        marketIcon = '⛳'; marketColor = '#8e44ad';
    } else if (market.includes('chute')) {
        marketIcon = '👟'; marketColor = '#d35400';
    }

    // Formata mercado para exibição curta
    let displayMarket = match.tip.market;
    displayMarket = displayMarket
        .replace('Total de Gols: ', '')
        .replace('Total de Pontos: ', 'Pts ')
        .replace('Vencer: ', '')
        .replace('Ambos Marcam: ', 'BTTS ');

    el.innerHTML = `
        <div style="display:flex; flex-direction:column; gap:4px; flex:1;">
             <div style="font-size:0.75rem; color:#999;">${dateStr} • ${match.league}</div>
             <div style="font-size:0.9rem; font-weight:700; color:#333;">${teamA} vs ${teamB}</div>
             <div style="font-size:0.8rem; color:${marketColor}; display:flex; align-items:center; gap:4px;">
                <span>${marketIcon}</span>
                <strong>${displayMarket}</strong>
             </div>
        </div>
        
        <div style="display:flex; flex-direction:column; align-items:flex-end; gap:5px; min-width:75px;">
            <div style="background:${bgBadge}; color:${resultColor}; font-weight:900; font-size:0.7rem; padding:4px 8px; border-radius:4px; letter-spacing:0.5px;">
                ${resultIcon}
            </div>
            <div style="font-size:0.7rem; color:#ccc;">ODD @${match.tip.odd}</div>
        </div>
    `;

    return el;
}

// Cria o Card estilo "Linha" (Row) igual ao print
function createMatchRow(match) {
    const el = document.createElement('div');
    el.className = 'game-card match-row';

    // Formata Hora
    const dateObj = new Date(match.date);
    const timeStr = dateObj.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    const isToday = new Date().toDateString() === dateObj.toDateString();
    const dateStr = isToday ? `Hoje, ${timeStr}` : `${dateObj.getDate()}/${dateObj.getMonth() + 1}, ${timeStr}`;

    const iconA = match.teamA.logo || 'https://via.placeholder.com/30';
    const iconB = match.teamB.logo || 'https://via.placeholder.com/30';

    // --- CONFIDENCE TIER BADGE ---
    const tier = match.tip.tier || 'PADRÃO';
    let tierBadge = '';
    const tierConfig = {
        'SEGURO': { icon: '🔒', color: '#27ae60', bg: '#eafaf1', label: 'SEGURO' },
        'VALOR': { icon: '⚡', color: '#f39c12', bg: '#fef9e7', label: 'VALOR' },
        'PREMIUM': { icon: '💎', color: '#8e44ad', bg: '#f5eef8', label: 'PREMIUM' },
        'PADRÃO': { icon: '🎯', color: '#3498db', bg: '#ebf5fb', label: 'PADRÃO' }
    };
    const tc = tierConfig[tier] || tierConfig['PADRÃO'];
    tierBadge = `<span style="background:${tc.bg}; color:${tc.color}; font-size:0.6rem; font-weight:900; padding:2px 6px; border-radius:4px; letter-spacing:0.5px;">${tc.icon} ${tc.label}</span>`;

    // --- VALUE INDICATOR (+EV) ---
    let valueBadge = '';
    if (match.tip.is_value) {
        valueBadge = `<span style="background:#fff3cd; color:#856404; font-size:0.55rem; font-weight:800; padding:2px 5px; border-radius:3px; margin-left:4px;">+EV</span>`;
    }

    // --- CASHOUT SIGNAL ---
    let cashoutBadge = '';
    if (match.tip.cashout_friendly) {
        cashoutBadge = `<span style="background:#d4edda; color:#155724; font-size:0.55rem; font-weight:800; padding:2px 5px; border-radius:3px; margin-left:4px;">💰 CASHOUT</span>`;
    }

    // Smart Analysis Logic
    let analysisHtml = '';
    if (match.tip.analysis) {
        // Split analysis by " | DNA " to separate main text from DNA insight
        const parts = match.tip.analysis.split(' | DNA ');
        const mainAnalysis = parts[0] || match.tip.analysis;
        const dnaInsight = parts[1] || '';

        analysisHtml = `
            <div style="background: #f8f9fa; border-left: 3px solid #ff5e00; padding: 8px 12px; margin-top: 12px; border-radius: 0 4px 4px 0;">
                <div style="display:flex; align-items:center; gap:6px; margin-bottom:4px;">
                    <span style="font-size:0.75rem; font-weight:800; color:#333; text-transform:uppercase;">🧠 Análise IA</span>
                    ${tierBadge} ${valueBadge} ${cashoutBadge}
                </div>
                <p style="font-size:0.75rem; color:#555; margin:0; line-height:1.4;">
                    "${mainAnalysis}"
                </p>
                ${dnaInsight ? `<p style="font-size:0.65rem; color:#999; margin:4px 0 0 0; font-style:italic;">📊 ${dnaInsight}</p>` : ''}
            </div>
        `;
    }

    // Market Icon/Badge based on type
    let marketBadgeColor = '#e90029';
    let marketIcon = '🎯';
    const mkt = (match.tip.market || '').toLowerCase();
    if (match.tip.type === 'Gols' || mkt.includes('gol') || mkt.includes('ponto')) { marketBadgeColor = '#2980b9'; marketIcon = '⚽'; }
    if (match.tip.type === 'Escanteios') { marketBadgeColor = '#8e44ad'; marketIcon = '⛳'; }
    if (match.tip.type === 'Chutes') { marketBadgeColor = '#d35400'; marketIcon = '👟'; }
    if (mkt.includes('dupla chance')) { marketBadgeColor = '#27ae60'; marketIcon = '🛡️'; }
    if (mkt.includes('handicap')) { marketBadgeColor = '#d35400'; marketIcon = '📊'; }
    if (mkt.includes('ambos marcam')) { marketBadgeColor = '#8e44ad'; marketIcon = '🔥'; }

    // Format market display
    let displayMarket = match.tip.market
        .replace('Vencer:', '')
        .replace('Total de Gols:', 'Gols')
        .replace('Escanteios:', 'Cantos')
        .replace('Total de Pontos:', 'Pts')
        .replace('Ambos Marcam:', 'BTTS');

    el.innerHTML = `
        <div class="row-left" style="width: 100%;">
            <div class="row-meta">
                <span class="match-time">${dateStr}</span>
                <div style="display:flex; gap:4px; align-items:center;">
                    ${tierBadge}
                    <div class="card-header-cta">Criar Aposta ></div>
                </div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px;">
                <div class="teams-container" style="margin-bottom: 0;">
                    <div class="team-row">
                        <img src="${iconA}" class="team-logo">
                        <span class="team-name" style="font-size: 0.9rem;">${match.teamA.name}</span>
                    </div>
                    <div class="team-row">
                        <img src="${iconB}" class="team-logo">
                        <span class="team-name" style="font-size: 0.9rem;">${match.teamB.name}</span>
                    </div>
                </div>

                <div class="row-right" style="min-width: unset;">
                    <div class="tip-market" style="color:${marketBadgeColor}">
                        ${marketIcon} ${displayMarket}
                    </div>
                    <div class="odd-button" style="padding: 6px 12px; min-width: 80px;">
                        <span class="odd-label" style="font-size: 0.6rem;">PROB.</span>
                        <span class="odd-value" style="font-size: 0.9rem;">${match.tip.win_rate}%</span>
                    </div>
                </div>
            </div>

            ${analysisHtml}

            <!-- Botão Apostar Agora -->
            <a href="${state.affiliateLink}" target="_blank" class="btn-action" style="margin-top:12px;">
                APOSTAR AGORA 🚀
            </a>
        </div>
    `;

    // Atribui os dados do jogo para o delegador conseguir ler
    el.dataset.match = JSON.stringify(match);

    return el;
}

// Global para ser acessível pelo HTML onclick
// Global para ser acessível pelo HTML onclick
window.openVerificationModal = function () {
    if (dom.onboardingModal) {
        dom.onboardingModal.classList.remove('hidden');
    }
}

// --- UTIL: TOAST NOTIFICATION SYSTEM ---
function showToast(message, icon = '✅') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.innerHTML = `<span class="toast-icon">${icon}</span> ${message}`;

    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
        toast.classList.add('show');
    });

    // Remove after 3s
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// --- FEATURE: COPIAR APOSTA REAL ---
window.copySingleTip = function (matchData) {
    if (!matchData) return;

    // Tenta parsear se vier como string (do HTML attribute)
    let match = matchData;
    if (typeof matchData === 'string') {
        try { match = JSON.parse(matchData); } catch (e) { }
    }

    const textToCopy = `🔥 *Dica HyperTips:*\n\n⚽ ${match.teamA.name} x ${match.teamB.name}\n🏆 ${match.league}\n\n🎯 *Aposta:* ${match.tip.market}\n📈 *Probabilidade:* ${match.tip.win_rate}%\n\n👉 Aposte aqui: ${state.affiliateLink}`;

    if (navigator.clipboard) {
        navigator.clipboard.writeText(textToCopy).then(() => {
            showToast("Aposta copiada com sucesso!");
        }).catch(() => {
            showToast("Erro ao copiar.", "❌");
        });
    } else {
        // Fallback antigo
        const ta = document.createElement('textarea');
        ta.value = textToCopy;
        document.body.appendChild(ta);
        ta.select();
        document.execCommand('copy');
        document.body.removeChild(ta);
        showToast("Aposta copiada com sucesso!");
    }
}

// Nova função para renderizar os stats REAIS acumulados
function renderStats() {
    const elHits = document.getElementById('stats-hits');
    const elWinRate = document.getElementById('stats-winrate');

    let hits = 18;
    let winRate = 84;

    if (window.dailyStats) {
        // Usa dados REAIS acumulados
        hits = window.dailyStats.hits || 0;
        winRate = window.dailyStats.win_rate || 85;
    } else {
        // Fallback Local Simulation based on time
        const hour = new Date().getHours();
        hits = Math.max(2, Math.floor(4 + (hour * 1.5)));
    }

    if (elHits) elHits.textContent = hits;
    if (elWinRate) elWinRate.textContent = `${winRate}%`;

    // Renderiza stats extras se existirem no DOM
    const elTotal = document.getElementById('stats-total');
    const elDays = document.getElementById('stats-days');
    if (elTotal && window.dailyStats) elTotal.textContent = window.dailyStats.total || 0;
    if (elDays && window.dailyStats) elDays.textContent = window.dailyStats.days_active || 0;
}

// Função Helper Global para o Banner de Histórico
window.showHistory = function () {
    // Remove active class das tabs
    dom.tabs.forEach(t => t.classList.remove('active'));

    // Set state manual
    state.activeFilter = 'history';
    state.historyFilter = 'all'; // Reseta filtro interno para 'Tudo'

    // Renderiza
    renderFeed('history');

    // Scroll suave até o feed
    dom.feed.scrollIntoView({ behavior: 'smooth' });
}
