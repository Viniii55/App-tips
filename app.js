// SuperTips Hub Logic
const state = {
    activeFilter: 'all',
    affiliateLink: "https://superbet.com/registro",
    dateFormat: new Intl.DateTimeFormat('pt-BR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long'
    }),
    isVerified: localStorage.getItem('superbet_verified') === 'true', // Persistência básica
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
    const onboarded = localStorage.getItem('supertips_onboarding_v2');
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
        localStorage.setItem('supertips_onboarding_v2', 'true');
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

// --- FUNÇÃO DE RENDERIZAÇÃO AGRUPADA POR LIGA ---
// --- FUNÇÃO DE RENDERIZAÇÃO AGRUPADA POR LIGA ---
function renderFeed(filterSport) {
    try {
        // Use current state filter if argument is not provided
        const currentFilter = filterSport || state.activeFilter;

        const container = dom.feed;
        if (!container) return;

        container.innerHTML = '';

        const allGames = state.matchData || [];

        // 1. Filtra os jogos
        let filtered = allGames.filter(g => {
            const gDate = new Date(g.date);
            const now = new Date();
            const isToday = gDate.getDate() === now.getDate() &&
                gDate.getMonth() === now.getMonth() &&
                gDate.getFullYear() === now.getFullYear();

            // Lógica Pedida:
            // "Na aba TUDO apenas exiba os jogos de hoje"
            if (currentFilter === 'all') {
                return isToday;
            }

            // "Quando clicar em esporte específico pode mostrar datas futuras"
            return g.sport === currentFilter;
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

// Cria o Card estilo "Linha" (Row) igual ao print
function createMatchRow(match) {
    const el = document.createElement('div');
    el.className = 'game-card match-row'; // match-row para estilo específico

    // Formata Hora
    const dateObj = new Date(match.date);
    const timeStr = dateObj.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    const isToday = new Date().toDateString() === dateObj.toDateString();
    const dateStr = isToday ? `Hoje, ${timeStr}` : `${dateObj.getDate()}/${dateObj.getMonth() + 1}, ${timeStr}`;

    const iconA = match.teamA.logo || 'https://via.placeholder.com/30';
    const iconB = match.teamB.logo || 'https://via.placeholder.com/30';

    el.innerHTML = `
        <div class="row-left" style="width: 100%;">
            <div class="row-meta">
                <span class="match-time">${dateStr}</span>
                <div class="card-header-cta">Criar Aposta ></div>
            </div>
            
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
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
                    <div class="tip-market">${match.tip.market}</div>
                    <div class="odd-button" style="padding: 6px 12px; min-width: 80px;">
                        <span class="odd-label" style="font-size: 0.6rem;">PROB.</span>
                        <span class="odd-value" style="font-size: 0.9rem;">${match.tip.win_rate}%</span>
                    </div>
                </div>
            </div>

            <!-- Botão Apostar Agora -->
            <a href="${state.affiliateLink}" target="_blank" class="btn-action">
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

    const textToCopy = `🔥 *Dica SuperTips:*\n\n⚽ ${match.teamA.name} x ${match.teamB.name}\n🏆 ${match.league}\n\n🎯 *Aposta:* ${match.tip.market}\n📈 *Probabilidade:* ${match.tip.win_rate}%\n\n👉 Aposte aqui: ${state.affiliateLink}`;

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

// Nova função para renderizar os stats
function renderStats() {
    const elHits = document.getElementById('stats-hits');
    const elWinRate = document.getElementById('stats-winrate');

    // Default (local) simulation if data is missing
    let hits = 18;
    let winRate = 84;

    if (window.dailyStats) {
        hits = window.dailyStats.hits;
        winRate = window.dailyStats.win_rate;
    } else {
        // Fallback Local Simulation based on time
        const hour = new Date().getHours();
        hits = Math.max(2, Math.floor(4 + (hour * 1.5)));
    }

    if (elHits) elHits.textContent = hits;
    if (elWinRate) elWinRate.textContent = `${winRate}%`;
}
