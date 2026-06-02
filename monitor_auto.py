#!/usr/bin/env python3
import os
import time
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

PROTOCOLO = "202604152154520921"
DATA_NASCIMENTO = "02/04/1996"
URL_BASE = "https://servicos.pf.gov.br/agenda-web/acessar"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8970536260:AAFIsovKbPTgHPm_kRHeLbPfyX0DR4-LyCo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7692839343")

ARQUIVO_ESTADO = "estado.json"

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}, timeout=10)
        print("✅ Telegram enviado")
    except Exception as e:
        print(f"Erro: {e}")

def enviar_pdf_telegram(caminho):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        with open(caminho, 'rb') as f:
            requests.post(url, files={'document': f}, data={'chat_id': TELEGRAM_CHAT_ID, 'caption': '📄 Comprovante PF'}, timeout=30)
        print("✅ PDF enviado")
    except Exception as e:
        print(f"Erro: {e}")

def carregar_estado():
    if os.path.exists(ARQUIVO_ESTADO):
        with open(ARQUIVO_ESTADO, 'r') as f:
            return json.load(f)
    return {"ja_agendou": False}

def salvar_estado(estado):
    with open(ARQUIVO_ESTADO, 'w') as f:
        json.dump(estado, f)

def monitorar():
    estado = carregar_estado()
    if estado.get("ja_agendou"):
        print("✅ Já agendou")
        return
    
    print(f"🚀 Iniciando - {datetime.now()}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            page.goto(URL_BASE, timeout=60000)
            time.sleep(3)
            
            page.click("text=Migração")
            time.sleep(1)
            
            page.fill("input[type='text']", PROTOCOLO)
            page.fill("input[type='date']", DATA_NASCIMENTO)
            time.sleep(1)
            
            page.click("button:has-text('Prosseguir')")
            time.sleep(5)
            
            conteudo = page.content()
            
            if "nenhuma vaga" in conteudo.lower():
                print("❌ Sem vagas")
                return
            
            print("✅ VAGAS ENCONTRADAS!")
            enviar_telegram("🚨 VAGAS ENCONTRADAS! Iniciando agendamento...")
            
            # Clica na primeira data disponível
            dias = page.query_selector_all("td:has-text('/'), button:has-text('/')")
            for dia in dias:
                texto_dia = dia.text_content()
                if '/' in texto_dia:
                    print(f"📅 Data: {texto_dia}")
                    dia.click()
                    time.sleep(2)
                    
                    # Clica no primeiro horário
                    horarios = page.query_selector_all("button:has-text(':')")
                    for horario in horarios:
                        texto_horario = horario.text_content()
                        if ':' in texto_horario:
                            print(f"⏰ Horário: {texto_horario}")
                            horario.click()
                            time.sleep(2)
                            
                            # Confirma
                            confirmar = page.query_selector("button:has-text('Confirmar')")
                            if confirmar:
                                confirmar.click()
                                time.sleep(3)
                                
                                # Salva PDF
                                nome_pdf = f"comprovante_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
                                page.pdf(path=nome_pdf, format='A4')
                                enviar_pdf_telegram(nome_pdf)
                                
                                msg = f"🎉 AGENDADO! {texto_dia} às {texto_horario}"
                                enviar_telegram(msg)
                                
                                salvar_estado({"ja_agendou": True, "data": texto_dia, "horario": texto_horario})
                                browser.close()
                                return
                            
        except Exception as e:
            print(f"Erro: {e}")
        finally:
            browser.close()

if __name__ == "__main__":
    print("="*50)
    monitorar()
