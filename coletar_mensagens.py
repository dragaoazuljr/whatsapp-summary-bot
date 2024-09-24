import os

from time import sleep

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait

from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from dotenv import load_dotenv

def coletar_mensagens():
    load_dotenv()
    options = Options()

    #options.add_argument("--headless=new")
    options.add_argument("user-data-dir=whatsapp")

    navegador = webdriver.Chrome(options=options)
    navegador.get('https://web.whatsapp.com/')

    sleep(5)

    # precisa logar ?
    delay = 60
    wait = WebDriverWait(navegador, delay)

    try:
        navegador.find_element(by="css selector", value="div.landing-wrapper")
        print("Logue com seu whatsapp...")
    except:
        pass
    
    # Esperar carregamento de mensagens
    try: 
        wait.until(lambda driver: driver.find_element(by="css selector", value="div[aria-label='Lista de conversas']"))
    except:
        pass

    # Listar todas as conversas
    divLista = navegador.find_element("css selector", "div[aria-label='Lista de conversas']")
    lista = divLista.find_elements("css selector", "span[title]:not([title=''])[aria-label]")

    conversas = [conversa.text for conversa in lista]

    print("Selecione a conversa para resumir: ")

    index = 1;

    for conversa in conversas:
        
        print(f"{index} - {conversa}")
        index += 1

    conversaSelecionada = input()

    conversa = conversas[int(conversaSelecionada)-1]

    try: 
        grupo = wait.until(lambda driver: driver.find_element("xpath", f"//span[starts-with(@title,'{conversa}')]"))  # type: ignore
    except:
        pass
    else: 
        grupo.click();

    sleep(5)

    # Coleta de mensagens do dia

    areaDeMensagens = navegador.find_element("css selector", "div[role='application']")

    scroll_recursivo(navegador, areaDeMensagens)

    navegador.quit()

def scroll_recursivo(navegador: WebDriver, areaDeMensagens):
    # Scroll para coletar mais mensagens
        dia = areaDeMensagens.find_element("css selector", "div > div");

        if (dia.text == "HOJE") :
            print("Buscando mais mensagens...")

            # Scroll para coletar mais mensagens
            #webdriver.ActionChains(navegador).scroll_by_amount(-10000, navegador.find_element("css selector", "div#main div.copyable-area > div[tabindex]").rect['y']).perform();
            navegador.execute_script("document.querySelector('div#main div.copyable-area > div[tabindex]').scrollBy(0, -100000);")

            sleep(1)

            scroll_recursivo(navegador, areaDeMensagens);
        else :
            #mensagens = [div.text for div in navegador.find_elements("css selector", "div.message-in")] 
            mensagens = []

            for div in navegador.find_elements("css selector", "div.message-in"):
                header = div.find_elements("css selector", "div[role] > span[dir][aria-label]")

                mensagem = ""

                if (len(header) == 3) :
                    mensagem += "Autor: "+header[0].text.replace("Você", "Danillo Moraes")+"\n"
                    mensagem += "Resposta a Mensagem = Autor: "+ header[1].text.replace("Você", "Danillo Moraes") + " Mensagem: " + header[2].text + "\n"
                    try: 
                        mensagem += "Mensagem: " + div.find_element("css selector", "div.copyable-text span.copyable-text").text + "\n"
                        mensagem += "Hora: "+div.find_element("css selector", "div[data-pre-plain-text]").get_attribute('data-pre-plain-text').split(' +')[0]+"\n"
                    except:
                        print("ERROR: Não foi possivel extrair a mensagem ou a hora: "+div.text)
                        pass

                if (mensagem != ""):
                    mensagens.append(mensagem)

            resumo = resumir_mensagens(mensagens)

            print("Resumo: "+resumo)

def resumir_mensagens(mensagens: list[str]):
    systemMessage = "Você é um assistente especializado em resumir conversas de grupos de mensagens. Seu objetivo é criar uma timeline de eventos relevantes, destacando os momentos de maior tensão e humor, e fornecendo um resumo claro e envolvente da conversa. Sua resposta deve ser organizada de forma cronológica e destacar os pontos principais, facilitando a compreensão da evolução da conversa."
    prompt = 'A seguir estão mensagens de um grupo de WhatsApp. Resuma a conversa destacando os momentos mais importantes, especialmente focando em elementos de tensão e humor. Organize os eventos em uma linha do tempo clara e concisa para facilitar a leitura. O resumo deve capturar a essência das interações e fornecer uma visão geral dos momentos mais relevantes. Aqui estão as mensagens: \n' 

    provider = os.getenv("PROVIDER", "OPENAI")
    model = os.getenv("MODEL", "gpt-4o")


    if (provider == "OLLAMA"):
        llm = ChatOllama(temperature=0, model=model)
    else :
        llm = ChatOpenAI(temperature=0, model=model)
    
    messages = [("system", systemMessage)] + [("human", prompt+"\n".join(mensagens))]

    #descomente caso queria o prompt completo
    #print("\n".join([m[1] for m in messages]))

    res = llm.invoke(messages)

    return res.content

if __name__ == "__main__":
    coletar_mensagens()
