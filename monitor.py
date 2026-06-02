import os
import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

PROTOCOLO = "202604152154520921"
DATA_NASC = "02/04/1996"
URL = "https://servicos.pf.gov.br/agenda-web/acessar?reagendamento=true"

TOKEN = "8970536260:AAFIsovKbPTgHPm_kRHeLbPfyX0DR4-LyCo"
CHAT_ID = "7692839343"

print(f"Iniciando - {datetime.now()}")

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()
    
    print("Acessando...")
    page.goto(URL, timeout=60000)
    time.sleep(3)
    
    print("Selecionando Migração...")
    page.click("text=Migração")
    time.sleep(1)
    
    print("Preenchendo...")
    page.fill("input[type='text']", PROTOCOLO)
    page.fill("input[type='date']", DATA_NASC)
    
    print("Prosseguindo...")
    page.click("button:has-text('Prosseguir')")
    time.sleep(5)
    
    if "nenhuma vaga" in page.content().lower():
        print("Sem vagas")
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            requests.post(url, json={"chat_id": CHAT_ID, "text": f"🔍 {datetime.now().strftime('%H:%M')} - Sem vagas"})
        except:
            pass
    else:
        print("VAGAS ENCONTRADAS!")
        try:
            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": "🚨 VAGAS! Agendando..."})
        except:
            pass
        
        for data in page.query_selector_all("td:has-text('/')"):
            texto = data.text_content()
            if '/' in texto:
                data.click()
                time.sleep(2)
                
                for horario in page.query_selector_all("button:has-text(':')"):
                    texto_horario = horario.text_content()
                    if ':' in texto_horario:
                        horario.click()
                        time.sleep(2)
                        
                        btn = page.query_selector("button:has-text('Confirmar')")
                        if btn:
                            btn.click()
                            time.sleep(3)
                            
                            nome = f"comprovante_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                            page.pdf(path=nome, format='A4')
                            
                            with open(nome, 'rb') as f:
                                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendDocument", files={'document': f}, data={'chat_id': CHAT_ID})
                            
                            requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", json={"chat_id": CHAT_ID, "text": f"✅ AGENDADO! {texto} {texto_horario}"})
                            browser.close()
                            exit()
                break
    
    browser.close()
