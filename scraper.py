import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
from datetime import datetime

async def scraper_remaju():
    """Extrae todos los remates de REMAJU"""
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("🔍 Conectando a REMAJU...")
        await page.goto("https://remaju.pj.gob.pe/remaju/pages/publico/mostrarRemates.xhtml")
        await page.wait_for_load_state("networkidle")
        
        remates = []
        pagina = 1
        
        while True:
            print(f"📄 Procesando página {pagina}...")
            
            await page.wait_for_selector("button:has-text('Detalle')", timeout=10000)
            botones = await page.locator("button:has-text('Detalle')").all()
            
            for i, boton in enumerate(botones):
                print(f"   Extrayendo remate {i+1}/{len(botones)}...")
                
                # Obtener texto de la tarjeta
                tarjeta = await boton.locator("xpath=../../..").inner_text()
                
                # Extraer código
                codigo_match = re.search(r'Remate N°\s*(\d+)', tarjeta)
                codigo = f"Remate N° {codigo_match.group(1)}" if codigo_match else "Desconocido"
                
                # Extraer distrito del texto de la tarjeta
                distrito_match = re.search(r'DISTRITO DE ([A-ZÑÁÉÍÓÚ\s]+)', tarjeta, re.IGNORECASE)
                distrito = distrito_match.group(1).strip() if distrito_match else "LIMA"
                
                # Extraer precio
                precio_match = re.search(r'(S/\.\s*[\d,]+\.\d{2}|\$\s*[\d,]+\.\d{2})', tarjeta)
                precio = precio_match.group(1) if precio_match else "S/. 0"
                
                # Determinar convocatoria
                conv = "1ra" if "PRIMERA" in tarjeta.upper() else ("2da" if "SEGUNDA" in tarjeta.upper() else "3ra")
                
                remates.append({
                    "Código de Remate": codigo,
                    "Distrito Judicial": distrito,
                    "Precio Base": precio,
                    "Convocatoria": conv,
                    "Fecha Extracción": datetime.now().strftime("%Y-%m-%d")
                })
            
            # Siguiente página
            siguiente = page.locator("a.ui-paginator-next:not(.ui-state-disabled)")
            if await siguiente.count() == 0:
                break
                
            await siguiente.first.click()
            await page.wait_for_timeout(3000)
            pagina += 1
        
        await browser.close()
        
        # Guardar Excel
        df = pd.DataFrame(remates)
        df.to_excel("Bloomberg_Remates_Organizado.xlsx", index=False)
        print(f"✅ Guardados {len(remates)} remates")
        return remates

if __name__ == "__main__":
    asyncio.run(scraper_remaju())