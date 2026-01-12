// SuperTips Hub Logic
const state = {
    activeFilter: 'all',
    affiliateLink: "https://superbet.com/registro",
    dateFormat: new Intl.DateTimeFormat('pt-BR', {
        weekday: 'long',
        day: 'numeric',
        month: 'long'
    }),
    isVerified: localStorage.getItem('superbet_verified') === 'true' // Persistência básica
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
    parlayCard: document.getElementById('parlay-card'),
    parlayItems: document.getElementById('parlay-items-container'),
    parlayOdd: document.getElementById('parlay-total-odd')
};

// ... (Resto do código) ...

function initFilters() {
    dom.tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            // Remove active class
            dom.tabs.forEach(t => t.classList.remove('active'));
            // Add active (Encontra o elemento pai .nav-icon-item se clicou no filho)
            const target = e.target.closest('.nav-icon-item');
            target.classList.add('active');
            // Update State
            state.activeFilter = target.dataset.sport;
            // Rerender
            renderFeed();
        });
    });
}

// Init
document.addEventListener('DOMContentLoaded', () => {
    // Check if onboarding is done
    const onboarded = localStorage.getItem('supertips_onboarding_v2');
    if (!onboarded) {
        dom.onboardingModal.classList.remove('hidden');
        setupOnboarding();
    } else {
        state.isVerified = true;
    }

    if (window.gamesData) {
        state.matchData = window.gamesData;
    } else if (window.LIVE_GAMES) {
        state.matchData = window.LIVE_GAMES;
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

    initFilters();
    renderFeed();

    // --- INTERSTITIAL LOGIC (TRAVA DE SEGURANÇA) ---
    const betReminderModal = document.getElementById('bet-reminder-modal');
    const btnConfirmBet = document.getElementById('btn-confirm-bet');
    const btnCancelBet = document.getElementById('btn-cancel-bet');
    let pendingAffiliateLink = null;

    // Delegação de evento para pegar cliques em QUALQUER botão de aposta dinâmico
    document.addEventListener('click', (e) => {
        // Verifica se clicou num botão de aposta (mas não nos botões do próprio modal ou onboarding)
        if (e.target.closest('.game-card .btn-action') || e.target.closest('.parlay-card .btn-action')) {
            e.preventDefault(); // PARE!

            // Pega o link original
            const btn = e.target.closest('a');
            if (btn) pendingAffiliateLink = btn.href;

            // Mostra o alerta
            betReminderModal.classList.remove('hidden');
        }
    });

    // Ação Confirmar
    btnConfirmBet.addEventListener('click', () => {
        betReminderModal.classList.add('hidden');
        if (pendingAffiliateLink) {
            window.open(pendingAffiliateLink, '_blank');
        }
    });

    // Ação Cancelar
    btnCancelBet.addEventListener('click', () => {
        betReminderModal.classList.add('hidden');
    });

});

function setupOnboarding() {
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

    dom.check18.addEventListener('change', checkValidity);
    dom.checkTerms.addEventListener('change', checkValidity);

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

function renderHighlight() {
    // Safety Force: Se não tiver highlight mas tiver dados normais, pega o primeiro
    if (!window.highlightMatch && window.gamesData && window.gamesData.length > 0) {
        window.highlightMatch = window.gamesData[0]; // Fallback forçado no Front
    }

    if (window.highlightMatch) {
        const game = window.highlightMatch;
        // Validação extra pra não quebrar
        if (!game.teamA || !game.teamB || !game.tip) return;

        dom.highlightCard.classList.remove('hidden');

        const winRate = game.tip.win_rate || 85;

        // UI Avatars Fallback
        const imgA = game.teamA.logo || `https://ui-avatars.com/api/?name=${game.teamA.name}&background=eee&color=333`;
        const imgB = game.teamB.logo || `https://ui-avatars.com/api/?name=${game.teamB.name}&background=eee&color=333`;

        dom.highlightContent.innerHTML = `
            <div style="display: flex; justify-content: space-around; align-items: start; margin-bottom: 25px;">
                <div style="display: flex; flex-direction: column; align-items: center; width: 40%;">
                    <div style="width: 70px; height: 70px; margin-bottom: 8px;">
                        <img src="${imgA}" style="width: 100%; height: 100%; object-fit: contain;">
                    </div>
                    <div style="font-weight: 700; text-align: center; font-size: 0.85rem; line-height: 1.2;">${game.teamA.name}</div>
                </div>
                
                <div style="font-size: 1.5rem; font-weight: 900; color: #ddd; margin-top: 20px;">VS</div>
                
                <div style="display: flex; flex-direction: column; align-items: center; width: 40%;">
                    <div style="width: 70px; height: 70px; margin-bottom: 8px;">
                        <img src="${imgB}" style="width: 100%; height: 100%; object-fit: contain;">
                    </div>
                    <div style="font-weight: 700; text-align: center; font-size: 0.85rem; line-height: 1.2;">${game.teamB.name}</div>
                </div>
            </div>
            
            <div style="background: #f8f9fa; border: 1px solid #eee; padding: 15px; border-radius: 12px; margin-bottom: 15px;">
                <div style="color: #666; font-size: 0.75rem; font-weight: 700; text-transform: uppercase; margin-bottom: 5px;">MERCADO INDICADO</div>
                <div style="color: #e90029; font-size: 1.1rem; font-weight: 900;">${game.tip.market}</div>
                <div style="color: #111; font-weight: 800; font-size: 1.1rem; margin-top: 5px;">ODD ${game.tip.odd}</div>
            </div>

            <div class="prob-bar-area">
                <span style="font-size:0.7rem; font-weight:700; color:#888;">PROBABILIDADE:</span>
                <div class="prob-bar-bg">
                    <div class="prob-bar-fill" style="width: ${winRate}%"></div>
                </div>
                <span class="prob-val">${winRate}%</span>
            </div>
            
            <a href="${state.affiliateLink}" target="_blank" class="btn-action" style="text-decoration: none; margin-top: 15px;">
                APOSTAR AGORA 🚀
            </a>
        `;
    }
}

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

function setupModalEvents() {
    if (dom.btnCreate) dom.btnCreate.href = state.affiliateLink;
    dom.btnValidate.addEventListener('click', () => {
        const id = dom.inputId.value;
        if (id.length > 4) {
            localStorage.setItem('superbet_verified', 'true');
            state.isVerified = true;
            dom.modal.classList.add('hidden');
            renderFeed();
            alert("ID Validado! Bônus SuperOdds Ativado.");
        } else {
            alert("ID Inválido. Certifique-se de copiar o ID da sua NOVA conta no perfil.");
        }
    });
}

function initFilters() {
    dom.tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            dom.tabs.forEach(t => t.classList.remove('active'));
            const target = e.target.closest('.nav-icon-item'); // Garante pegar o item certo
            if (target) {
                target.classList.add('active');
                state.activeFilter = target.dataset.sport;
                renderFeed();
            }
        });
    });
}

