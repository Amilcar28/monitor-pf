import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

PROTOCOLO = "202604152154520921"
DATA_NASC = "02/04/1996"
TELEGRAM_TOKEN = "8970536260:AAFIsovKbPTgHPm_kRHeLbPfyX0DR4-LyCo"
TELEGRAM_CHAT_ID = "7692839343"

def enviar(msg):
    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})

def main():
    print("INICIANDO COM PLAYWRIGHT!")
    enviar("🤖 Monitor PF com agendamento automático iniciado!")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        page.goto("https://servicos.pf.gov.br/agenda-web/acessar?reagendamento=true")
        time.sleep(3)
        
        page.click("text=Migração")
        time.sleep(1)
        
        page.fill("input[type='text']", PROTOCOLO)
        page.fill("input[type='date']", DATA_NASC)
        time.sleep(1)
        
        page.click("button:has-text('Prosseguir')")
        time.sleep(5)
        
        conteudo = page.content()
        if "nenhuma vaga" in conteudo.lower():
            print("Sem vagas")
            enviar(f"🔍 {datetime.now().strftime('%H:%M')} - Sem vagas")
        else:
            print("VAGAS ENCONTRADAS!")
            enviar("🚨 VAGAS ENCONTRADAS! Agendando...")
            
            for data in page.query_selector_all("td:has-text('/')"):
                if '/' in data.text_content():
                    data.click()
                    time.sleep(2)
                    for horario in page.query_selector_all("button:has-text(':')"):
                        if ':' in horario.text_content():
                            horario.click()
                            time.sleep(2)
                            confirmar = page.query_selector("button:has-text('Confirmar')")
                            if confirmar:
                                confirmar.click()
                                time.sleep(3)
                                nome = f"comprovante_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                page.pdf(path=nome, format='A4')
                                with open(nome, 'rb') as f:
                                    requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", files={'document': f}, data={'chat_id': TELEGRAM_CHAT_ID})
                                enviar(f"✅ AGENDADO! {data.text_content()} {horario.text_content()}")
                                browser.close()
                                return
                    break
        
        browser.close()

if __name__ == "__main__":
    main()
