import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import re
import os

async def ejecutar_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-gpu"]
        )
        context = await browser.new_context()
        page = await context.new_page()
        
        print("1. Conectando a REMAJU...")
        await page.goto("https://remaju.pj.gob.pe/remaju/", timeout=60000)
        await page.wait_for_load_state("networkidle")
        
        print("2. Entrando a Remates...")
        await page.click("text=Remates")
        await page.wait_for_timeout(5000)
        
        print("3. Extrayendo datos...")
        lista = []
        pagina = 1
        
        while True:
            print(f"   Página {pagina}...")
            
            # Esperar que carguen los remates
            try:
                await page.wait_for_selector("text=Remate N°", timeout=10000)
            except:
                print("   No hay más remates")
                break
            
            # Contar remates
            remates = await page.locator("text=Remate N°").all()
            print(f"   Encontrados {len(remates)} remates")
            
            for i, remate in enumerate(remates):
                try:
                    # Obtener texto de la tarjeta
                    texto = await remate.locator("xpath=../../..").inner_text()
                    
                    # Extraer código
                    codigo = re.search(r'Remate N°\s*(\d+)', texto)
                    codigo = f"Remate N° {codigo.group(1)}" if codigo else "Desconocido"
                    
                    # Extraer precio
                    precio = re.search(r'(S/\.\s*[\d,]+\.\d{2}|\$\s*[\d,]+\.\d{2})', texto)
                    precio = precio.group(1) if precio else "S/. 0"
                    
                    lista.append({
                        "Código de Remate": codigo,
                        "Precio Base": precio,
                        "Página Origen": pagina,
                        "Información Tarjeta Externa (Comercial)": " ".join(texto.split())
                    })
                    print(f"      ✅ {codigo}")
                except:
                    pass
            
            # Buscar botón siguiente
            try:
                siguiente = page.locator("a.ui-paginator-next:not(.ui-state-disabled)")
                if await siguiente.count() > 0:
                    await siguiente.first.click()
                    await page.wait_for_timeout(4000)
                    pagina += 1
                else:
                    print("   Última página")
                    break
            except:
                print("   Última página")
                break
        
        if lista:
            df = pd.DataFrame(lista)
            df.to_excel("Bloomberg_Remates_Organizado.xlsx", index=False)
            print(f"\n✅ {len(lista)} remates guardados")
            print("📁 Archivos:", os.listdir())
        else:
            print("❌ No se extrajo nada")
        
        await browser.close()

if __name__ == "__main__":
    asyncio.run(ejecutar_scraper())
