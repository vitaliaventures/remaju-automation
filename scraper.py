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
        
        lista_maestra_bloomberg = []
        numero_pagina = 1
        max_paginas = 50  # Límite de seguridad
        
        while True:
            print(f"\n========================================================")
            print(f"📖 PÁGINA N° {numero_pagina}")
            print(f"========================================================")
            
            # Esperar que carguen los remates
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
            
            # --- PAGINACIÓN MEJORADA ---
            if numero_pagina >= max_paginas:
                print(f"⚠️ Límite de {max_paginas} páginas alcanzado.")
                break
                
            print(f"\n🔄 Buscando página siguiente...")
            
            # Esperar a que la paginación esté disponible
            await page.wait_for_timeout(1000)
            
            # Verificar si el botón "Siguiente" está deshabilitado
            try:
                boton_siguiente = page.locator(".ui-paginator-next")
                if await boton_siguiente.count() > 0:
                    clases = await boton_siguiente.first.get_attribute("class") or ""
                    if "ui-state-disabled" in clases:
                        print("🏁 Botón 'Siguiente' deshabilitado. Última página.")
                        break
            except:
                pass
            
            # Intentar diferentes métodos de click
            click_exitoso = False
            
            # Método 1: Click normal en el botón
            try:
                boton = page.locator(".ui-paginator-next:not(.ui-state-disabled)")
                if await boton.count() > 0:
                    await boton.first.click()
                    await page.wait_for_load_state("networkidle")
                    await page.wait_for_timeout(4000)
                    click_exitoso = True
                    print(f"   ✅ Avanzando a página {numero_pagina + 1} (Método 1)")
            except:
                pass
            
            # Método 2: JavaScript directo
            if not click_exitoso:
                try:
                    resultado = await page.evaluate("""() => {
                        const nextBtn = document.querySelector('.ui-paginator-next:not(.ui-state-disabled)');
                        if (nextBtn) {
                            nextBtn.click();
                            return true;
                        }
                        return false;
                    }""")
                    if resultado:
                        await page.wait_for_load_state("networkidle")
                        await page.wait_for_timeout(4000)
                        click_exitoso = True
                        print(f"   ✅ Avanzando a página {numero_pagina + 1} (Método 2 - JS)")
                except:
                    pass
            
            # Método 3: Hover y click con retraso
            if not click_exitoso:
                try:
                    boton = page.locator(".ui-paginator-next:not(.ui-state-disabled)")
                    if await boton.count() > 0:
                        await boton.first.hover()
                        await page.wait_for_timeout(200)
                        await boton.first.click()
                        await page.wait_for_load_state("networkidle")
                        await page.wait_for_timeout(4000)
                        click_exitoso = True
                        print(f"   ✅ Avanzando a página {numero_pagina + 1} (Método 3 - Hover)")
                except:
                    pass
            
            if not click_exitoso:
                print("🏁 No se pudo avanzar. Fin del proceso.")
                break
            else:
                numero_pagina += 1
                
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
