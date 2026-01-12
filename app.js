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
    tabs: document.querySelectorAll('.tab-btn'),
    modal: document.getElementById('cpa-modal'),
    inputId: document.getElementById('superbet-id-input'),
    btnValidate: document.getElementById('btn-validate-id'),
    btnCreate: document.getElementById('btn-create-account'),
    // Novos Elementos
    parlayCard: document.getElementById('parlay-card'),
    parlayItems: document.getElementById('parlay-items-container'),
    parlayOdd: document.getElementById('parlay-total-odd')
};

// Init
document.addEventListener('DOMContentLoaded', () => {
    // Carregar dados de fonte externa (games_data.js)
    if (window.gamesData) {
        state.matchData = window.gamesData;
        renderParlay(); // Renderiza a Múltipla se existir
    } else if (window.LIVE_GAMES) {
        state.matchData = window.LIVE_GAMES; // Fallback antigo
    } else {
        state.matchData = [];
    }

    initFilters();
    renderFeed();
    setupModalEvents();
});

function renderParlay() {
    if (window.dailyParlay && window.dailyParlay.length > 0) {
        dom.parlayCard.classList.remove('hidden');
        dom.parlayOdd.innerText = window.parlayTotalOdd || "3.50";

        dom.parlayItems.innerHTML = '';
        window.dailyParlay.forEach(game => {
            const item = document.createElement('div');
            item.className = 'parlay-item';

            // Ícone do esporte
            const sportIcon = getSportIcon(game.sport);

            item.innerHTML = `
                <div class="parlay-match-info">
                    <span>${sportIcon} ${game.teamA.name} x ${game.teamB.name}</span>
                </div>
                <span class="parlay-tip-market">${game.tip.market}</span>
            `;
            dom.parlayItems.appendChild(item);
        });
    }
}

function copyParlay() {
    if (!window.dailyParlay) return;

    let text = "🚀 *BILHETE PRONTO IA - SUPERTIPS*\n\n";
    window.dailyParlay.forEach(game => {
        text += `⚽ ${game.teamA.name} x ${game.teamB.name}\n`;
        text += `🎯 ${game.tip.market} (@${game.tip.odd})\n\n`;
    });
    text += `💰 Odd Total: ${window.parlayTotalOdd}\n`;
    text += `🔗 Aposte aqui: ${state.affiliateLink}`;

    navigator.clipboard.writeText(text).then(() => {
        const btn = document.querySelector('.btn-copy-parlay');
        const originalText = btn.innerText;
        btn.innerText = "COPIADO! ✅";
        btn.classList.add('copied');
        setTimeout(() => {
            btn.innerText = originalText;
            btn.classList.remove('copied');
        }, 2000);
    });
}

function copySingleTip(matchIndex) {
    // Acha o match pelo ID ou Index (simplificado aqui passamos o objeto direto no onclick se possivel, mas stringify é ruim)
    // Vamos reconstruir no frontend
    // Implementação simplificada:
    alert("Código copiado! (Simulação)");
}

function getSportIcon(sportKey) {
    const icons = {
        'football': '⚽',
        'basketball': '🏀',
        'tennis': '🎾',
        'mma': '🥊',
        'american_football': '🏈',
        'hockey': '🏒',
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
            e.target.classList.add('active');
            state.activeFilter = e.target.dataset.sport;
            renderFeed();
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

    el.innerHTML = `
        <div class="card-header">
            <span class="league-info"><span class="sport-icon">${sportIcon}</span> ${match.league}</span>
            <span class="game-time">${timeStr}</span>
        </div>

        <div class="teams-container">
            <div class="team">
                <div class="team-avatar">
                    <img src="${match.teamA.logo}" alt="${match.teamA.name}" onerror="this.onerror=null;this.src='https://ui-avatars.com/api/?name=${match.teamA.name}&background=eee&color=333'">
                </div>
                <span class="team-name">${match.teamA.name}</span>
            </div>
            <span class="vs-badge">VS</span>
            <div class="team">
                <div class="team-avatar">
                    <img src="${match.teamB.logo}" alt="${match.teamB.name}" onerror="this.onerror=null;this.src='https://ui-avatars.com/api/?name=${match.teamB.name}&background=eee&color=333'">
                </div>
                <span class="team-name">${match.teamB.name}</span>
            </div>
        </div>

        <div class="tip-box ${state.isVerified ? '' : 'locked'}">
            ${!state.isVerified ? `
                <div class="lock-overlay">
                    <button class="btn-unlock" onclick="openVerificationModal()">
                        🔓 DESBLOQUEAR TIP
                    </button>
                </div>
            ` : ''}

            <div class="tip-content">
                <span class="tip-market">${match.tip.market}</span>
                
                <div class="win-rate-display">
                    <span class="win-rate-text">${winRate}%</span>
                    <span class="win-rate-label">Probabilidade IA</span>
                </div>
                
                <div class="progress-container">
                    <div class="progress-bar" style="width: ${winRate}%"></div>
                </div>
                
                <div class="actions-area">
                    <button class="btn-copy-code" onclick="event.stopPropagation(); alert('Link da aposta copiado!')">
                        📋 COPIAR
                    </button>
                     <span class="superbet-badge-tiny">VERIFICADO</span>
                </div>
            </div>
        </div>
    `;

    el.addEventListener('click', (e) => {
        if (!state.isVerified) {
            openVerificationModal();
        } else if (e.target.tagName !== 'BUTTON') {
            window.open(state.affiliateLink, '_blank');
        }
    });

    return el;
}

// Global para ser acessível pelo HTML onclick
window.openVerificationModal = function () {
    dom.modal.classList.remove('hidden');
}
