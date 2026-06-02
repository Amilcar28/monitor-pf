#!/usr/bin/env python3
import os
import time
import json
import requests
from datetime import datetime
from playwright.sync_api import sync_playwright

# ============================================
# CONFIGURAÇÕES
# ============================================
PROTOCOLO = "202604152154520921"
DATA_NASCIMENTO = "02/04/1996"

# URL SEM CAPTCHA (importante!)
URL_BASE = "https://servicos.pf.gov.br/agenda-web/acessar?reagendamento=true"

# Telegram
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8970536260:AAFIsovKbPTgHPm_kRHeLbPfyX0DR4-LyCo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7692839343")

# Controle
ARQUIVO_ESTADO = "estado.json"

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}, timeout=10)
        print("✅ Telegram enviado")
    except Exception as e:
        print(f"Erro: {e}")

def enviar_pdf_telegram(caminho_pdf):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        with open(caminho_pdf, 'rb') as f:
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

def monitorar_e_agendar():
    estado = carregar_estado()
    
    if estado.get("ja_agendou"):
        print("✅ Já agendou anteriormente")
        return
    
    print(f"\n{'='*60}")
    print(f"🚀 INICIANDO - {datetime.now()}")
    print(f"{'='*60}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        try:
            # 1. Acessar site (sem CAPTCHA!)
            print("🌐 Acessando site sem CAPTCHA...")
            page.goto(URL_BASE, timeout=60000)
            time.sleep(3)
            
            # 2. Selecionar Migração
            print("📌 Selecionando Migração...")
            page.click("text=Migração")
            time.sleep(1)
            
            # 3. Preencher dados
            print("📝 Preenchendo protocolo...")
            page.fill("input[type='text']", PROTOCOLO)
            print("📝 Preenchendo data de nascimento...")
            page.fill("input[type='date']", DATA_NASCIMENTO)
            time.sleep(1)
            
            # 4. Clicar em Prosseguir
            print("▶️ Clicando em Prosseguir...")
            page.click("button:has-text('Prosseguir')")
            time.sleep(5)
            
            # 5. Verificar se tem vagas
            conteudo = page.content()
            
            if "nenhuma vaga" in conteudo.lower():
                print("❌ NENHUMA VAGA DISPONÍVEL")
                enviar_telegram(f"🔍 {datetime.now().strftime('%d/%m %H:%M')} - Sem vagas")
                browser.close()
                return
            
            # 6. TEM VAGA! Iniciar agendamento
            print("="*50)
            print("✅ VAGAS ENCONTRADAS!")
            print("="*50)
            enviar_telegram("🚨 *VAGAS ENCONTRADAS!* Iniciando agendamento automático...")
            
            # 7. Encontrar data disponível
            datas = page.query_selector_all("td:has-text('/'), button:has-text('/')")
            
            agendou = False
            for data in datas:
                texto_data = data.text_content()
                if '/' in texto_data and len(texto_data) >= 8:
                    print(f"📅 Data encontrada: {texto_data}")
                    data.click()
                    time.sleep(2)
                    
                    # 8. Encontrar horário disponível
                    horarios = page.query_selector_all("button:has-text(':')")
                    
                    for horario in horarios:
                        texto_horario = horario.text_content()
                        if ':' in texto_horario:
                            print(f"⏰ Horário: {texto_horario}")
                            horario.click()
                            time.sleep(2)
                            
                            # 9. Confirmar
                            confirmar = page.query_selector("button:has-text('Confirmar')")
                            if confirmar:
                                confirmar.click()
                                print("✅ Agendamento confirmado!")
                                time.sleep(3)
                                
                                # 10. Salvar PDF
                                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                                nome_pdf = f"comprovante_{PROTOCOLO}_{timestamp}.pdf"
                                page.pdf(path=nome_pdf, format='A4')
                                print(f"📄 PDF salvo: {nome_pdf}")
                                
                                # 11. Enviar PDF pelo Telegram
                                enviar_pdf_telegram(nome_pdf)
                                
                                # 12. Mensagem de sucesso
                                msg = f"""🎉 *AGENDAMENTO REALIZADO!* 🎉

📅 Data: {texto_data}
⏰ Horário: {texto_horario}
📝 Protocolo: {PROTOCOLO}

✅ Agendamento concluído automaticamente!"""
                                
                                enviar_telegram(msg)
                                
                                # 13. Salvar estado
                                salvar_estado({
                                    "ja_agendou": True,
                                    "data": texto_data,
                                    "horario": texto_horario,
                                    "pdf": nome_pdf,
                                    "timestamp": datetime.now().isoformat()
                                })
                                
                                agendou = True
                                break
                    if agendou:
                        break
            
            if not agendou:
                print("⚠️ Vagas encontradas mas nenhuma data/horário disponível")
                enviar_telegram("⚠️ Vagas detectadas, mas sem data/horário para agendar")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            enviar_telegram(f"❌ Erro: {str(e)[:200]}")
        finally:
            browser.close()

if __name__ == "__main__":
    monitorar_e_agendar()
