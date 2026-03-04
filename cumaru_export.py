"""
cumaru_export.py — Wood Capital
================================
Gera cumaru_data.json com todos os dados necessários para o dashboard HTML.
Execute mensalmente após o fechamento do período.

Todo mês altere:
    1. AVALIACAO_END  → último dia útil do mês
    2. CARTA_MENSAL   → seu texto da carta
    3. LOG            → adicione a operação do mês se houver

Uso:
    python cumaru_export.py

Saída:
    cumaru_data.json  → suba junto com cumaru.html no GitHub Pages
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import date, timedelta
import warnings
warnings.filterwarnings('ignore')

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

CAPITAL_INICIAL  = 100_000
AVALIACAO_START  = '2026-03-01'           # Abertura do Cumaru
AVALIACAO_END    = '2026-03-31'           # ← atualizar todo mês antes de rodar

hoje             = date.today()
JANELA_START     = (hoje - timedelta(days=400)).strftime('%Y-%m-%d')
JANELA_END       = AVALIACAO_END

# =============================================================================
# UNIVERSO IBOV POR SETOR
# =============================================================================

IBOV_UNIVERSE = {
    'Petróleo e Gás':    ['PETR4.SA', 'PETR3.SA', 'PRIO3.SA', 'RECV3.SA', 'ENEV3.SA'],
    'Mineração':         ['VALE3.SA', 'CMIN3.SA', 'CSNA3.SA'],
    'Siderurgia':        ['GGBR4.SA', 'USIM5.SA', 'GOAU4.SA'],
    'Energia Elétrica':  ['EGIE3.SA', 'NEOE3.SA', 'CPFE3.SA', 'ENGI11.SA', 'EQTL3.SA', 'CMIG4.SA'],
    'Bancos':            ['ITUB4.SA', 'BBDC4.SA', 'BBAS3.SA', 'SANB11.SA', 'BPAC11.SA'],
    'Fintechs':          ['ROXO34.SA', 'INBR32.SA'],
    'Seguros':           ['BBSE3.SA', 'IRBR3.SA', 'PSSA3.SA'],
    'Varejo':            ['MGLU3.SA', 'AZZA3.SA', 'LREN3.SA'],
    'Alimentos':         ['ABEV3.SA', 'BEEF3.SA', 'BRFS3.SA', 'JBSS3.SA'],
    'Saúde':             ['RDOR3.SA', 'HAPV3.SA', 'HYPE3.SA', 'FLRY3.SA', 'RADL3.SA'],
    'Telecom':           ['VIVT3.SA', 'TIMS3.SA'],
    'Tecnologia':        ['TOTS3.SA', 'LWSA3.SA', 'CASH3.SA'],
    'Construção Civil':  ['CYRE3.SA', 'MRVE3.SA', 'EVEN3.SA', 'DIRR3.SA', 'EZTC3.SA'],
    'Logística':         ['RAIL3.SA', 'ECOR3.SA', 'AZUL4.SA'],
    'Agro/Insumos':      ['KEPL3.SA', 'SLCE3.SA', 'RANI3.SA', 'AGRO3.SA'],
    'Papel e Celulose':  ['SUZB3.SA', 'KLBN11.SA'],
    'Utilidades':        ['SBSP3.SA', 'CSMG3.SA', 'SAPR11.SA'],
    'Indústria':         ['WEGE3.SA', 'ROMI3.SA'],
    'Distribuição':      ['GMAT3.SA', 'ASAI3.SA', 'PCAR3.SA'],
    'Shoppings':         ['MULT3.SA', 'IGTI11.SA'],
}

ALL_TICKERS = list({t for tickers in IBOV_UNIVERSE.values() for t in tickers})

# =============================================================================
# LOG DE OPERAÇÕES — adicionar mensalmente
# =============================================================================

LOG = [
    {
        "data":      "Mar 2026",
        "tipo":      "Abertura",
        "descricao": "Montagem da carteira Cumaru — Momentum puro, universo IBOV",
        "motivo":    "Top 2 por setor com momentum 12-1 positivo. Pesos Inverse Volatility. Capital inicial R$ 100.000.",
        "resultado": "—"
    },
]

# =============================================================================
# CARTA MENSAL — editar todo mês antes de rodar o script
# =============================================================================

CARTA_MENSAL = {
    "titulo": "Março 2026 — Abertura",
    "data":   "Abr 2026",
    "corpo": [
        "O Cumaru abre em março de 2026 com {n_ativos} ativos distribuídos em {n_setores} setores do IBOV, todos com momentum 12-1 positivo na data de entrada. A carteira é integralmente quantitativa — nenhum ativo foi selecionado por convicção qualitativa.",
        "A metodologia é simples e replicável: filtra o universo IBOV pelos dois melhores scores de momentum em cada setor, aplica Inverse Volatility para definir pesos e rebalanceia todo mês. O objetivo é capturar o prêmio de momentum documentado na literatura sem concentração setorial excessiva.",
        "O primeiro relatório de performance estará disponível em abril, após o fechamento do mês de março. Acompanhe o retorno acumulado versus IBOV a partir daí."
    ]
}

# =============================================================================
# COLETA E CÁLCULO DE MOMENTUM
# =============================================================================

print("Baixando dados do Cumaru...")

data_janela = yf.download(
    ALL_TICKERS,
    start=JANELA_START,
    end=JANELA_END,
    auto_adjust=True,
    progress=False
)['Close']

data_janela = data_janela.dropna(axis=1, thresh=200)
data_janela.ffill(inplace=True)
tickers_disponiveis = list(data_janela.columns)

idx      = data_janela.index
ref_hoje = pd.Timestamp(AVALIACAO_END)
data_12m = ref_hoje - timedelta(days=365)
data_1m  = ref_hoje - timedelta(days=30)

def idx_mais_proximo(datas_index, data_alvo):
    diffs = abs(datas_index - data_alvo)
    return diffs.argmin()

i_12m = idx_mais_proximo(idx, data_12m)
i_1m  = idx_mais_proximo(idx, data_1m)

momentum_scores = {}
for t in tickers_disponiveis:
    p_12m = data_janela[t].iloc[i_12m]
    p_1m  = data_janela[t].iloc[i_1m]
    if pd.isna(p_12m) or pd.isna(p_1m) or p_12m == 0:
        momentum_scores[t] = np.nan
    else:
        momentum_scores[t] = (p_1m / p_12m) - 1

# Seleção top 2 por setor com momentum positivo
ativos_selecionados = []
for setor, tickers in IBOV_UNIVERSE.items():
    candidatos = []
    for t in tickers:
        if t not in tickers_disponiveis:
            continue
        score = momentum_scores.get(t, np.nan)
        if not pd.isna(score) and score > 0:
            candidatos.append((t, score))
    candidatos.sort(key=lambda x: x[1], reverse=True)
    ativos_selecionados.extend([t for t, _ in candidatos[:2]])

# Pesos Inverse Volatility
retornos     = data_janela[ativos_selecionados].pct_change().dropna()
vol          = retornos.std()
vol          = vol[vol > 0].dropna()
ativos_validos = [t for t in ativos_selecionados if t in vol.index]
inv_vol      = 1 / vol[ativos_validos]
pesos        = inv_vol / inv_vol.sum()

# =============================================================================
# PERFORMANCE (dados a partir da abertura)
# =============================================================================

data_aval = yf.download(
    ativos_validos,
    start=AVALIACAO_START,
    end=AVALIACAO_END,
    auto_adjust=True,
    progress=False
)['Close']
data_aval.ffill(inplace=True)
data_aval.bfill(inplace=True)

ibov = yf.download('^BVSP', start=AVALIACAO_START, end=AVALIACAO_END, auto_adjust=True)['Close']
ibov.ffill(inplace=True)

precos_ini = data_aval.iloc[0]
precos_fim = data_aval.iloc[-1]
stop_loss  = -2 * vol * np.sqrt(252)

patrimonio = 0
ativos_out = []

for t in ativos_validos:
    ticker_clean  = t.replace('.SA', '')
    peso          = float(pesos[t])
    valor_alocado = CAPITAL_INICIAL * peso
    preco_entrada = float(precos_ini[t])
    preco_atual   = float(precos_fim[t])
    cotas         = valor_alocado / preco_entrada if preco_entrada > 0 else 0
    retorno       = (preco_atual / preco_entrada) - 1
    valor_atual   = valor_alocado * (1 + retorno)
    patrimonio   += valor_atual
    vol_anual     = float(vol[t] * np.sqrt(252))
    score         = momentum_scores.get(t, np.nan)
    setor_ativo   = next((s for s, ts in IBOV_UNIVERSE.items() if t in ts), 'N/A')

    ativos_out.append({
        'ticker':        ticker_clean,
        'setor':         setor_ativo,
        'peso':          round(peso * 100, 2),
        'score_mom':     round(float(score) * 100, 2) if not pd.isna(score) else None,
        'preco_entrada': round(preco_entrada, 2),
        'preco_atual':   round(preco_atual, 2),
        'cotas':         round(cotas, 4),
        'valor_alocado': round(valor_alocado, 2),
        'valor_atual':   round(valor_atual, 2),
        'vol_anual':     round(vol_anual * 100, 2),
        'stop_pct':      round(float(stop_loss[t]) * 100, 2),
        'retorno':       round(retorno * 100, 2),
        'stop_atingido': bool(retorno < float(stop_loss[t])),
    })

# Curva de performance (base 100)
pesos_series            = pd.Series({t: float(pesos[t]) for t in ativos_validos})
retornos_diarios        = data_aval[ativos_validos].pct_change().fillna(0)
retorno_carteira_diario = retornos_diarios.dot(pesos_series)
retorno_ibov_diario     = ibov.pct_change().fillna(0).squeeze()

curva_c = (1 + retorno_carteira_diario).cumprod() * 100
curva_i = (1 + retorno_ibov_diario).cumprod() * 100

peak_c  = curva_c.cummax()
peak_i  = curva_i.cummax()
dd_c    = (curva_c - peak_c) / peak_c * 100
dd_i    = (curva_i - peak_i) / peak_i * 100

# Amostragem mensal
datas_mensais   = curva_c.resample('ME').last()
labels_grafico  = ['Início'] + [d.strftime('%b/%y') for d in datas_mensais.index]
curva_c_graf    = [100.0] + [round(v, 2) for v in datas_mensais.values]
curva_i_graf    = [100.0] + [round(v, 2) for v in curva_i.resample('ME').last().values]
dd_c_graf       = [0.0]   + [round(v, 2) for v in dd_c.resample('ME').last().values]
dd_i_graf       = [0.0]   + [round(v, 2) for v in dd_i.resample('ME').last().values]

retorno_total  = (patrimonio / CAPITAL_INICIAL) - 1
retorno_ibov_t = float((ibov.iloc[-1] / ibov.iloc[0]).values[0]) - 1
alpha          = retorno_total - retorno_ibov_t
dd_max         = float(dd_c.min())
vol_carteira   = float(retorno_carteira_diario.std() * np.sqrt(252) * 100)

# Retorno por setor
setor_ret  = {}
setor_peso = {}
for a in ativos_out:
    s = a['setor']
    setor_ret[s]  = setor_ret.get(s, 0)  + a['retorno']  * (a['peso'] / 100)
    setor_peso[s] = setor_peso.get(s, 0) + a['peso']

setores_dados = sorted(
    [{'setor': k, 'retorno': round(setor_ret[k], 2), 'peso': round(setor_peso[k], 2)} for k in setor_ret],
    key=lambda x: x['peso'], reverse=True
)

# Interpola placeholders na carta
n_ativos  = len(ativos_validos)
n_setores = len(set(a['setor'] for a in ativos_out))

def interpola(txt):
    return (txt
        .replace('{alpha}',    f"{'+' if alpha*100 >= 0 else ''}{alpha*100:.2f}%")
        .replace('{ibov}',     f"{'+' if retorno_ibov_t*100 >= 0 else ''}{retorno_ibov_t*100:.2f}%")
        .replace('{retorno}',  f"{'+' if retorno_total*100 >= 0 else ''}{retorno_total*100:.2f}%")
        .replace('{n_ativos}', str(n_ativos))
        .replace('{n_setores}', str(n_setores))
    )

carta_final = {
    "titulo": CARTA_MENSAL["titulo"],
    "data":   CARTA_MENSAL["data"],
    "corpo":  [interpola(p) for p in CARTA_MENSAL["corpo"]]
}

# =============================================================================
# EXPORTAR JSON
# =============================================================================

output = {
    "meta": {
        "fundo":              "Cumaru",
        "estrategia":         "Momentum 12-1 Puro · Top 2 por Setor IBOV · Inverse Volatility",
        "capital_inicial":    CAPITAL_INICIAL,
        "patrimonio_atual":   round(patrimonio, 2),
        "retorno_acumulado":  round(retorno_total * 100, 2),
        "retorno_ibov":       round(retorno_ibov_t * 100, 2),
        "alpha":              round(alpha * 100, 2),
        "drawdown_max":       round(dd_max, 2),
        "volatilidade_anual": round(vol_carteira, 2),
        "periodo_inicio":     AVALIACAO_START,
        "periodo_fim":        AVALIACAO_END,
        "n_ativos":           n_ativos,
        "n_setores":          n_setores,
        "benchmark":          "IBOV",
        "proxima_rebal":      (pd.Timestamp(AVALIACAO_END) + timedelta(days=30)).strftime('%d/%m/%Y'),
    },
    "curva": {
        "labels":      labels_grafico,
        "carteira":    curva_c_graf,
        "ibov":        curva_i_graf,
        "dd_carteira": dd_c_graf,
        "dd_ibov":     dd_i_graf,
    },
    "ativos":        ativos_out,
    "setores":       setores_dados,
    "log":           LOG,
    "carta_mensal":  carta_final,
}

with open('cumaru_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✓ cumaru_data.json exportado com sucesso.")
print(f"  Patrimônio: R$ {patrimonio:,.2f}")
print(f"  Retorno:    {retorno_total*100:.2f}%")
print(f"  Alpha:      {alpha*100:.2f}%")
print(f"  Ativos:     {n_ativos} | Setores: {n_setores}")
print(f"  Período:    {AVALIACAO_START} → {AVALIACAO_END}")
