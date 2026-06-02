import requests
import os
import time
from datetime import datetime

URL_BASE = "https://servicos.pf.gov.br/agenda-web/acessar"
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "8970536260:AAFIsovKbPTgHPm_kRHeLbPfyX0DR4-LyCo")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7692839343")

def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}, timeout=10)
        print("✅ Telegram enviado")
    except Exception as e:
        print(f"Erro: {e}")

def verificar_site():
    print(f"🔍 Verificando - {datetime.now().strftime('%H:%M:%S')}")
    
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        response = requests.get(URL_BASE, headers=headers, timeout=15)
        
        if response.status_code == 200:
            print(f"✅ Site online (status: {response.status_code})")
            
            # Verifica palavras de "sem vaga"
            conteudo = response.text.lower()
            
            if "nenhuma vaga" in conteudo:
                print("❌ Sem vagas disponíveis")
                return False
            elif "esgotado" in conteudo:
                print("❌ Vagas esgotadas")
                return False
            else:
                print("⚠️ Página carregou - pode ter vagas!")
                return True
        else:
            print(f"❌ Site offline: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Erro: {e}")
        return False

def main():
    print("="*50)
    print("MONITOR PF - GITHUB ACTIONS")
    print("="*50)
    
    if verificar_site():
        mensagem = f"""🚨 *ALERTA!*
        
Site da Polícia Federal indica disponibilidade!

🔗 Acesse AGORA: {URL_BASE}

⚠️ Você precisa resolver o CAPTCHA manualmente.
📝 Protocolo: 202604152154520921

⏰ {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"""
        
        enviar_telegram(mensagem)
        print("✅ Alerta enviado! Verifique seu Telegram.")
    else:
        enviar_telegram(f"🔍 Monitor ativo - {datetime.now().strftime('%H:%M')} - Sem vagas")
        print("❌ Nenhuma vaga detectada")

if __name__ == "__main__":
    main()
