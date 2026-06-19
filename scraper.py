import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import random
import re
import os

async def ejecutar_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled", "--no-sandbox", "--disable-gpu"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("1. Conectando a la plataforma REMAJU...")
        await page.goto("https://remaju.pj.gob.pe/remaju/", timeout=60000)
        await page.wait_for_load_state("networkidle")
        
        print("2. Entrando a la sección de Remates...")
        await page.locator("a:has-text('Remates')").first.click()
        await page.wait_for_timeout(6000)
        await page.wait_for_load_state("networkidle")
        
        # URL base
        base_url = page.url
        print(f"   URL base: {base_url}")
        
        lista_maestra_bloomberg = []
        numero_pagina = 1
        total_paginas = None
        
        # Intentar obtener el total de páginas
        try:
            paginacion_texto = await page.locator(".ui-paginator-current").inner_text()
            match = re.search(r'de\s+(\d+)', paginacion_texto)
            if match:
                total_paginas = int(match.group(1))
                print(f"   📄 Total de páginas: {total_paginas}")
        except:
            total_paginas = 50  # Estimación
        
        while True:
            print(f"\n========================================================")
            print(f"📖 PÁGINA N° {numero_pagina}")
            print(f"========================================================")
            
            # Verificar si estamos en la página correcta
            await page.wait_for_timeout(2000)
            
            try:
                await page.wait_for_selector("button:has-text('Detalle')", timeout=15000)
            except:
                print("   ⚠️ No se encontraron remates. Saliendo...")
                break
                
            botones_detalle = await page.locator("button:has-text('Detalle')").all()
            total_remates_pagina = len(botones_detalle)
            print(f"   Se detectaron {total_remates_pagina} remates en esta página.")
            
            if total_remates_pagina == 0:
                break
            
            # Extraer remates
            for i in range(total_remates_pagina):
                await asyncio.sleep(random.uniform(0.8, 1.5))
                
                print(f"   Extrayendo remate {i+1}/{total_remates_pagina}...")
                try:
                    tarjeta_titulo = page.locator("text=Remate N°").nth(i)
                    texto_tarjeta = await tarjeta_titulo.locator("xpath=../../..").inner_text()
                    texto_limpio_tarjeta = " ".join(texto_tarjeta.split())
                    
                    remate_match = re.search(r'(Remate N°\s*\d+)', texto_limpio_tarjeta, re.IGNORECASE)
                    num_remate = remate_match.group(1).strip() if remate_match else f"Remate_{i+1}_P{numero_pagina}"
                    
                    boton_actual = page.locator("button:has-text('Detalle')").nth(i)
                    await boton_actual.scroll_into_view_if_needed()
                    await boton_actual.click()
                    
                    await page.wait_for_timeout(3000)
                    await page.wait_for_url("**/mostrarDetalleRemate.xhtml", timeout=12000)
                    await page.wait_for_load_state("networkidle")
                    
                    texto_profundo_pagina = await page.locator("body").inner_text()
                    texto_limpio_profundo = " | ".join([linea.strip() for linea in texto_profundo_pagina.split('\n') if linea.strip()])
                    
                    exp_match = re.search(r'Expediente\s*\|\s*([\d\-]+[\w\-]+)', texto_limpio_profundo, re.IGNORECASE)
                    expediente_judicial = exp_match.group(1).strip() if exp_match else "No localizado"
                    
                    precio_internomatch = re.search(r'Precio Base\s*\|\s*((?:S/\.|S/\s+|\$)\s*[\d,]+\.\d{2})', texto_limpio_profundo, re.IGNORECASE)
                    precio_base = precio_internomatch.group(1).strip() if precio_internomatch else "Revisar Ficha"
                    
                    tasacion_match = re.search(r'Tasación\s*\|\s*((?:S/\.|S/\s+|\$)\s*[\d,]+\.\d{2})', texto_limpio_profundo, re.IGNORECASE)
                    tasacion = tasacion_match.group(1).strip() if tasacion_match else "Revisar Ficha"

                    await page.locator("button:has-text('Regresar')").first.click()
                    await page.wait_for_timeout(3000)
                    
                    lista_maestra_bloomberg.append({
                        "Código de Remate": num_remate,
                        "Número de Expediente": expediente_judicial,
                        "Precio Base": precio_base,
                        "Tasación Real": tasacion,
                        "Página Origen": numero_pagina,
                        "Información Ficha Interna (Completa)": texto_limpio_profundo,
                        "Información Tarjeta Externa (Comercial)": texto_limpio_tarjeta
                    })
                    print(f"      ✅ {num_remate}")
                    
                except Exception as e:
                    print(f"      ⚠️ Error: {e}")
                    try:
                        await page.goto("https://remaju.pj.gob.pe/remaju/pages/publico/mostrarRemates.xhtml")
                        await page.wait_for_load_state("networkidle")
                        await page.wait_for_timeout(3000)
                    except:
                        pass
                    continue
            
            # --- CAMBIAR DE PÁGINA MANUALMENTE ---
            if numero_pagina >= total_paginas:
                print(f"🏁 Última página ({total_paginas}) alcanzada.")
                break
            
            print(f"\n🔄 Cambiando a página {numero_pagina + 1}...")
            
            # Buscar el input de página (si existe)
            try:
                input_pagina = page.locator(".ui-paginator-rpp-options").first
                if await input_pagina.count() > 0:
                    await input_pagina.select_option(str(numero_pagina + 1))
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(4000)
                    numero_pagina += 1
                    print(f"   ✅ Cambiado a página {numero_pagina} (Método 1 - Select)")
                    continue
            except:
                pass
            
            # Método 2: Click en el número de página
            try:
                siguiente_numero = numero_pagina + 1
                boton_pagina = page.locator(f"a:has-text('{siguiente_numero}')").first
                if await boton_pagina.count() > 0:
                    await boton_pagina.click()
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(4000)
                    numero_pagina += 1
                    print(f"   ✅ Cambiado a página {numero_pagina} (Método 2 - Click número)")
                    continue
            except:
                pass
            
            # Método 3: Botón "Siguiente" estándar
            try:
                boton_siguiente = page.locator(".ui-paginator-next:not(.ui-state-disabled)")
                if await boton_siguiente.count() > 0:
                    await boton_siguiente.first.click()
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(4000)
                    numero_pagina += 1
                    print(f"   ✅ Cambiado a página {numero_pagina} (Método 3 - Siguiente)")
                    continue
            except:
                pass
            
            # Si llegamos aquí, no podemos avanzar
            print("🏁 No se pudo cambiar de página. Fin del proceso.")
            break
                
        if lista_maestra_bloomberg:
            df = pd.DataFrame(lista_maestra_bloomberg)
            df.to_excel("Bloomberg_Remates_Organizado.xlsx", index=False)
            print(f"\n📊 ¡EXTRACCIÓN COMPLETADA!")
            print(f"   {len(lista_maestra_bloomberg)} registros en {numero_pagina} páginas.")
            print("📁 Archivos generados:", os.listdir())
        else:
            print("\n⚠️ No se extrajo ningún remate.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(ejecutar_scraper())