function renderFeed() {
    dom.feed.innerHTML = '';
    let filtered = state.matchData.filter(m =>
        state.activeFilter === 'all' || m.sport === state.activeFilter
    );
    filtered.sort((a, b) => new Date(a.date) - new Date(b.date));
    let lastDateStr = '';

    filtered.forEach(match => {
        const dateObj = new Date(match.date);
        const dateStr = state.dateFormat.format(dateObj);

        if (dateStr !== lastDateStr) {
            const header = document.createElement('div');
            header.className = 'date-header';
            header.innerText = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
            dom.feed.appendChild(header);
            lastDateStr = dateStr;
        }
        const card = createGameCard(match);
        dom.feed.appendChild(card);
    });

    if (filtered.length === 0) {
        dom.feed.innerHTML = '<div style="text-align:center; padding: 40px; color: #666;">Carregando oportunidades da IA...</div>';
    }
}

function createGameCard(match) {
    const el = document.createElement('div');
    el.className = 'game-card';

    const dateObj = new Date(match.date);
    const timeStr = dateObj.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    const sportIcon = getSportIcon(match.sport);
    const winRate = match.tip.win_rate || 75;

    // UI Avatars for Games
    const imgA = match.teamA.logo || `https://ui-avatars.com/api/?name=${match.teamA.name}&background=eee&color=333`;
    const imgB = match.teamB.logo || `https://ui-avatars.com/api/?name=${match.teamB.name}&background=eee&color=333`;

    el.innerHTML = `
        <div class="card-header">
            <span class="league-info"><span class="sport-icon">${sportIcon}</span> ${match.league}</span>
            <span class="game-time">${timeStr}</span>
        </div>

        <div class="teams-container">
            <div class="team">
                <div class="team-avatar">
                    <img src="${imgA}" onerror="this.src='https://ui-avatars.com/api/?name=${match.teamA.name}&background=eee&color=333'">
                </div>
                <span class="team-name">${match.teamA.name}</span>
            </div>
            <span class="vs-text">VS</span>
            <div class="team">
                <div class="team-avatar">
                    <img src="${imgB}" onerror="this.src='https://ui-avatars.com/api/?name=${match.teamB.name}&background=eee&color=333'">
                </div>
                <span class="team-name">${match.teamB.name}</span>
            </div>
        </div>

        <div class="tip-container">
            <div class="market-name" style="margin-bottom: 10px;">${match.tip.market}</div>
            
            <div class="prob-bar-area">
                <span style="font-size:0.7rem; font-weight:700; color:#888;">IA PROB:</span>
                <div class="prob-bar-bg">
                    <div class="prob-bar-fill" style="width: ${winRate}%"></div>
                </div>
                <span class="prob-val">${winRate}%</span>
            </div>
            
            <a href="${state.affiliateLink}" target="_blank" class="btn-action" style="text-decoration: none;">
                APOSTAR AGORA
            </a>
            
            <div class="actions-area" style="justify-content: center; margin-top: 15px;">
                 <span class="superbet-badge-tiny">VERIFICADO PELA IA</span>
            </div>
        </div>
    `;

    // Click no card leva pro link
    el.addEventListener('click', (e) => {
        if (e.target.tagName !== 'A') {
            window.open(state.affiliateLink, '_blank');
        }
    });

    return el;
}

// Global para ser acessível pelo HTML onclick
window.openVerificationModal = function () {
    dom.modal.classList.remove('hidden');
}
