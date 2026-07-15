Este projeto foi desenvolvido para o case técnico de Estágio em Growth AI-Native do Méliuz.

A proposta é automatizar a análise de testes A/B de cashback. A solução recebe um arquivo CSV, valida os dados, calcula as principais métricas de negócio, analisa as diferenças entre as variantes e gera uma recomendação sobre qual grupo deve ser escalado.

A mesma estrutura funciona para os três datasets fornecidos, alterando apenas o caminho do arquivo de entrada.

## Como a solução funciona

O fluxo de análise é dividido em quatro etapas:

1. leitura e validação do CSV;
2. cálculo das métricas por grupo;
3. análise estatística e tomada de decisão;
4. geração do relatório e registro do resultado.

A execução é feita pelo arquivo `analisar_teste.py`, que coordena os módulos da pasta `src`.

## Estrutura do projeto

```text
case_meliuz/
├── analisar_teste.py
├── requirements.txt
├── data/
│   ├── dataset_01_parceiroA.csv
│   ├── dataset_02_parceiroB.csv
│   └── dataset_03_parceiroC.csv
├── reports/
├── src/
│   ├── pipeline.py
│   ├── decision.py
│   ├── report.py
│   └── tracking.py
└── tracking/
    └── acompanhamento.csv

