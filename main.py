import pandas as pd
import requests
from bs4 import BeautifulSoup
import time
import datetime
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configurações
DATA_DIR = "dados_saude"
os.makedirs(DATA_DIR, exist_ok=True)
hoje = datetime.datetime.now().strftime("%Y-%m-%d")

# URLs (fontes de dados)
urls = {
    'datasus': 'http://tabnet.datasus.gov.br/cgi/deftohtm.exe?cnes/cnv/estabbr.def',
    'repasses': 'https://www.gov.br/saude/pt-br/acesso-a-informacao/repasses-financeiros',
    'saude_mulher': 'http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sih/cnv/qiuf.def',
    'nascimentos': 'http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sinasc/cnv/nvuf.def',
    'procedimentos': 'http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sia/cnv/qauf.def'
}


# Configuração do Selenium
def configurar_driver():
    chrome_options = Options()
    # chrome_options.add_argument("--headless")  # Executar em modo headless (sem interface gráfica)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=chrome_options)
    return driver


# Função para extrair dados do DATASUS usando Selenium
def extrair_datasus(driver, url, params, nome_arquivo):
    driver.get(url)

    # Aguardar carregamento da página
    time.sleep(3)

    # Selecionar parâmetros de busca
    for param_id, valor in params.items():
        try:
            elemento = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, param_id))
            )
            elemento.clear()
            elemento.send_keys(valor)
        except Exception as e:
            print(f"Erro ao selecionar parâmetro {param_id}: {e}")

    # Clicar no botão de busca
    try:
        botao_busca = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//input[@type='button' and @value='Mostra']"))
        )
        botao_busca.click()

        # Aguardar resultados
        time.sleep(5)

        # Extrair tabela de resultados
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        tabelas = soup.find_all('table')

        if tabelas:
            # Geralmente a tabela de resultados é a maior
            tabela_resultados = max(tabelas, key=lambda x: len(x.find_all('tr')))

            # Extrair dados da tabela
            linhas = tabela_resultados.find_all('tr')
            cabecalho = [th.text.strip() for th in linhas[0].find_all(['th', 'td'])]

            dados = []
            for linha in linhas[1:]:
                colunas = linha.find_all(['td', 'th'])
                if colunas:
                    linha_dados = [col.text.strip() for col in colunas]
                    dados.append(linha_dados)

            # Criar DataFrame
            df = pd.DataFrame(dados, columns=cabecalho)

            # Salvar em CSV
            caminho_arquivo = os.path.join(DATA_DIR, f"{nome_arquivo}_{hoje}.csv")
            df.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
            print(f"Dados salvos em {caminho_arquivo}")
            return df
        else:
            print("Nenhuma tabela encontrada na página")
            return None

    except Exception as e:
        print(f"Erro ao extrair dados: {e}")
        return None


# Função para extrair dados de repasses usando requests
def extrair_repasses(url, nome_arquivo):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, 'html.parser')

        # Buscar links para planilhas de repasse
        links = soup.find_all('a', href=True)
        links_xlsx = [link['href'] for link in links if link['href'].endswith('.xlsx')]

        dados_combinados = pd.DataFrame()

        for i, link in enumerate(links_xlsx):
            if i >= 3:  # Limitar a 3 arquivos para não sobrecarregar
                break

            try:
                print(f"Baixando {link}")
                if not link.startswith('http'):
                    link = 'https://www.gov.br' + link if not link.startswith('/') else 'https://www.gov.br' + link

                df = pd.read_excel(link)
                # Adicionar origem do arquivo como coluna
                df['fonte_arquivo'] = os.path.basename(link)
                dados_combinados = pd.concat([dados_combinados, df], ignore_index=True)
            except Exception as e:
                print(f"Erro ao processar {link}: {e}")

        if not dados_combinados.empty:
            # Salvar em CSV
            caminho_arquivo = os.path.join(DATA_DIR, f"{nome_arquivo}_{hoje}.csv")
            dados_combinados.to_csv(caminho_arquivo, index=False, encoding='utf-8-sig')
            print(f"Dados salvos em {caminho_arquivo}")
            return dados_combinados
        else:
            print("Nenhum dado encontrado")
            return None

    except Exception as e:
        print(f"Erro ao extrair repasses: {e}")
        return None


# Função para extrair números de clínicas e hospitais do CNES
def extrair_estabelecimentos(driver):
    params = {
        'Linha': 'Região de Saúde (CIR)',
        'Coluna': 'Tipo de Estabelecimento',
        'Incremento': 'Quantidade',
        'Arquivos': 'estabbr.dbf',
        'pesqmes1': 'Digite o texto aqui',
        'SMunic': 'TODAS_AS_CATEGORIAS__',
        'SRegiao': 'OESTE',  # Filtrar para região Oeste
        'SEstado': 'TODAS_AS_CATEGORIAS__'
    }

    return extrair_datasus(driver, urls['datasus'], params, 'estabelecimentos_saude')


