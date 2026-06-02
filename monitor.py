#!/usr/bin/env python3
# monitor.py - Versão para GitHub Actions (sem navegador)
import requests
import json
import os
import time
from datetime import datetime

# ============================================
# CONFIGURAÇÕES (pegando dos secrets do GitHub)
# ============================================
PROTOCOLO = "202604152154520921"
DATA_NASCIMENTO = "02/04/1996"

# URL do site
URL_BASE = "https://servicos.pf.gov.br/agenda-web/acessar"

# Telegram - PEGO DOS SECRETS DO GITHUB
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Arquivo de controle (persiste entre execuções)
ARQUIVO_ESTADO = "estado.json"

def enviar_telegram(mensagem):
    """Envia mensagem para o Telegram"""
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        print("⚠️ Telegram não configurado")
        return False
    
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        dados = {"chat_id": TELEGRAM_CHAT_ID, "text": mensagem}
        r = requests.post(url, json=dados, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"Erro Telegram: {e}")
        return False

def verificar_site():
    """Verifica se o site está acessível e se há indicativo de vagas"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        print(f"🔍 Verificando {URL_BASE}...")
        resp = requests.get(URL_BASE, headers=headers, timeout=15)
        
        if resp.status_code == 200:
            print(f"✅ Site acessível (status {resp.status_code})")
            
            # Analisa o conteúdo da página
            conteudo = resp.text.lower()
            
            # Palavras-chave que indicam vagas indisponíveis
            palavras_sem_vaga = [
                "nenhuma vaga",
                "sem vagas",
                "indisponível",
                "esgotado"
            ]
            
            for palavra in palavras_sem_vaga:
                if palavra in conteudo:
                    print(f"⚠️ Detectado: '{palavra}' - sem vagas")
                    return {"tem_vaga": False}
            
            # Se não encontrou palavras de "sem vaga", pode ter vaga
            print("✅ Possível vaga detectada!")
            return {"tem_vaga": True, "detalhe": "Site indica disponibilidade"}
        else:
            print(f"❌ Site offline: {resp.status_code}")
            return {"tem_vaga": False, "erro": f"Status {resp.status_code}"}
            
    except Exception as e:
        print(f"❌ Erro ao acessar: {e}")
        return {"tem_vaga": False, "erro": str(e)}

def carregar_estado():
    """Carrega o estado anterior"""
    if os.path.exists(ARQUIVO_ESTADO):
        try:
            with open(ARQUIVO_ESTADO, 'r') as f:
                return json.load(f)
        except:
            pass
    return {"ja_avisou": False, "ultima_vaga": None}

def salvar_estado(estado):
    """Salva o estado atual"""
    with open(ARQUIVO_ESTADO, 'w') as f:
        json.dump(estado, f)

def monitorar():
    """Função principal de monitoramento"""
    agora = datetime.now()
    print(f"\n{'='*50}")
    print(f"🕐 {agora.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📝 Protocolo: {PROTOCOLO}")
    print(f"{'='*50}")
    
    # Carrega estado anterior
    estado = carregar_estado()
    
    # Verifica site
    resultado = verificar_site()
    
    if resultado.get("tem_vaga"):
        # Só avisa se não tiver avisado antes ou se for uma nova detecção
        if not estado.get("ja_avisou"):
            print("🚨 VAGA DETECTADA! Enviando alerta...")
            
            mensagem = f"""🚨 *VAGA NA POLÍCIA FEDERAL!* 🚨

✅ Site indica disponibilidade de agendamento!

📝 Protocolo: {PROTOCOLO}
🔗 Acesse AGORA: {URL_BASE}

⚠️ Corra antes que acabe!
📅 Data: {agora.strftime('%d/%m/%Y %H:%M:%S')}"""
            
            if enviar_telegram(mensagem):
                print("✅ Alerta enviado para o Telegram!")
                salvar_estado({"ja_avisou": True, "ultima_vaga": agora.isoformat()})
            else:
                print("❌ Falha ao enviar alerta")
        else:
            print("ℹ️ Já avisou anteriormente. Ignorando duplicado.")
    else:
        print("❌ Nenhuma vaga detectada")
        
        # Reseta o estado se já não há mais vaga
        if estado.get("ja_avisou"):
            print("🔄 Resetando estado (vaga expirou?)")
            salvar_estado({"ja_avisou": False, "ultima_vaga": None})
        
        # Envia heartbeat a cada 24h (opcional)
        ultimo_heartbeat = estado.get("ultimo_heartbeat")
        if not ultimo_heartbeat or (agora - datetime.fromisoformat(ultimo_heartbeat)).seconds > 86400:
            enviar_telegram(f"🔍 Monitor PF ativo - {agora.strftime('%d/%m/%Y %H:%M')}")
            salvar_estado({**estado, "ultimo_heartbeat": agora.isoformat()})

# ============================================
# EXECUÇÃO
# ============================================
if __name__ == "__main__":
    print("""
    ╔════════════════════════════════════════════╗
    ║     MONITOR PF - GITHUB ACTIONS            ║
    ║     Rodando 24/7 na nuvem sem seu PC       ║
    ╚════════════════════════════════════════════╝
    """)
    
    monitorar()
