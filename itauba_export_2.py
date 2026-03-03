"""
itauba_export.py — Wood Capital
================================
Gera itauba_data.json com todos os dados necessários para o dashboard HTML.
Execute mensalmente após o fechamento do período.

Uso:
    python itauba_export.py

Saída:
    itauba_data.json  → suba junto com o index.html no GitHub Pages
"""

import yfinance as yf
import pandas as pd
import numpy as np
import json
from datetime import date, timedelta

# =============================================================================
# CONFIGURAÇÕES
# =============================================================================

CAPITAL_INICIAL  = 100_000
CALIBRACAO_START = '2025-01-01'
CALIBRACAO_END   = '2025-12-31'
AVALIACAO_START  = '2026-01-02'
AVALIACAO_END    = '2026-02-27'  # ← atualizar todo mês antes de rodar

MOMENTUM_END   = (date.today() - timedelta(days=30)).strftime('%Y-%m-%d')
MOMENTUM_START = (date.today() - timedelta(days=365)).strftime('%Y-%m-%d')

TICKERS = [
    'BPAC11.SA', 'ROXO34.SA', 'INBR32.SA', 'VALE3.SA',  'PETR4.SA',
    'ENEV3.SA',  'EQTL3.SA',  'EGIE3.SA',  'AZZA3.SA',  'KEPL3.SA',
    'TOTS3.SA',  'WEGE3.SA',  'GMAT3.SA'
]

# Mapeamento pilar por ticker
PILARES = {
    'GMAT3':  'Descentralização',
    'WEGE3':  'Energia',
    'ENEV3':  'Energia',
    'EGIE3':  'Energia',
    'EQTL3':  'Energia',
    'VALE3':  'Commodities',
    'PETR4':  'Commodities',
    'KEPL3':  'Commodities',
    'BPAC11': 'Financeiro/Digital',
    'TOTS3':  'Financeiro/Digital',
    'ROXO34': 'Financeiro/Digital',
    'INBR32': 'Financeiro/Digital',
    'AZZA3':  'Consumo',
}

# Status manual — atualizar mensalmente
STATUS = {
    'GMAT3':  'Hold',
    'WEGE3':  'Hold',
    'ENEV3':  'Watch',
    'EGIE3':  'Watch',
    'EQTL3':  'Hold',
    'VALE3':  'Hold',
    'PETR4':  'Hold',
    'KEPL3':  'Watch',
    'BPAC11': 'Hold',
    'TOTS3':  'Watch',
    'ROXO34': 'Hold',
    'INBR32': 'Watch',
    'AZZA3':  'Hold',
}

# Log de operações — adicionar manualmente ao longo do tempo
LOG = [
    {
        "data": "Jan 2026",
        "tipo": "Abertura",
        "descricao": "Montagem da carteira v1 — 13 ativos, 5 pilares",
        "motivo": "Estratégia Inverse Volatility calibrada em 2025. Capital inicial R$ 100.000.",
        "resultado": "—"
    },
    {
        "data": "Fev 2026",
        "tipo": "Saída",
        "descricao": "NEOE3 → EQTL3",
        "motivo": "OPA da Neoenergia sem upside residual. Equatorial como substituta estrutural no pilar energia.",
        "resultado": "-0.4%"
    },
    {
        "data": "Fev 2026",
        "tipo": "Revisão",
        "descricao": "Filtro Momentum 12-1 aplicado — v2",
        "motivo": "EGIE3 e TOTS3 com momentum negativo: peso reduzido à metade. PETR4 e GMAT3 reforçados.",
        "resultado": "Rebal."
    },
    {
        "data": "Fev 2026",
        "tipo": "Tese",
        "descricao": "PETR4 — catalisador geopolítico",
        "motivo": "Operação Epic Fury (28/02). Ormuz fechado. Petróleo +7%. P/L ~6x, yield ~14%. Posição mantida.",
        "resultado": "+11.3%"
    },
    {
        "data": "Mar 2026",
        "tipo": "Pendente",
        "descricao": "Rebalanceamento mensal — Cumaru e Itaúba",
        "motivo": "Avaliar saída de TOTS3 e INBR32. Manter AZZA3 por tese de valuation. Novo filtro momentum.",
        "resultado": "—"
    },
]

