# Como rodar o pipeline de NLP na máquina com GPU

Extrai sentimento geral (1–5 estrelas) e sentimento por aspecto (limpeza, staff,
localização, conforto, comida, custo-benefício, ruído, facilidades) de todas as
reviews, usando **modelos gratuitos e locais** (nenhum dado sai da máquina).

## 1. Pré-requisitos

- Python 3.10+ e uma GPU NVIDIA com CUDA.
- Copiar o projeto para a máquina com GPU (com a pasta `data/Hotel_Reviews.csv`).

## 2. Instalar dependências

```bash
pip install -r requirements.txt
```

> Importante: instale a versão de **PyTorch com CUDA** compatível com a GPU
> (veja https://pytorch.org). O `requirements.txt` pede `torch` genérico; numa
> máquina com GPU, instale o wheel CUDA para usar a placa de verdade.
> Verifique com: `python -c "import torch; print(torch.cuda.is_available())"` → deve dar `True`.

## 3. Teste de fumaça primeiro (obrigatório)

Rode numa amostra pequena para confirmar que a GPU está sendo usada e o download
dos modelos (~1 GB no total, só na 1ª vez) funcionou:

```bash
python src/nlp_pipeline.py --sample 500 --batch-size 64
```

Deve logar `CUDA GPU detected: ...` e salvar `outputs/reviews_enriched_sample.parquet`.

## 4. Rodada completa

```bash
python src/nlp_pipeline.py --batch-size 128
```

- Ajuste `--batch-size` conforme a VRAM (128–256 para GPUs de 8–12 GB).
- Tempo estimado: **~1–3 h** numa GPU tipo T4/RTX 3060 (515k reviews).
- Saída: `outputs/reviews_enriched.parquet` — uma linha por review, com
  `overall_stars` e uma coluna `aspect_<nome>` por aspecto
  (`positive` / `negative` / `neutral` / `not_mentioned`).

## 5. Devolver o resultado

Traga de volta o arquivo `outputs/reviews_enriched.parquet`. A partir dele eu
construo o painel hotel × trimestre e as features (fase seguinte, roda em CPU).

## Notas técnicas

- **Aspectos** são "abertos" por palavra-chave (`ASPECT_LEXICON` em
  `src/nlp_pipeline.py`) antes de rodar o ABSA — assim o modelo só pontua o que
  a review realmente menciona. Para adicionar um aspecto de negócio, basta
  incluir uma entrada nesse dicionário.
- Reviews e pares (texto, aspecto) são **deduplicados** antes da inferência.
- Modelos usados (gratuitos):
  - `nlptown/bert-base-multilingual-uncased-sentiment` (sentimento geral)
  - `yangheng/deberta-v3-base-absa-v1.1` (sentimento por aspecto)
