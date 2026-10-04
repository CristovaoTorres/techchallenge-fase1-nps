"""Funções de carga e preparação da base de NPS.

Ficam aqui (e não só no notebook) para que o tratamento seja o mesmo
em todos os notebooks do projeto (preparação e EDA). Todas as faixas e
limiares usados nas análises estão definidos neste módulo, em um único
lugar, para que notebook e CSV nunca fiquem com rótulos diferentes.
"""

from pathlib import Path

import numpy as np
import pandas as pd

# Caminhos a partir da raiz do projeto (a pasta acima de src/)
RAIZ_PROJETO = Path(__file__).resolve().parents[1]
CAMINHO_BASE_BRUTA = RAIZ_PROJETO / "data" / "raw" / "desafio_nps_fase_1.csv"
CAMINHO_BASE_TRATADA = RAIZ_PROJETO / "data" / "processed" / "nps_tratado.csv"

# Limites da metodologia NPS. As notas desta base têm casas decimais,
# por isso usamos "menor que 7" em vez de "de 0 a 6": um 6,8 ainda não é nota 7.
LIMITE_NEUTRO = 7
LIMITE_PROMOTOR = 9

# Ordem das faixas, usada nos gráficos e tabelas
ORDEM_NPS_CATEGORIA = ["Detrator", "Neutro", "Promotor"]

# Faixas de apresentação: fonte única de verdade para `criar_variaveis` (que as cria)
# e `carregar_base_tratada` (que restaura a ordem, perdida ao salvar em CSV).
# Os cortes foram escolhidos para separar grupos com tamanho razoável e leitura
# simples para o gestor ("1-2 dias", "3+ contatos").
FAIXAS = {
    "faixa_atraso": {
        "coluna": "delivery_delay_days",
        "bins": [-1, 0, 2, 4, np.inf],
        "labels": ["Sem atraso", "1-2 dias", "3-4 dias", "5+ dias"],
    },
    "faixa_contatos": {
        "coluna": "customer_service_contacts",
        "bins": [-1, 0, 2, np.inf],
        "labels": ["Nenhum", "1-2 contatos", "3+ contatos"],
    },
    "faixa_reclamacoes": {
        "coluna": "complaints_count",
        "bins": [-1, 1, 3, 5, np.inf],
        "labels": ["0-1", "2-3", "4-5", "6+"],
    },
    "faixa_resolucao": {
        "coluna": "resolution_time_days",
        "bins": [-1, 3, 7, np.inf],
        "labels": ["Até 3 dias", "4-7 dias", "8+ dias"],
    },
    "faixa_idade": {
        "coluna": "customer_age",
        "bins": [18, 29, 44, 59, np.inf],
        "labels": ["18-29", "30-44", "45-59", "60+"],
    },
    "faixa_tempo_cliente": {
        "coluna": "customer_tenure_months",
        "bins": [0, 12, 36, 72, np.inf],
        "labels": ["Até 1 ano", "1-3 anos", "3-6 anos", "6+ anos"],
    },
}

# Tipos de jornada (usados na EDA, pergunta 4). "Perfeita" exige TODAS as condições;
# "Crítica" basta UMA. Os limiares vêm da própria EDA: a partir de 3 dias de atraso ou
# 3 contatos, 95%+ dos clientes são detratores; 6+ reclamações é a faixa mais alta.
ORDEM_TIPO_JORNADA = ["Perfeita", "Intermediária", "Crítica"]
JORNADA_PERFEITA = {"delivery_delay_days": 0, "complaints_count": 1, "customer_service_contacts": 1}
JORNADA_CRITICA = {"delivery_delay_days": 3, "complaints_count": 6, "customer_service_contacts": 3}

# Quartis do valor do pedido (os rótulos são gerados a partir dos dados, nunca fixos)
QUANTIS_VALOR_PEDIDO = 4


def carregar_base_bruta(caminho: Path = CAMINHO_BASE_BRUTA) -> pd.DataFrame:
    """Lê o CSV original sem nenhuma alteração.

    Args:
        caminho: Arquivo CSV da base bruta (padrão: ``data/raw/desafio_nps_fase_1.csv``).

    Returns:
        DataFrame com as 19 colunas originais, exatamente como no arquivo.
    """
    return pd.read_csv(caminho)


def carregar_base_tratada(caminho: Path = CAMINHO_BASE_TRATADA) -> pd.DataFrame:
    """Lê a base tratada e restaura a ordem das faixas (o CSV não guarda essa ordem).

    Args:
        caminho: Arquivo CSV gerado pelo notebook ``02_preparacao_dados``.

    Returns:
        DataFrame com as colunas originais, as derivadas de ``criar_variaveis`` e as
        flags de inconsistência. As colunas de faixa voltam como ``Categorical`` ordenado.
    """
    df = pd.read_csv(caminho)
    ordens = {nome: faixa["labels"] for nome, faixa in FAIXAS.items()}
    ordens["nps_categoria"] = ORDEM_NPS_CATEGORIA
    ordens["tipo_jornada"] = ORDEM_TIPO_JORNADA
    # Os rótulos dos quartis dependem dos dados: ordenamos pelo menor valor de cada faixa
    ordens["faixa_valor_pedido"] = (
        df.groupby("faixa_valor_pedido")["order_value"].min().sort_values().index.tolist()
    )
    for coluna, ordem in ordens.items():
        df[coluna] = pd.Categorical(df[coluna], categories=ordem, ordered=True)
    return df


