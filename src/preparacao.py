"""Funções de carga e preparação da base de NPS.

Ficam aqui (e não só no notebook) para que o tratamento seja o mesmo
em todos os notebooks do projeto (preparação e EDA).
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


def carregar_base_bruta(caminho: Path = CAMINHO_BASE_BRUTA) -> pd.DataFrame:
    """Lê o CSV original sem nenhuma alteração."""
    return pd.read_csv(caminho)


def carregar_base_tratada(caminho: Path = CAMINHO_BASE_TRATADA) -> pd.DataFrame:
    """Lê a base tratada e restaura a ordem das faixas (o CSV não guarda essa ordem)."""
    df = pd.read_csv(caminho)
    ordens = {
        "nps_categoria": ORDEM_NPS_CATEGORIA,
        "faixa_atraso": ["Sem atraso", "1-2 dias", "3-4 dias", "5+ dias"],
        "faixa_contatos": ["Nenhum", "1-2 contatos", "3+ contatos"],
        "faixa_idade": ["18-29", "30-44", "45-59", "60+"],
        "faixa_tempo_cliente": ["Até 1 ano", "1-3 anos", "3-6 anos", "6+ anos"],
    }
    for coluna, ordem in ordens.items():
        df[coluna] = pd.Categorical(df[coluna], categories=ordem, ordered=True)
    return df


def classificar_nps(nota: float) -> str:
    """Converte a nota (0 a 10) em Detrator, Neutro ou Promotor."""
    if nota >= LIMITE_PROMOTOR:
        return "Promotor"
    if nota >= LIMITE_NEUTRO:
        return "Neutro"
    return "Detrator"


def calcular_nps(notas: pd.Series) -> float:
    """NPS = % de promotores - % de detratores (vai de -100 a +100)."""
    categorias = notas.apply(classificar_nps)
    pct_promotores = (categorias == "Promotor").mean()
    pct_detratores = (categorias == "Detrator").mean()
    return round((pct_promotores - pct_detratores) * 100, 1)


def criar_variaveis(df: pd.DataFrame) -> pd.DataFrame:
    """Adiciona as variáveis derivadas usadas na EDA. Não altera as colunas originais."""
    df = df.copy()

    # Alvo em formato de negócio
    df["nps_categoria"] = pd.Categorical(
        df["nps_score"].apply(classificar_nps), categories=ORDEM_NPS_CATEGORIA, ordered=True
    )
    df["flag_detrator"] = (df["nps_categoria"] == "Detrator").astype(int)

    # Logística: atrasou ou não, e faixas de atraso para os gráficos
    df["flag_atraso"] = (df["delivery_delay_days"] > 0).astype(int)
    df["faixa_atraso"] = pd.cut(
        df["delivery_delay_days"],
        bins=[-1, 0, 2, 4, np.inf],
        labels=["Sem atraso", "1-2 dias", "3-4 dias", "5+ dias"],
    )

    # Pedido: peso do desconto e do frete.
    # Hipótese: order_value é o valor já com desconto (líquido). É a única leitura
    # em que os pedidos com desconto maior que order_value fazem sentido.
    valor_bruto = df["order_value"] + df["discount_value"]
    df["pct_desconto"] = (df["discount_value"] / valor_bruto).round(3)
    df["pct_frete"] = (df["freight_value"] / df["order_value"]).round(3)

    # Atendimento: faixas de contatos
    df["faixa_contatos"] = pd.cut(
        df["customer_service_contacts"],
        bins=[-1, 0, 2, np.inf],
        labels=["Nenhum", "1-2 contatos", "3+ contatos"],
    )

    # Perfil do cliente
    df["faixa_idade"] = pd.cut(
        df["customer_age"],
        bins=[17, 29, 44, 59, np.inf],
        labels=["18-29", "30-44", "45-59", "60+"],
    )
    df["faixa_tempo_cliente"] = pd.cut(
        df["customer_tenure_months"],
        bins=[0, 12, 36, 72, np.inf],
        labels=["Até 1 ano", "1-3 anos", "3-6 anos", "6+ anos"],
    )

    return df
