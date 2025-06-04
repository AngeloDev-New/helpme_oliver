# Projeto de Recuperação de Dados do DATASUS

Este projeto tem como objetivo coletar, processar e organizar dados públicos disponíveis no portal do DATASUS e outras fontes oficiais relacionadas à saúde pública brasileira. Os dados coletados são preparados para análise posterior, incluindo visualizações em ferramentas como o Power BI.

## Funcionalidades

- Coleta de dados de:
  - Estabelecimentos de saúde (CNES)
  - Saúde da mulher
  - Nascimentos
  - Procedimentos realizados
  - Repasses financeiros federais
- Armazenamento em CSV
- Estruturação dos dados para uso em Business Intelligence

## Pré-requisitos

- Python 3.7+
- Google Chrome instalado
- ChromeDriver compatível com sua versão do Chrome

## Instalação

Clone o repositório e instale as dependências.

### Windows

```bash
python -m venv venv
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
venv\Scripts\activate
pip install -r requirements.txt
```

### Linux

```bash
python -m venv venv
chmod +x venv/
. venv/bin/activate
pip install -r requirements.txt
```

## Execução

Após ativar o ambiente virtual, execute:

```bash
python main.py
```

## Estrutura

- `main.py`: script principal para coleta e integração dos dados.
- `dados_saude/`: pasta onde os arquivos CSV serão armazenados.
- `power_bi/`: subpasta com dados prontos para análise no Power BI.

## Observações

- O script utiliza Selenium para acessar páginas dinâmicas e BeautifulSoup para extrair informações das páginas HTML.
- A coleta é feita em modo interativo por padrão (não headless) para facilitar o diagnóstico de falhas. Você pode ativar o modo headless comentando a linha correspondente no código (`chrome_options.add_argument("--headless")`).
- Alguns filtros estão fixos no script para demonstrar a coleta de dados da Região Oeste. Você pode alterar os parâmetros conforme necessário.

## Licença

Este projeto está licenciado sob a licença MIT.
