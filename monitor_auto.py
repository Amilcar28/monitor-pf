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

TELEGRAM_TOKEN = "8970536260:AAFIsovKbPTgHPm_kRHeLbPfyX0DR4-LyCo"
TELEGRAM_CHAT_ID = "7692839343"

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}, timeout=10)
        print("✅ Telegram enviado")
    except Exception as e:
        print(f"Erro Telegram: {e}")

def monitorar():
    print(f"🚀 Iniciando - {datetime.now()}")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()
        
        try:
            print("🌐 Acessando site...")
            page.goto(URL_BASE, timeout=60000)
            time.sleep(5)
            
            # Esperar a página carregar completamente
            page.wait_for_load_state("networkidle")
            
            # Tirar screenshot para debug
            page.screenshot(path="site_carregado.png")
            
            # Tentar diferentes formas de selecionar o serviço
            print("📌 Procurando opções de serviço...")
            
            # Lista de seletores possíveis
            seletores = [
                "text=Migração",
                "text=Migracao",
                "text=migração",
                "input[value='Migração']",
                "label:has-text('Migração')",
                "button:has-text('Migração')",
                "span:has-text('Migração')"
            ]
            
            encontrou = False
            for seletor in seletores:
                try:
                    if page.query_selector(seletor):
                        page.click(seletor)
                        print(f"✅ Clicou em: {seletor}")
                        encontrou = True
                        break
                except:
                    pass
            
            if not encontrou:
                print("❌ Não encontrou a opção Migração")
                # Mostra todos os textos clicáveis
                todos_botoes = page.query_selector_all("button, a, input[type='button']")
                print("Botões encontrados:")
                for botao in todos_botoes[:10]:
                    texto = botao.text_content()
                    if texto:
                        print(f"  - {texto.strip()}")
                browser.close()
                return
            
            time.sleep(2)
            
            # Preencher campos
            print("📝 Preenchendo dados...")
            page.fill("input[type='text']", PROTOCOLO)
            page.fill("input[type='date']", SUA_DATA_NASCIMENTO)
            time.sleep(1)
            
            # Clicar em prosseguir
            print("▶️ Prosseguindo...")
            botoes_prosseguir = ["button:has-text('Prosseguir')", "button:has-text('Avançar')", "input[value='Prosseguir']"]
            for seletor in botoes_prosseguir:
                if page.query_selector(seletor):
                    page.click(seletor)
                    break
            
            time.sleep(5)
            
            conteudo = page.content()
            if "nenhuma vaga" in conteudo.lower():
                print("❌ Nenhuma vaga disponível")
                return
            
            print("✅ VAGAS ENCONTRADAS!")
            enviar_telegram("🚨 VAGAS ENCONTRADAS! Site da PF com disponibilidade!")
            
        except Exception as e:
            print(f"❌ Erro: {e}")
            page.screenshot(path="erro.png")
        finally:
            browser.close()

if __name__ == "__main__":
    print("="*50)
    monitorar()
