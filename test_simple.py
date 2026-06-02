import os
import requests
from datetime import datetime

print(f"Teste executando em {datetime.now()}")
print(f"Python version: {os.sys.version}")

# Testar Telegram
TOKEN = os.environ.get("TELEGRAM_TOKEN", "8970536260:AAFIsovKbPTgHPm_kRHeLbPfyX0DR4-LyCo")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "7692839343")

try:
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    r = requests.post(url, json={"chat_id": CHAT_ID, "text": "✅ Teste do GitHub Actions funcionando!"}, timeout=10)
    print(f"Telegram status: {r.status_code}")
    print(f"Resposta: {r.text}")
except Exception as e:
    print(f"Erro: {e}")

print("Teste concluido!")
