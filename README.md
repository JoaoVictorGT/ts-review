# Hotel Reviews — Sistema de Acomodações

Análise de dados e machine learning sobre o dataset [515K Hotel Reviews Data in Europe](https://www.kaggle.com/datasets/jiashenliu/515k-hotel-reviews-data-in-europe) (Kaggle), com o objetivo de construir o MVP de uma plataforma web para gestores de hotéis: analisar reviews históricas, extrair insights acionáveis e prever/explicar a nota média do hotel.

## Estrutura do projeto

```
data/            # dataset bruto (não versionado — ver "Dados" abaixo)
notebooks/        # notebooks de análise exploratória
src/              # pipeline em Python, modular
  data_quality.py       # Fase 1 — auditoria de qualidade do dataset
  panel_feasibility.py  # viabilidade estatística do painel hotel x período
  text_cleaning.py      # diagnóstico e normalização do texto das reviews
  nlp_pipeline.py       # extração de sentimento geral + por aspecto (GPU)
outputs/          # artefatos gerados (parquet, csv) — não versionados (exceto amostra)
figures/          # gráficos gerados pelas análises
reports/          # relatórios em Markdown das auditorias e guias de execução
```

## Dados

O CSV bruto (`Hotel_Reviews.csv`, ~230MB) **não é versionado** no repositório (excede o limite do GitHub). Baixe do Kaggle e coloque em `data/Hotel_Reviews.csv` antes de rodar qualquer script.

## Setup

```bash
pip install -r requirements.txt
```

## Pipeline de NLP (rodar na máquina com GPU)

Veja o passo a passo completo em [`reports/RUN_NLP_ON_GPU.md`](reports/RUN_NLP_ON_GPU.md). Resumo:

```bash
python src/nlp_pipeline.py --sample 500 --batch-size 64   # teste de fumaça
python src/nlp_pipeline.py --batch-size 128                # rodada completa
```

Gera `outputs/reviews_enriched.parquet` — sentimento geral (1–5 estrelas) e por aspecto (limpeza, staff, localização, conforto, comida, custo-benefício, ruído, facilidades) por review, usando modelos gratuitos e locais (`nlptown/bert-base-multilingual-uncased-sentiment` e `yangheng/deberta-v3-base-absa-v1.1` — nenhum dado sai da máquina).

## Auditoria de dados

```bash
python src/data_quality.py         # Fase 1: estrutura, health checks, distribuições
python src/panel_feasibility.py    # viabilidade do painel hotel x trimestre
```

Relatórios em `reports/01_data_audit.md` e figuras em `figures/`.

## Roadmap

1. ✅ Data Audit
2. ✅ Auditoria de texto + estratégia de limpeza/NLP
3. ▶️ Feature engineering — painel hotel x período (target = nota trimestral/semestral reconstruída)
4. Clustering + correlações (benchmarking de pares)
5. Modelagem (regressão de painel) + SHAP
6. Relatório final
