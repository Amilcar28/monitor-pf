import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# CONFIGURAÇÕES
PROTOCOLO = "202604152154520921"
DATA_NASCIMENTO = "02/04/1996"
UF = "São Paulo"
CIDADE = "São Paulo"

TELEGRAM_TOKEN = "8970536260:AAFIsovKbPTgHPm_kRHeLbPfyX0DR4-LyCo"
TELEGRAM_CHAT_ID = "7692839343"

URL_BASE = "https://servicos.pf.gov.br/agenda-web/acessar"

def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": msg})
        print("✅ Msg enviada")
    except Exception as e:
        print(f"Erro: {e}")

def enviar_pdf(caminho):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        with open(caminho, 'rb') as f:
            requests.post(url, files={'document': f}, data={'chat_id': TELEGRAM_CHAT_ID})
        print("✅ PDF enviado")
    except Exception as e:
        print(f"Erro PDF: {e}")

def main():
    print(f"Iniciando - {datetime.now()}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # PASSO 1: ACESSAR
            page.goto(URL_BASE, timeout=60000)
            time.sleep(3)
            
            # PASSO 2: MIGRAÇÃO
            page.click("text=Migração")
            time.sleep(1)
            
            page.click("button:has-text('Prosseguir')")
            time.sleep(3)
            
            # PASSO 3: DADOS
            page.fill("input[type='text']", PROTOCOLO)
            page.fill("input[type='date']", DATA_NASCIMENTO)
            time.sleep(1)
            
            page.click("button:has-text('Prosseguir')")
            time.sleep(5)
            
            # PASSO 4: LOCALIDADE
            page.click("text=São Paulo")
            time.sleep(1)
            page.click("text=São Paulo")
            time.sleep(1)
            
            unidades = page.query_selector_all("button, a, div[role='button']")
            for unidade in unidades:
                texto = unidade.text_content()
                if texto and ("Unidade" in texto or "Policia" in texto):
                    unidade.click()
                    break
            time.sleep(2)
            
            page.click("button:has-text('Próximo'), button:has-text('Prosseguir')")
            time.sleep(5)
            
            # PASSO 5: VERIFICAR VAGAS
            if "nenhuma vaga" in page.content().lower():
                print("Sem vagas")
                browser.close()
                return
            
            print("VAGAS ENCONTRADAS! AGENDANDO...")
            enviar_telegram("🚨 VAGAS ENCONTRADAS! Iniciando agendamento...")
            
            # PASSO 6: ESCOLHER DATA
            datas = page.query_selector_all("td:has-text('/'), button:has-text('/')")
            for data in datas:
                texto_data = data.text_content()
                if '/' in texto_data:
                    data.click()
                    time.sleep(2)
                    
                    # PASSO 7: ESCOLHER HORÁRIO
                    horarios = page.query_selector_all("button:has-text(':')")
                    for horario in horarios:
                        texto_horario = horario.text_content()
                        if ':' in texto_horario:
                            horario.click()
                            time.sleep(2)
                            
                            # PASSO 8: CONFIRMAR
                            confirmar = page.query_selector("button:has-text('Confirmar')")
                            if confirmar:
                                confirmar.click()
                                time.sleep(3)
                                
                                # PASSO 9: PDF
                                nome = f"comprovante_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                page.pdf(path=nome, format='A4')
                                enviar_pdf(nome)
                                enviar_telegram(f"🎉 AGENDADO! {texto_data} {texto_horario}")
                                browser.close()
                                return
                    break
            
        except Exception as e:
            print(f"Erro: {e}")
            enviar_telegram(f"❌ Erro: {str(e)[:200]}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
