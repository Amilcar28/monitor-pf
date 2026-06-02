import time
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# ==================================================
# CONFIGURAÇÕES
# ==================================================
PROTOCOLO = "202604152154520921"
DATA_NASCIMENTO = "02/04/1996"
UF = "São Paulo"
CIDADE = "São Paulo"

# Telegram
TELEGRAM_TOKEN = "8970536260:AAFIsovKbPTgHPm_kRHeLbPfyX0DR4-LyCo"
TELEGRAM_CHAT_ID = "7692839343"

URL_BASE = "https://servicos.pf.gov.br/agenda-web/acessar"
# ==================================================

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}, timeout=10)
        print("✅ Msg enviada")
    except Exception as e:
        print(f"Erro: {e}")

def enviar_pdf(caminho):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        with open(caminho, 'rb') as f:
            requests.post(url, files={'document': f}, data={'chat_id': TELEGRAM_CHAT_ID}, timeout=30)
        print("✅ PDF enviado")
    except Exception as e:
        print(f"Erro PDF: {e}")

def main():
    print(f"\nIniciando - {datetime.now()}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # PASSO 1: ACESSAR E ESCOLHER SERVIÇO
            print("1. Acessando site...")
            page.goto(URL_BASE, timeout=60000)
            time.sleep(3)
            
            print("2. Selecionando Migração...")
            page.click("text=Migração")
            time.sleep(1)
            
            print("3. Prosseguir...")
            page.click("button:has-text('Prosseguir')")
            time.sleep(3)
            
            # PASSO 2: PREENCHER DADOS
            print("4. Preenchendo protocolo...")
            page.fill("input[type='text']", PROTOCOLO)
            time.sleep(1)
            
            print("5. Preenchendo data...")
            page.fill("input[type='date']", DATA_NASCIMENTO)
            time.sleep(1)
            
            print("6. Prosseguir...")
            page.click("button:has-text('Prosseguir')")
            time.sleep(5)
            
            # PASSO 3: LOCALIDADE
            print("7. Selecionando UF São Paulo...")
            page.click(f"text={UF}")
            time.sleep(1)
            
            print("8. Selecionando Cidade São Paulo...")
            page.click(f"text={CIDADE}")
            time.sleep(1)
            
            print("9. Escolhendo primeira unidade...")
            unidades = page.query_selector_all("button, a, div[role='button']")
            for unidade in unidades:
                texto = unidade.text_content()
                if texto and ("Unidade" in texto or "Policia" in texto):
                    unidade.click()
                    break
            time.sleep(2)
            
            print("10. Próximo...")
            page.click("button:has-text('Próximo'), button:has-text('Prosseguir')")
            time.sleep(5)
            
            # PASSO 4: AGENDAMENTO
            if "nenhuma vaga" in page.content().lower():
                print("❌ Sem vagas")
                enviar_telegram(f"🔍 {datetime.now().strftime('%H:%M')} - Sem vagas")
                browser.close()
                return
            
            print("✅ VAGAS ENCONTRADAS!")
            enviar_telegram("🚨 VAGAS! Agendando...")
            
            datas = page.query_selector_all("td:has-text('/'), button:has-text('/')")
            for data in datas:
                texto_data = data.text_content()
                if '/' in texto_data:
                    print(f"📅 Data: {texto_data}")
                    data.click()
                    time.sleep(2)
                    
                    horarios = page.query_selector_all("button:has-text(':')")
                    for horario in horarios:
                        texto_horario = horario.text_content()
                        if ':' in texto_horario:
                            print(f"⏰ Horário: {texto_horario}")
                            horario.click()
                            time.sleep(2)
                            
                            confirmar = page.query_selector("button:has-text('Confirmar')")
                            if confirmar:
                                confirmar.click()
                                time.sleep(3)
                                
                                nome = f"comprovante_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                page.pdf(path=nome, format='A4')
                                enviar_pdf(nome)
                                enviar_telegram(f"🎉 AGENDADO! {texto_data} {texto_horario}")
                                browser.close()
                                return
                    break
            
            print("⚠️ Nenhum horário disponível")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            enviar_telegram(f"❌ Erro: {str(e)[:200]}")
        finally:
            browser.close()

if __name__ == "__main__":
    main()
