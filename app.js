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
    btnCreate: document.getElementById('btn-create-account')
};

// Init
document.addEventListener('DOMContentLoaded', () => {
    // Carregar dados de fonte externa ou fallback
    if (window.LIVE_GAMES) {
        state.matchData = window.LIVE_GAMES;
    } else {
        state.matchData = []; // Fallback vazio
    }

    initFilters();
    renderFeed();
    setupModalEvents();
});

function setupModalEvents() {
    // Link do botão "Criar Conta" dentro do modal
    if (dom.btnCreate) dom.btnCreate.href = state.affiliateLink;

    // Botão Validar ID
    dom.btnValidate.addEventListener('click', () => {
        const id = dom.inputId.value;
        if (id.length > 4) {
            // Fake Validation Success
            localStorage.setItem('superbet_verified', 'true');
            state.isVerified = true;
            dom.modal.classList.add('hidden');
            renderFeed(); // Re-render unlocked
            alert("ID Validado! Bônus SuperOdds Ativado.");
        } else {
            alert("ID Inválido. Certifique-se de copiar o ID da sua NOVA conta no perfil.");
        }
    });
}

function initFilters() {
    dom.tabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            // Remove active class
            dom.tabs.forEach(t => t.classList.remove('active'));
            // Add active
            e.target.classList.add('active');
            // Update State
            state.activeFilter = e.target.dataset.sport;
            // Rerender
            renderFeed();
        });
    });
}

function renderFeed() {
    dom.feed.innerHTML = '';

    // Filter Matches
    let filtered = state.matchData.filter(m =>
        state.activeFilter === 'all' || m.sport === state.activeFilter
    );

    // Sort by Date
    filtered.sort((a, b) => new Date(a.date) - new Date(b.date));

    // Group by Date Label
    let lastDateStr = '';

    filtered.forEach(match => {
        // Date Header Logic
        const dateObj = new Date(match.date);
        const dateStr = state.dateFormat.format(dateObj);

        if (dateStr !== lastDateStr) {
            const header = document.createElement('div');
            header.className = 'date-header';
            header.innerText = dateStr.charAt(0).toUpperCase() + dateStr.slice(1);
            dom.feed.appendChild(header);
            lastDateStr = dateStr;
        }

        // Create Card
        const card = createGameCard(match);
        dom.feed.appendChild(card);
    });

    if (filtered.length === 0) {
        dom.feed.innerHTML = '<div style="text-align:center; padding: 40px; color: #666;">Nenhum jogo encontrado no banco de dados. Verifique o games_data.js.</div>';
    }
}

function createGameCard(match) {
    const el = document.createElement('div');
    el.className = 'game-card';

    const dateObj = new Date(match.date);
    const timeStr = dateObj.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' });
    const sportIcons = {
        'football': '⚽',
        'basketball': '🏀',
        'tennis': '🎾',
        'mma': '🥊',
        'american_football': '🏈',
        'hockey': '🏒',
        'default': '📅'
    };
    const sportIcon = sportIcons[match.sport] || sportIcons['default'];

    // Link para Superbet Wrapper
    const matchLink = state.affiliateLink;

    // Lógica Visual de Winrate
    const winRate = match.tip.win_rate || 75; // Fallback

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
                
                <span class="superbet-badge-tiny">VERIFICADO</span>
            </div>
        </div>
    `;

    // Make whole card clickable Logic
    el.addEventListener('click', (e) => {
        // Se estiver bloqueado, qualquer clique abre o modal
        if (!state.isVerified) {
            openVerificationModal();
        } else if (e.target.tagName !== 'A' && e.target.tagName !== 'BUTTON') {
            window.open(matchLink, '_blank');
        }
    });

    return el;
}

// Global para ser acessível pelo HTML onclick
window.openVerificationModal = function () {
    dom.modal.classList.remove('hidden');
}
