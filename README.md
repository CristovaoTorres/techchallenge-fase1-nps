# NPS Preditivo: o que faz um cliente de e-commerce virar detrator?

**Tech Challenge · Fase 1 · Pós-Tech FIAP AI Scientist**

Análise de dados operacionais de um e-commerce (pedidos, logística e atendimento) para descobrir **quais fatores determinam a satisfação do cliente** e **como a empresa pode agir antes da pesquisa de NPS**.

| Entregável | Link |
|---|---|
| 📊 Slides (storytelling gerencial) | `reports/` *(adicionar link)* |
| 🎥 Vídeo executivo (até 5 min) | *(adicionar link)* |

---

## 1. Objetivo do projeto

A empresa cresceu rápido e passou a ter alta variação de satisfação entre clientes. Hoje o NPS só é coletado **depois** do fim da jornada de compra, quando já não dá para corrigir a experiência.

**Pergunta orientadora:**
> Quais fatores operacionais realmente influenciam a satisfação do cliente e como a empresa pode agir de forma proativa, antes mesmo da aplicação da pesquisa de NPS?

O foco é **entendimento do problema, pensamento analítico e storytelling com dados**: traduzir os dados em recomendações claras para Logística, Atendimento, CX e Estratégia.

## 2. Principais resultados

| | Achado |
|---|---|
| 🚨 **Retrato** | NPS de **−80**: 84% dos clientes são detratores e só 4% são promotores. |
| 🚚 **Fator nº 1** | **Atraso na entrega.** Sem atraso: 52% de detratores. Com 3+ dias: **97–100%**. |
| ⏱️ **Ponto de ruptura** | **3 dias de atraso.** Até o 2º dia ainda dá para recuperar o cliente, depois disso quase ninguém é recuperado. |
| 📦 **Prazo ≠ atraso** | O prazo total de entrega **não** afeta a nota. O que pesa é **quebrar a promessa**. |
| 📞 **Atendimento** | Reclamações e contatos repetidos derrubam a nota: 3+ contatos = 95% de detratores. |
| 👥 **Perfil do cliente** | Região, idade, tempo de casa e valor do pedido **não** mudam o NPS (todos ≈ −80). |
| ✅ **Jornada perfeita** | Sem atraso e sem problemas no atendimento, o NPS é **+9**, mas só 3% dos clientes têm essa experiência. |
| 💰 **Por que importa** | **Nenhum detrator recomprou em 30 dias.** Quem recomprou tem NPS de +50. |

<p align="center">
  <img src="reports/figures/03_06_ponto_ruptura_atraso.png" width="720" alt="Ponto de ruptura: % de detratores por dia de atraso">
</p>

**Mensagem central:** a insatisfação não vem de *quem* é o cliente, mas do *que acontece* com o pedido dele. É um problema **gerenciável pela operação**: cumprir o prazo prometido e resolver o problema no primeiro contato.

## 3. Base de dados

