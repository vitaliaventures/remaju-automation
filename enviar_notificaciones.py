import pandas as pd
import json
import re
import os
from datetime import datetime

def extraer_distrito(texto):
    if not texto:
        return "LIMA"
    match = re.search(r'DISTRITO ([A-ZÑÁÉÍÓÚ\s]+)', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return "LIMA"

def enviar():
    print("📁 Archivos en el directorio:", os.listdir())
    
    excel_files = [f for f in os.listdir() if f.endswith('.xlsx')]
    if not excel_files:
        print("❌ No se encontró Excel")
        return
    
    df = pd.read_excel(excel_files[0])
    print(f"📂 Columnas: {df.columns.tolist()}")
    
    # Extraer distrito de la tarjeta externa
    df['Distrito_Extraido'] = df['Información Tarjeta Externa (Comercial)'].apply(extraer_distrito)
    
    # Extraer precio numérico
    def extraer_precio(texto):
        if not texto:
            return 0
        match = re.search(r'([\d,]+\.\d{2})', str(texto).replace(',', ''))
        if match:
            return float(match.group(1))
        return 0
    
    df['Precio_Num'] = df['Precio Base'].apply(extraer_precio)
    
    if df.empty or len(df) == 0:
        print("⚠️ No hay datos")
        return
    
    top1 = df.nsmallest(1, 'Precio_Num').iloc[0]
    
    whatsapp_msg = f"""🔥 REMATE DEL DÍA - {datetime.now().strftime('%d/%m')}

🏷️ {top1['Código de Remate']}
📍 {top1['Distrito_Extraido']}
💰 {top1['Precio Base']}

👉 Ver todos: https://remaju-automation.netlify.app/mapa_remates.html"""
    
    print("📱 Mensaje WhatsApp:")
    print(whatsapp_msg)
    print(f"✅ {len(df)} remates procesados")

if __name__ == "__main__":
    enviar()
