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

## Instalação

Crie um ambiente virtual:

```bash
python -m venv .venv
```

No Windows:

```bash
.venv\Scripts\activate
```

No Linux ou macOS:

```bash
source .venv/bin/activate
```

Depois, instale as dependências:

```bash
pip install -r requirements.txt
```

## Como executar

Exemplo para o Parceiro A:

```bash
python analisar_teste.py data/dataset_01_parceiroA.csv \
  --nome "Cashback Parceiro A" \
  --desc "Teste de porcentagem de cashback"
```

No PowerShell:

```powershell
python analisar_teste.py data\dataset_01_parceiroA.csv --nome "Cashback Parceiro A" --desc "Teste de porcentagem de cashback"
```

Para analisar outro teste, basta informar outro arquivo CSV. Não é necessário alterar o código.

## Métrica principal

A métrica principal escolhida foi a margem líquida:

```text
margem líquida = comissão recebida - cashback distribuído
```

Escolhi essa métrica porque ela representa o valor que permanece para o Méliuz depois do pagamento do cashback.

Além da margem, a análise também considera:

- GMV;
- compradores;
- margem por comprador;
- ticket médio;
- percentual de cashback;
- percentual de margem.

Essas métricas ajudam a identificar casos em que uma variante melhora o resultado financeiro, mas prejudica o volume de vendas ou de compradores.

## Análise estatística

Os datasets possuem uma observação por grupo e por dia.

Como as variantes são observadas nas mesmas datas, as comparações são feitas de forma pareada. Isso ajuda a reduzir a influência de fatores como dia da semana, sazonalidade e mudanças gerais de demanda.

Quando existem mais de duas variantes, é aplicada uma correção para múltiplas comparações.

A solução também verifica se as taxas de cashback permaneceram estáveis durante o período. Caso uma variante mude de configuração ao longo do teste, o experimento é sinalizado como inválido.

## Regra de decisão

A solução pode retornar três tipos de decisão:

- `ESCALAR Grupo X`: há evidência suficiente para recomendar a variante;
- `INCONCLUSIVO — NÃO ESCALAR`: existe uma liderança, mas sem evidência suficiente;
- `TESTE INVÁLIDO — NÃO ESCALAR`: foram encontrados problemas no desenho ou na qualidade do experimento.

## Relatórios

Após cada execução, um relatório em Markdown é criado na pasta `reports`.

Os relatórios incluem:

- resumo executivo;
- métricas por variante;
- evidência estatística;
- qualidade dos dados;
- limitações;
- recomendação final.

## Acompanhamento dos testes

Cada teste analisado é registrado em:

```text
tracking/acompanhamento.csv
```

O arquivo possui uma linha por teste, contendo nome, descrição, resultado, decisão e outras informações da análise.

A solução também possui integração opcional com Google Sheets por meio de uma conta de serviço.
