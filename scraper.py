import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import random
import re

async def ejecutar_scraper():
    async with async_playwright() as p:
        # HEADLESS=True para GitHub Actions (sin ventana gráfica)
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-gpu"
            ]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("1. Conectando a REMAJU...")
        await page.goto("https://remaju.pj.gob.pe/remaju/pages/publico/mostrarRemates.xhtml", timeout=60000)
        await page.wait_for_load_state("networkidle")
        
        print("2. Esperando que cargue la tabla...")
        await page.wait_for_selector("button:has-text('Detalle')", timeout=30000)
        
        lista_maestra_bloomberg = []
        numero_pagina = 1
        max_paginas = 50
        
        while True:
            print(f"\n📖 PÁGINA N° {numero_pagina}")
            
            # Obtener botones "Detalle" de la página actual
            botones_detalle = await page.locator("button:has-text('Detalle')").all()
            total_remates_pagina = len(botones_detalle)
            print(f"   {total_remates_pagina} remates en esta página.")
            
            if total_remates_pagina == 0:
                print("   ⚠️ No hay remates en esta página. Saliendo...")
                break
            
            for i in range(total_remates_pagina):
                print(f"   Extrayendo remate {i+1}/{total_remates_pagina}...")
                try:
                    # Capturar tarjeta externa
                    tarjeta_titulo = page.locator("text=Remate N°").nth(i)
                    texto_tarjeta = await tarjeta_titulo.locator("xpath=../../..").inner_text()
                    texto_limpio_tarjeta = " ".join(texto_tarjeta.split())
                    
                    remate_match = re.search(r'(Remate N°\s*\d+)', texto_limpio_tarjeta, re.IGNORECASE)
                    num_remate = remate_match.group(1).strip() if remate_match else f"Remate_{i+1}_P{numero_pagina}"
                    
                    # Click en Detalle
                    boton_actual = page.locator("button:has-text('Detalle')").nth(i)
                    await boton_actual.scroll_into_view_if_needed()
                    await boton_actual.click()
                    
                    # Esperar que cargue el detalle
                    await page.wait_for_timeout(3000)
                    await page.wait_for_url("**/mostrarDetalleRemate.xhtml", timeout=15000)
                    await page.wait_for_load_state("networkidle")
                    
                    # Extraer datos del detalle
                    texto_profundo = await page.locator("body").inner_text()
                    texto_limpio_profundo = " | ".join([linea.strip() for linea in texto_profundo.split('\n') if linea.strip()])
                    
                    exp_match = re.search(r'Expediente\s*\|\s*([\d\-]+[\w\-]+)', texto_limpio_profundo, re.IGNORECASE)
                    expediente = exp_match.group(1).strip() if exp_match else "No localizado"
                    
                    precio_match = re.search(r'Precio Base\s*\|\s*((?:S/\.|S/\s+|\$)\s*[\d,]+\.\d{2})', texto_limpio_profundo, re.IGNORECASE)
                    precio_base = precio_match.group(1).strip() if precio_match else "Revisar Ficha"
                    
                    tasacion_match = re.search(r'Tasación\s*\|\s*((?:S/\.|S/\s+|\$)\s*[\d,]+\.\d{2})', texto_limpio_profundo, re.IGNORECASE)
                    tasacion = tasacion_match.group(1).strip() if tasacion_match else "Revisar Ficha"
                    
                    # Volver usando "Regresar"
                    await page.locator("button:has-text('Regresar')").first.click()
                    await page.wait_for_timeout(3000)
                    
                    lista_maestra_bloomberg.append({
                        "Código de Remate": num_remate,
                        "Número de Expediente": expediente,
                        "Precio Base": precio_base,
                        "Tasación Real": tasacion,
                        "Página Origen": numero_pagina,
                        "Información Ficha Interna (Completa)": texto_limpio_profundo,
                        "Información Tarjeta Externa (Comercial)": texto_limpio_tarjeta
                    })
                    print(f"      ✅ {num_remate}")
                    
                except Exception as e:
                    print(f"      ⚠️ Error en remate {i+1}: {e}")
                    try:
                        await page.goto("https://remaju.pj.gob.pe/remaju/pages/publico/mostrarRemates.xhtml")
                        await page.wait_for_load_state("networkidle")
                        await page.wait_for_timeout(3000)
                    except:
                        pass
                    continue
            
            # --- PAGINACIÓN ---
            print(f"\n🔄 Buscando página siguiente...")
            
            try:
                boton_siguiente = page.locator("a.ui-paginator-next")
                if await boton_siguiente.count() > 0:
                    clases = await boton_siguiente.first.get_attribute("class") or ""
                    if "ui-state-disabled" in clases:
                        print("🏁 Última página alcanzada.")
                        break
                    else:
                        await boton_siguiente.first.click()
                        await page.wait_for_load_state("networkidle")
                        await page.wait_for_timeout(3000)
                        numero_pagina += 1
                        continue
            except:
                pass
            
            # Si llegamos aquí, no hay más páginas
            print("🏁 Fin del proceso.")
            break
        
        # --- EXPORTAR ---
        if lista_maestra_bloomberg:
            df = pd.DataFrame(lista_maestra_bloomberg)
            df.to_excel("Bloomberg_Remates_Organizado.xlsx", index=False)
            print(f"\n📊 ¡EXTRACCIÓN COMPLETADA!")
            print(f"   {len(lista_maestra_bloomberg)} registros en {numero_pagina} páginas.")
        else:
            print("\n⚠️ No se extrajo ningún remate.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(ejecutar_scraper())
