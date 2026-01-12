# Plano de Implementação: Scanner de Oportunidades Esportivas (MVP)

## 1. Visão Geral
Aplicação web mobile-first focada em gestão de banca e simulação de sinais de apostas esportivas.
Tecnologia: HTML5, CSS3, JavaScript (Vanilla). Sem dependências.

## 2. Estrutura de Dados (app.js)

```javascript
/* Estado Global da Aplicação */
const appState = {
    bankroll: 30.00, // Valor inicial padrão
    isScanning: false,
    currentSignal: null, // Objeto do sinal atual
    config: {
        minConfidence: 88,
        maxConfidence: 98,
        entryPercentageMin: 0.02, // 2%
        entryPercentageMax: 0.04, // 4%
        winMultiplier: 1.80 // Odd média simulada
    }
};

/* Estrutura do Objeto de Sinal */
const SignalSchema = {
    match: "Time A vs Time B",
    market: "Over 2.5 Gols",
    confidence: 95, // %
    entryValue: 1.20, // R$
    timestamp: Date.now()
};
```

## 3. Identidade Visual (Design System)

**Paleta de Cores:**
- Background: `#0f172a` (Slate 900)
- Surface: `#1e293b` (Slate 800)
- Primary/Accent: `#8b5cf6` (Violet 500)
- Go/Success: `#10b981` (Emerald 500)
- Stop/Error: `#ef4444` (Red 500)
- Text Primary: `#f8fafc` (Slate 50)
- Text Secondary: `#94a3b8` (Slate 400)

**Tipografia:**
- Font Family: 'Inter', sans-serif.

## 4. Lista de Tarefas (Roadmap)

### Fase 2.1: Estrutura & Estilo (HTML/CSS)
- [ ] Criar `index.html` com meta tags viewport e importação de fontes Google.
- [ ] Estruturar o Modal de Onboarding (backdrop + card).
- [ ] Estruturar o Header (Dashboard de Banca).
- [ ] Estruturar a Área de Ação (Botão Escanear / Loader).
- [ ] Estruturar o Card de Sinal (inicialmente oculto).
- [ ] Criar `style.css` com reset CSS e variáveis de cores.
- [ ] Implementar animação de "Pulso" no botão de escanear.
- [ ] Implementar animação de "Radar/Loading" de 3 segundos.
- [ ] Estilizar cards com "Glassmorphism" sutil (bordas translúcidas).

### Fase 2.2: Lógica (JavaScript)
- [ ] Inicializar `app.js` e seletores DOM.
- [ ] **Lógica de Onboarding:**
    - Verificar se há banca salva (localStorage opcional, mas foco em sessão atual).
    - Exibir modal ao carregar.
    - Validar input e atualizar `appState.bankroll`.
- [ ] **Motor de Scanner:**
    - Listener no botão "Escanear".
    - `setTimeout` de 3000ms para simular processamento.
    - Ocultar botão -> Mostrar Loader -> Mostrar Resultado.
- [ ] **Gerador de Sinais (RNG):**
    - Array de TIs (Times) e Mercados.
    - Função para gerar confiança (88-98%).
    - Função para calcular entrada (2-4% da banca atual).
    - Renderizar dados no DOM.
- [ ] **Gestão de Resultados:**
    - Listeners nos botões "Green" e "Red".
    - **Green:** Banca += Entrada * 1.80. Feedback visual (Confetes/Verde).
    - **Red:** Banca -= Entrada. Feedback visual (Shake/Vermelho).
    - Atualizar display da banca.
    - Resetar estado para permitir novo scan.

## 5. Critérios de Aceite
1. O app abre sem erros no console.
2. O fluxo: Início -> Scan (3s) -> Sinal -> Resultado -> Atualização de Banca funciona sem travamentos.
3. Responsividade total em resoluções mobile (320px+).
4. Visual "Cyber-Dark" fiel à descrição.