- **Arquivo:** `data/raw/desafio_nps_fase_1.csv` ([fonte original](https://github.com/AnaRaquelCafe/POSTECH_AI_SCIENTIST/blob/main/Base%20de%20dados%20Tech%20Challenge/desafio_nps_fase_1.csv))
- **Tamanho:** 2.500 pedidos × 19 colunas, sem valores nulos nem duplicados, 1 pedido por cliente

| Grupo | Coluna | Descrição |
|---|---|---|
| Identificação | `customer_id`, `order_id` | Identificadores do cliente e do pedido |
| Perfil | `customer_age` | Idade do cliente |
| | `customer_region` | Região geográfica |
| | `customer_tenure_months` | Tempo de relacionamento com a empresa (meses) |
| Pedido | `order_value` | Valor total do pedido |
| | `items_quantity` | Quantidade de itens |
| | `discount_value` | Valor de desconto aplicado |
| | `payment_installments` | Número de parcelas |
| Logística | `delivery_time_days` | Tempo total de entrega (dias) |
| | `delivery_delay_days` | Dias de atraso na entrega |
| | `freight_value` | Valor do frete |
| | `delivery_attempts` | Tentativas de entrega |
| Atendimento | `customer_service_contacts` | Contatos com o atendimento |
| | `resolution_time_days` | Tempo para resolução de problemas (dias) |
| | `complaints_count` | Reclamações registradas |
| Pós-compra* | `repeat_purchase_30d` | Recompra em até 30 dias (0/1) |
| | `csat_internal_score` | Score interno de satisfação |
| **Alvo** | `nps_score` | Nota de NPS (0 a 10), coletada após a experiência de compra |

\* Medidos **junto ou depois** do NPS. Não são usados como fatores explicativos, para evitar *data leakage* (vazamento de informação).

## 4. Metodologia

O projeto segue o **CRISP-DM**. Cada fase corresponde a um notebook:

| Fase CRISP-DM | Notebook | O que faz |
|---|---|---|
| Entendimento do Negócio | [`01_entendimento_negocio`](notebooks/01_entendimento_negocio.ipynb) | Problema de negócio, importância do NPS, áreas beneficiadas, impacto em recompra, boca a boca e market share, definição da target e seus riscos |
| Entendimento + Preparação dos Dados | [`02_preparacao_dados`](notebooks/02_preparacao_dados.ipynb) | Qualidade dos dados, tratamento de inconsistências, outliers, regra de classificação do NPS e variáveis derivadas |
| Análise Exploratória | [`03_eda`](notebooks/03_eda.ipynb) | Responde às 4 perguntas de negócio, com gráficos e textos voltados a gestores não técnicos |

### Principais decisões de tratamento

| Decisão | Justificativa |
|---|---|
| **Classificação do NPS por corte direto** (Detrator < 7 ≤ Neutro < 9 ≤ Promotor) | As notas têm casas decimais. Um 6,8 não chegou a 7. A alternativa de arredondar foi testada (NPS −74 contra −80) e a conclusão não muda. |
| **Imputação pela mediana** do tempo de entrega em 121 pedidos (4,8%) com atraso maior que o tempo total | Excluir esses pedidos tiraria da base os clientes mais insatisfeitos (nota média 2,3 contra 4,5). A **imputação por regressão linear** foi testada e descartada (R² = 0,017). O valor original foi preservado em `delivery_time_days_original`. |
| **Desconto > valor do pedido** (35 pedidos) mantido | Interpretado como valor **líquido**. O % de desconto é calculado sobre o valor bruto. |
| **Outliers mantidos** | São casos reais (atrasos longos, muitos contatos) e justamente os mais relevantes para entender detratores. |
| **CSAT e recompra fora dos fatores explicativos** | Evita *leakage*: essas informações não existem antes da pesquisa de NPS. |

### Limitações

- A análise mostra **associação, não causalidade**. O ideal é validar as recomendações com testes controlados.
- A base não tem datas: não é possível analisar sazonalidade nem a evolução no tempo.
- As notas com decimais e as inconsistências indicam possíveis diferenças na forma de coleta dos dados.
- O modelo preditivo (desafio opcional 4) **não** faz parte do escopo desta entrega.

## 5. Estrutura do repositório

```
├── data/
│   ├── raw/                  # base original (nunca alterada)
│   └── processed/            # base tratada, gerada pelo notebook 02
├── notebooks/
│   ├── 01_entendimento_negocio.ipynb
│   ├── 02_preparacao_dados.ipynb
│   └── 03_eda.ipynb
├── src/
│   └── preparacao.py         # funções de carga, classificação do NPS e variáveis derivadas
├── reports/
│   └── figures/              # gráficos gerados pelos notebooks (usados nos slides)
├── requirements.txt
└── README.md
```

## 6. Como reproduzir

**Pré-requisito:** Python **3.11+**

```bash
# 1. Clonar o repositório
git clone <url-do-repositorio>
cd <pasta-do-repositorio>

# 2. Criar e ativar um ambiente virtual
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# 3. Instalar as dependências
pip install -r requirements.txt

# 4. Abrir os notebooks
jupyter notebook
```

Execute os notebooks **na ordem** `01 → 02 → 03`. O notebook `02` gera `data/processed/nps_tratado.csv`, que é lido pelo `03`. Todos os gráficos são salvos automaticamente em `reports/figures/`.

Para rodar tudo de uma vez pela linha de comando:

```bash
cd notebooks
jupyter nbconvert --to notebook --execute --inplace 02_preparacao_dados.ipynb 03_eda.ipynb
```

## 7. Autores

| Nome | RM |
|---|---|
| *(preencher)* | *(preencher)* |
