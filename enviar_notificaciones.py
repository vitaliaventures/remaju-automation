import pandas as pd
import requests
import json
import re
from datetime import datetime

def extraer_distrito(texto):
    """Extrae el distrito del texto de la ficha interna"""
    if not texto:
        return "LIMA"
    
    # Buscar "Distrito Judicial | XXXX"
    match = re.search(r'Distrito Judicial\s*\|\s*([A-ZÑÁÉÍÓÚ\s]+)', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Buscar "DISTRITO DE XXXX"
    match = re.search(r'DISTRITO DE ([A-ZÑÁÉÍÓÚ\s]+)', texto, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    return "LIMA"

def extraer_precio_num(texto):
    """Extrae el número del precio"""
    if not texto:
        return 0
    precio_str = str(texto).replace(',', '').strip()
    match = re.search(r'([\d]+\.\d{2})', precio_str)
    if match:
        return float(match.group(1))
    match2 = re.search(r'(\d+)', precio_str)
    if match2:
        return float(match2.group(1))
    return 0

def enviar():
    df = pd.read_excel("Bloomberg_Remates_Organizado.xlsx")
    
    # Crear columna de distrito extraído
    df['Distrito_Extraido'] = df['Información Ficha Interna (Completa)'].apply(extraer_distrito)
    
    # Crear columna de precio numérico
    df['Precio_Num'] = df['Precio Base'].apply(extraer_precio_num)
    
    # Top 1 para WhatsApp
    top1 = df.nsmallest(1, 'Precio_Num').iloc[0]
    
    # Top 10 para Email
    top10 = df.nsmallest(10, 'Precio_Num').to_dict('records')
    
    # WhatsApp message
    whatsapp_msg = f"""🔥 REMATE DEL DÍA - {datetime.now().strftime('%d/%m')}

🏷️ {top1['Código de Remate']}
📍 {top1['Distrito_Extraido']}
💰 {top1['Precio Base']}
📢 {top1.get('Convocatoria', '1ra')}

👉 Ver todos: https://remaju-automation.netlify.app/mapa_remates.html"""
    
    print("📱 Mensaje WhatsApp generado:")
    print(whatsapp_msg)
    
    # Guardar top10 para respaldo
    with open(f"top10_{datetime.now().strftime('%Y%m%d')}.json", "w") as f:
        json.dump(top10, f, indent=2, ensure_ascii=False)
    
    print(f"✅ {len(top10)} remates guardados para newsletter")
    print(f"📊 Total remates procesados: {len(df)}")

if __name__ == "__main__":
    enviar()