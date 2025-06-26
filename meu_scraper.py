import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

# --- Configurações ---
BOTOES_DIR = "botoes"

def setup_driver():
    """Configura e retorna uma instância do WebDriver do Selenium."""
    print("Configurando o WebDriver...")
    try:
        service = ChromeService(ChromeDriverManager().install())
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920x1080")
        options.add_argument("--log-level=3") # Suprime logs excessivos
        driver = webdriver.Chrome(service=service, options=options)
        print("WebDriver configurado com sucesso.")
        return driver
    except Exception as e:
        print(f"Ocorreu um erro ao configurar o WebDriver: {e}")
        print("Verifique sua conexão com a internet ou a configuração do Chrome/ChromeDriver.")
        return None

def get_button_urls_from_html_file(file_path):
    """
    Lê um arquivo HTML local, extrai os links dos botões e os retorna.
    """
    print(f"Lendo o arquivo HTML local: {file_path}")
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"Erro: O arquivo '{file_path}' não foi encontrado.")
        return []

    soup = BeautifulSoup(content, 'html.parser')
    
    # Este seletor é mais robusto, pois pega o link "fake" que existe em cada card.
    # Ele tem o href correto para a página do botão.
    link_elements = soup.select("article a.fake-link")
    
    base_url = "https://uiverse.io"
    button_urls = []
    
    # Usamos um set para garantir que as URLs sejam únicas
    unique_hrefs = set()

    for elem in link_elements:
        href = elem.get('href')
        if href:
            unique_hrefs.add(href)

    for href in sorted(list(unique_hrefs)): # Ordena para um processamento consistente
        full_url = base_url + href
        button_urls.append(full_url)
            
    total_buttons = len(button_urls)
    if total_buttons == 0:
        print("Nenhum link de botão foi encontrado no arquivo HTML. Verifique o seletor 'article a.fake-link'.")
    else:
        print(f"Encontrados {total_buttons} links de botões únicos no arquivo HTML.")
        
    return button_urls

def extract_button_data(driver, url, index, total):
    """
    Navega até a URL de um botão, extrai o código HTML e CSS e salva em arquivos.
    """
    print(f"Processando botão {index}/{total}: {url}")
    try:
        driver.get(url)
        wait = WebDriverWait(driver, 20)

        # O código está na página principal, não precisamos entrar no iframe.
        # Esperamos os blocos de código ficarem visíveis e extraímos o texto.
        html_code_element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-name='html'] code"))
        )
        css_code_element = wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "div[data-name='css'] code"))
        )

        button_html = html_code_element.text
        button_css = css_code_element.text

        if not button_html:
            print(f"  -> Código HTML não encontrado para a URL: {url}. Pulando.")
            return

        # Gera um nome de arquivo a partir da URL
        file_name = url.split('/')[-1]
        
        # Salva os arquivos
        with open(os.path.join(BOTOES_DIR, f"{file_name}.html"), "w", encoding="utf-8") as f:
            f.write(button_html)
        with open(os.path.join(BOTOES_DIR, f"{file_name}.css"), "w", encoding="utf-8") as f:
            f.write(button_css)

    except TimeoutException:
        print(f"  -> Erro de Timeout ao processar a URL: {url}. A página pode ter mudado ou demorou para carregar. Pulando.")
    except Exception as e:
        print(f"  -> Ocorreu um erro inesperado em '{url}': {e}")

def main():
    """Função principal do scraper."""
    if not os.path.exists(BOTOES_DIR):
        os.makedirs(BOTOES_DIR)

    # Etapa 1: Extrair URLs do arquivo HTML local
    button_urls = get_button_urls_from_html_file('botoes.html')

    if not button_urls:
        print("Nenhuma URL foi extraída. Encerrando o script.")
        return

    # Etapa 2: Configurar o driver do Selenium (só é necessário agora)
    driver = setup_driver()
    if not driver:
        return

    try:
        # Etapa 3: Iterar sobre as URLs e extrair os dados de cada botão
        total_buttons = len(button_urls)
        for i, url in enumerate(button_urls, 1):
            extract_button_data(driver, url, i, total_buttons)
            
        print("\nPronto! A extração foi concluída. Verifique a pasta 'botoes' ")
    
    finally:
        # Fecha o navegador
        print("Fechando o navegador...")
        driver.quit()

if __name__ == "__main__":
    main()