def classificar_nps(nota: float) -> str:
    """Converte a nota (0 a 10) em Detrator, Neutro ou Promotor.

    Args:
        nota: Nota dada pelo cliente, de 0 a 10 (pode ter casas decimais).

    Returns:
        ``"Promotor"`` se nota >= 9, ``"Neutro"`` se 7 <= nota < 9, ``"Detrator"`` se nota < 7.
    """
    if nota >= LIMITE_PROMOTOR:
        return "Promotor"
    if nota >= LIMITE_NEUTRO:
        return "Neutro"
    return "Detrator"


def calcular_nps(notas: pd.Series) -> float:
    """NPS = % de promotores - % de detratores (vai de -100 a +100).

    Args:
        notas: Série (ou array) com as notas de 0 a 10.

    Returns:
        NPS arredondado a uma casa decimal.
    """
    # Mesma regra de `classificar_nps`, em forma vetorizada (rápido o bastante para bootstrap)
    notas = np.asarray(notas, dtype=float)
    pct_promotores = (notas >= LIMITE_PROMOTOR).mean()
    pct_detratores = (notas < LIMITE_NEUTRO).mean()
    return round(float(pct_promotores - pct_detratores) * 100, 1)


def classificar_jornada(df: pd.DataFrame) -> pd.Categorical:
    """Classifica cada pedido em jornada Perfeita, Intermediária ou Crítica.

    Args:
        df: DataFrame com ``delivery_delay_days``, ``complaints_count`` e
            ``customer_service_contacts``.

    Returns:
        ``Categorical`` ordenado (Perfeita < Intermediária < Crítica). Perfeita exige
        todas as condições de ``JORNADA_PERFEITA``; Crítica basta uma de ``JORNADA_CRITICA``.
    """
    perfeita = np.logical_and.reduce(
        [df[coluna] <= limite for coluna, limite in JORNADA_PERFEITA.items()]
    )
    critica = np.logical_or.reduce(
        [df[coluna] >= limite for coluna, limite in JORNADA_CRITICA.items()]
    )
    tipos = pd.Series("Intermediária", index=df.index)
    tipos[critica] = "Crítica"
    tipos[perfeita] = "Perfeita"
    return pd.Categorical(tipos, categories=ORDEM_TIPO_JORNADA, ordered=True)


def rotulos_quartis_reais(serie: pd.Series, quantis: int = QUANTIS_VALOR_PEDIDO) -> list[str]:
    """Gera rótulos como "Até R$220", "R$220-375", ..., a partir dos quantis dos dados.

    Args:
        serie: Valores monetários.
        quantis: Quantidade de faixas (4 = quartis).

    Returns:
        Lista de rótulos, um por faixa, com os cortes reais arredondados.
    """
    cortes = serie.quantile(np.linspace(0, 1, quantis + 1)).round(0).astype(int).tolist()
    rotulos = [f"Até R${cortes[1]}"]
    rotulos += [f"R${cortes[i]}-{cortes[i + 1]}" for i in range(1, quantis - 1)]
    rotulos.append(f"Acima R${cortes[-2]}")
    return rotulos


def criar_variaveis(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona as variáveis derivadas usadas na EDA. Não altera as colunas originais.

    Args:
        df: Base (bruta ou já imputada) com as 19 colunas originais.

    Returns:
        Cópia de ``df`` com as colunas novas: ``nps_categoria``, ``flag_detrator``,
        ``flag_atraso``, ``pct_desconto``, ``pct_frete``, as faixas de ``FAIXAS``,
        ``faixa_valor_pedido`` e ``tipo_jornada``.
    """
    df = df.copy()

    # Alvo em formato de negócio
    df["nps_categoria"] = pd.Categorical(
        df["nps_score"].apply(classificar_nps), categories=ORDEM_NPS_CATEGORIA, ordered=True
    )
    df["flag_detrator"] = (df["nps_categoria"] == "Detrator").astype(int)

    # Logística: atrasou ou não (as faixas de atraso vêm de FAIXAS, abaixo)
    df["flag_atraso"] = (df["delivery_delay_days"] > 0).astype(int)

    # Pedido: peso do desconto e do frete.
    # Hipótese: order_value é o valor já com desconto (líquido). É a única leitura
    # em que os pedidos com desconto maior que order_value fazem sentido.
    valor_bruto = df["order_value"] + df["discount_value"]
    df["pct_desconto"] = (df["discount_value"] / valor_bruto).round(3)
    # Um pedido de valor zero (não há nenhum na base) ficaria sem % de frete, em vez de
    # gerar divisão por zero
    df["pct_frete"] = (df["freight_value"] / df["order_value"].where(df["order_value"] > 0)).round(
        3
    )

    # Faixas de apresentação (atraso, contatos, reclamações, resolução, idade, tempo de casa).
    # include_lowest garante que o menor valor possível (18 na idade, 0 no tempo de casa) entre
    # na 1ª faixa; nas contagens o 1º corte é -1 para que o zero caia em "Sem atraso"/"Nenhum".
    for nome, faixa in FAIXAS.items():
        df[nome] = pd.cut(
            df[faixa["coluna"]], bins=faixa["bins"], labels=faixa["labels"], include_lowest=True
        )

    # Valor do pedido em quartis, com rótulos calculados dos próprios dados
    df["faixa_valor_pedido"] = pd.qcut(
        df["order_value"],
        QUANTIS_VALOR_PEDIDO,
        labels=rotulos_quartis_reais(df["order_value"]),
    )

    # Tipo de jornada (pergunta 4 da EDA)
    df["tipo_jornada"] = classificar_jornada(df)

    return df