# Função para extrair dados de saúde da mulher
def extrair_saude_mulher(driver):
    params = {
        'Linha': 'Município',
        'Coluna': 'Proc realizados',
        'Incremento': 'AIH aprovadas',
        'Arquivos': 'qiuf2207.dbf',
        'pesqmes1': 'Digite o texto aqui',
        'SMunic': 'TODAS_AS_CATEGORIAS__',
        'SRegiao': 'OESTE',  # Filtrar para região Oeste
        'SCapitulo': '15_Gravidez_parto_e_puerperio',  # Capítulo relacionado à saúde da mulher
        'SLista': 'Procedimentos_obstetricos'  # Procedimentos obstétricos
    }

    return extrair_datasus(driver, urls['saude_mulher'], params, 'saude_mulher')


# Função para extrair dados de nascimentos
def extrair_nascimentos(driver):
    params = {
        'Linha': 'Município',
        'Coluna': 'Idade da mãe',
        'Incremento': 'Nascim_p/resid.mãe',
        'Arquivos': 'nvuf2207.dbf',
        'pesqmes1': 'Digite o texto aqui',
        'SMunic': 'TODAS_AS_CATEGORIAS__',
        'SRegiao': 'OESTE'  # Filtrar para região Oeste
    }

    return extrair_datasus(driver, urls['nascimentos'], params, 'nascimentos')


# Função para extrair dados de procedimentos
def extrair_procedimentos(driver):
    params = {
        'Linha': 'Município',
        'Coluna': 'Complexidade',
        'Incremento': 'Qtd.aprovada',
        'Arquivos': 'qauf2207.dbf',
        'pesqmes1': 'Digite o texto aqui',
        'SMunic': 'TODAS_AS_CATEGORIAS__',
        'SRegiao': 'OESTE'  # Filtrar para região Oeste
    }

    return extrair_datasus(driver, urls['procedimentos'], params, 'procedimentos')


# Função para integrar e preparar os dados para o Power BI
def preparar_dados_power_bi():
    # Criar diretório específico para Power BI
    powerbi_dir = os.path.join(DATA_DIR, "power_bi")
    os.makedirs(powerbi_dir, exist_ok=True)

    # Encontrar os arquivos mais recentes
    arquivos = {}
    for nome in ['estabelecimentos_saude', 'saude_mulher', 'nascimentos', 'procedimentos', 'repasses']:
        arquivos_encontrados = [f for f in os.listdir(DATA_DIR) if f.startswith(nome) and f.endswith('.csv')]
        if arquivos_encontrados:
            # Ordenar por data (mais recente primeiro)
            arquivos_encontrados.sort(reverse=True)
            arquivos[nome] = os.path.join(DATA_DIR, arquivos_encontrados[0])

    # Criar tabelas dimensão e fato
    tabelas = {}
    for nome, arquivo in arquivos.items():
        if os.path.exists(arquivo):
            df = pd.read_csv(arquivo, encoding='utf-8-sig')
            tabelas[nome] = df

    # Criar tabela fato (exemplo)
    if 'estabelecimentos_saude' in tabelas and 'procedimentos' in tabelas:
        # Criar tabela fato relacionando estabelecimentos e procedimentos
        # Nota: Esta é uma simplificação, o relacionamento real dependeria da estrutura dos dados
        df_estabelecimentos = tabelas['estabelecimentos_saude']
        df_procedimentos = tabelas['procedimentos']

        # Salvar tabelas individuais para Power BI
        for nome, df in tabelas.items():
            caminho = os.path.join(powerbi_dir, f"{nome}_processado.csv")
            df.to_csv(caminho, index=False, encoding='utf-8-sig')
            print(f"Tabela dimensão {nome} salva em {caminho}")

    # Criar arquivo de metadados para Power BI
    metadados = {
        'ultima_atualizacao': hoje,
        'tabelas_disponiveis': list(tabelas.keys()),
        'contagem_registros': {nome: len(df) for nome, df in tabelas.items()}
    }

    with open(os.path.join(powerbi_dir, 'metadados.json'), 'w') as f:
        import json
        json.dump(metadados, f, indent=4)

    print(f"Dados preparados para Power BI em {powerbi_dir}")


# Função principal que coordena todo o processo
def main():
    print("Iniciando extração de dados de saúde...")

    # Configurar driver
    driver = configurar_driver()

    try:
        # Extrair dados
        print("\n1. Extraindo dados de estabelecimentos de saúde...")
        extrair_estabelecimentos(driver)

        print("\n2. Extraindo dados de saúde da mulher...")
        extrair_saude_mulher(driver)

        print("\n3. Extraindo dados de nascimentos...")
        extrair_nascimentos(driver)

        print("\n4. Extraindo dados de procedimentos...")
        extrair_procedimentos(driver)

        print("\n5. Extraindo dados de repasses...")
        extrair_repasses(urls['repasses'], 'repasses')

        print("\n6. Preparando dados para Power BI...")
        preparar_dados_power_bi()

        print("\nProcesso de extração concluído com sucesso!")

    except Exception as e:
        print(f"Erro durante a extração: {e}")

    finally:
        # Fechar o driver
        driver.quit()
if __name__=='__main__':
    main()