# Carta mensal — editar todo mês antes de rodar o script
CARTA_MENSAL = {
    "titulo": "Janeiro · Fevereiro 2026 — Tese certa, mercado mais rápido",
    "data": "Mar 2026",
    "corpo": [
        "PETR4 acumulou +11,3% no período por uma convergência de três vetores: alta de ~14% no Brent desde o início do ano, entrada de ~R$36 bilhões de capital estrangeiro na B3 com a Petrobras como principal porta de acesso, e expectativa de dividendos ordinários de R$0,94/ação com pagamento em fevereiro e março. A ação entrou no portfólio por P/L ~6x e yield ~14% — não como aposta geopolítica. O fechamento de Ormuz no dia 28 adicionou impulso pontual ao final do período, mas a alta já estava feita.",
        "ROXO34 foi o ponto de atrito do período. O BDR acumulou queda de ~8% em 2026 apesar de um resultado operacional robusto no 4T25 — lucro líquido de US$895 milhões (+50% a/a), ROE de 33%, recorde histórico. A queda veio de fora: um relatório de research nos EUA reacendeu o temor de que a inteligência artificial possa afetar o setor financeiro, pressionando fintechs de crescimento. O mercado pune o múltiplo antes de qualquer deterioração de fundamento. A tese permanece intacta — o Nubank negocia a ~20x P/L 2026 com crescimento de crédito de 40% a/a e licença bancária nos EUA avançando.",
        "O pilar de energia pesou negativamente via EGIE3 e ENEV3. A EGIE3 enfrenta pressão de juros altos e vencimento relevante de debêntures no horizonte — aguardamos o resultado do próximo trimestre antes de qualquer decisão. ENEV3 mantém tese intacta pela flexibilidade térmica, mas o risco regulatório da ANEEL permanece monitorado.",
        "Alpha negativo de -9,12 p.p. está dentro do esperado para uma estratégia estruturalmente defensiva. O IBOV subiu 17,6% puxado por ativos de alto beta que intencionalmente não carregamos. O portfólio não foi construído para ganhar em janeiro — foi construído para não perder em dezembro de 2027."
    ]
}

# =============================================================================
# COLETA E CÁLCULO
# =============================================================================

print("Baixando dados...")

data_cal  = yf.download(TICKERS, start=CALIBRACAO_START, end=CALIBRACAO_END,  auto_adjust=True)['Close']
data_aval = yf.download(TICKERS, start=AVALIACAO_START,  end=AVALIACAO_END,   auto_adjust=True)['Close']
data_mom  = yf.download(TICKERS, start=MOMENTUM_START,   end=MOMENTUM_END,    auto_adjust=True)['Close']
ibov      = yf.download('^BVSP', start=AVALIACAO_START,  end=AVALIACAO_END,   auto_adjust=True)['Close']

for df in [data_aval, data_mom, ibov]:
    df.ffill(inplace=True)
    df.bfill(inplace=True)

# Volatilidade e pesos base
retornos_cal = data_cal.pct_change().dropna()
vol          = retornos_cal.std()
vol_anual    = vol * np.sqrt(252)
inv_vol      = 1 / vol
pesos_base   = inv_vol / inv_vol.sum()

# Momentum
momentum_scores = {}
for t in TICKERS:
    if t in data_mom.columns:
        serie = data_mom[t].dropna()
        momentum_scores[t] = (serie.iloc[-1] / serie.iloc[0]) - 1 if len(serie) >= 2 else np.nan
    else:
        momentum_scores[t] = np.nan

# Pesos ajustados
pesos_ajustados = {}
for t in TICKERS:
    score = momentum_scores.get(t, np.nan)
    pesos_ajustados[t] = pesos_base[t] if (pd.isna(score) or score >= 0) else pesos_base[t] * 0.5

total_peso      = sum(pesos_ajustados.values())
pesos_ajustados = {t: p / total_peso for t, p in pesos_ajustados.items()}

# Performance
precos_ini = data_aval.iloc[0]
precos_fim = data_aval.iloc[-1]
stop_loss  = -2 * vol_anual
patrimonio = 0
ativos     = []

for t in TICKERS:
    ticker_clean  = t.replace('.SA', '')
    peso          = pesos_ajustados[t]
    valor_alocado = CAPITAL_INICIAL * peso
    retorno       = (precos_fim[t] / precos_ini[t]) - 1
    valor_final   = valor_alocado * (1 + retorno)
    patrimonio   += valor_final
    score         = momentum_scores.get(t, np.nan)

    ativos.append({
        'ticker':        ticker_clean,
        'pilar':         PILARES.get(ticker_clean, '—'),
        'status':        STATUS.get(ticker_clean, '—'),
        'peso_base':     round(float(pesos_base[t]) * 100, 2),
        'peso_final':    round(float(peso) * 100, 2),
        'vol_anual':     round(float(vol_anual[t]) * 100, 2),
        'momentum':      round(float(score) * 100, 2) if not pd.isna(score) else None,
        'mom_status':    'Positivo' if (not pd.isna(score) and score >= 0) else 'Negativo',
        'retorno':       round(float(retorno) * 100, 2),
        'valor_final':   round(float(valor_final), 2),
        'stop_pct':      round(float(stop_loss[t]) * 100, 2),
        'stop_atingido': bool(retorno < stop_loss[t]),
    })

