import pandas as pd
import requests
import json
from datetime import datetime

def enviar():
    df = pd.read_excel("Bloomberg_Remates_Organizado.xlsx")
    
    # Limpiar datos
    df['Precio_Num'] = df['Precio Base'].astype(str).str.extract(r'(\d+[\d,]*)')[0].str.replace(',', '').astype(float)
    
    # Top 1 para WhatsApp
    top1 = df.nsmallest(1, 'Precio_Num').iloc[0]
    
    # Top 10 para Email
    top10 = df.nsmallest(10, 'Precio_Num').to_dict('records')
    
    # WhatsApp message
    whatsapp_msg = f"""🔥 REMATE DEL DÍA - {datetime.now().strftime('%d/%m')}

🏷️ {top1['Código de Remate']}
📍 {top1['Distrito Judicial']}
💰 {top1['Precio Base']}
📢 {top1['Convocatoria']}

👉 Ver todos: https://remaju-automation.netlify.app/mapa_remates.html"""
    
    # Enviar a Make.com (lo configuraremos después)
    webhook_whatsapp = "https://hook.make.com/TU_WEBHOOK_AQUI"  # Temporal
    
    try:
        requests.post(webhook_whatsapp, json={"message": whatsapp_msg}, timeout=5)
        print("✅ Notificación WhatsApp enviada")
    except:
        print("⚠️ Webhook no configurado aún")
    
    # Guardar top10 para respaldo
    with open(f"top10_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
        json.dump(top10, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {len(top10)} remates guardados para newsletter")

if __name__ == "__main__":
    enviar()