# Curva mensal normalizada (base 100)
retornos_diarios = data_aval.pct_change().fillna(0)
pesos_series     = pd.Series({t: pesos_ajustados[t] for t in TICKERS})
retorno_carteira_diario = retornos_diarios[TICKERS].dot(pesos_series)
retorno_ibov_diario     = ibov.pct_change().fillna(0).squeeze()

curva_carteira = (1 + retorno_carteira_diario).cumprod() * 100
curva_ibov     = (1 + retorno_ibov_diario).cumprod() * 100

# Drawdown
peak_c = curva_carteira.cummax()
peak_i = curva_ibov.cummax()
dd_c   = ((curva_carteira - peak_c) / peak_c * 100)
dd_i   = ((curva_ibov   - peak_i) / peak_i * 100)

# Amostrar mensalmente para o gráfico
datas_mensais = curva_carteira.resample('ME').last()
labels_grafico = ['Início'] + [d.strftime('%b/%y') for d in datas_mensais.index]
curva_c_grafico = [100.0] + [round(v, 2) for v in datas_mensais.values]
curva_i_grafico = [100.0] + [round(v, 2) for v in curva_ibov.resample('ME').last().values]
dd_c_grafico    = [0.0]   + [round(v, 2) for v in dd_c.resample('ME').last().values]
dd_i_grafico    = [0.0]   + [round(v, 2) for v in dd_i.resample('ME').last().values]

retorno_total   = (patrimonio / CAPITAL_INICIAL) - 1
retorno_ibov_t  = float((ibov.iloc[-1] / ibov.iloc[0]).values[0]) - 1
alpha           = retorno_total - retorno_ibov_t
dd_max          = float(dd_c.min())
vol_carteira    = float(retorno_carteira_diario.std() * np.sqrt(252) * 100)

# Retorno por pilar
pilar_ret = {}
pilar_peso = {}
for a in ativos:
    p = a['pilar']
    pilar_ret[p]  = pilar_ret.get(p, 0)  + a['retorno']  * (a['peso_final'] / 100)
    pilar_peso[p] = pilar_peso.get(p, 0) + a['peso_final']

pilares_dados = [
    {'pilar': k, 'retorno': round(pilar_ret[k], 2), 'peso': round(pilar_peso[k], 2)}
    for k in pilar_ret
]

# =============================================================================
# EXPORTAR JSON
# =============================================================================

output = {
    "meta": {
        "fundo": "Itaúba",
        "estrategia": "Inverse Volatility + Filtro Momentum 12-1",
        "capital_inicial": CAPITAL_INICIAL,
        "patrimonio_atual": round(patrimonio, 2),
        "retorno_acumulado": round(retorno_total * 100, 2),
        "retorno_ibov": round(retorno_ibov_t * 100, 2),
        "alpha": round(alpha * 100, 2),
        "drawdown_max": round(dd_max, 2),
        "volatilidade_anual": round(vol_carteira, 2),
        "periodo_inicio": AVALIACAO_START,
        "periodo_fim": AVALIACAO_END,
        "n_ativos": len(TICKERS),
        "benchmark": "IBOV",
    },
    "curva": {
        "labels":     labels_grafico,
        "carteira":   curva_c_grafico,
        "ibov":       curva_i_grafico,
        "dd_carteira": dd_c_grafico,
        "dd_ibov":    dd_i_grafico,
    },
    "ativos": ativos,
    "pilares": pilares_dados,
    "log": LOG,
    "carta_mensal": CARTA_MENSAL,
}

with open('itauba_data.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"\n✓ itauba_data.json exportado com sucesso.")
print(f"  Patrimônio: R$ {patrimonio:,.2f}")
print(f"  Retorno:    {retorno_total*100:.2f}%")
print(f"  Alpha:      {alpha*100:.2f}%")
print(f"  Período:    {AVALIACAO_START} → {AVALIACAO_END}")
