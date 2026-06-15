import asyncio
from playwright.async_api import async_playwright
import pandas as pd
import random
import re

async def resolver_captcha_manualmente(page):
    """Detecta si saltó el bloqueo de reCAPTCHA y pausa el script para resolución humana."""
    if await page.locator("iframe[src*='recaptcha']").count() > 0 or "validate" in page.url.lower():
        print("\n🚨 [ALERTA ANTIRADAR]: El sistema ha detectado un reCAPTCHA del Poder Judicial.")
        print("   -> Por favor, ve a la ventana del navegador y resuélvelo manualmente con el mouse.")
        
        for _ in range(3):
            print('\a')
            await asyncio.sleep(0.5)
            
        print("   Waiting: Tienes 40 segundos para resolver el captcha en pantalla...")
        try:
            await page.wait_for_url("**/mostrarDetalleRemate.xhtml", timeout=40000)
            print("   🔑 Captcha superado. Retomando control automatizado...")
            return True
        except Exception:
            print("   ❌ No se detectó la resolución del captcha en el tiempo límite.")
            return False
    return False

async def ejecutar_scraper():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=["--disable-blink-features=AutomationControlled"]
        )
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("1. Conectando a la plataforma REMAJU con huella humanizada...")
        await page.goto("https://remaju.pj.gob.pe/remaju/", timeout=60000)
        await page.wait_for_load_state("networkidle")
        
        print("2. Entrando a la sección de Remates...")
        await page.locator("a:has-text('Remates')").first.click()
        await page.wait_for_timeout(6000)
        
        lista_maestra_bloomberg = []
        numero_pagina = 1
        
        while True:
            print(f"\n========================================================")
            print(f"📖 AUDITANDO MIGRACIÓN DE DATOS - PÁGINA N° {numero_pagina}")
            print(f"========================================================")
            
            await page.wait_for_selector("button:has-text('Detalle')", timeout=15000)
            botones_detalle = await page.locator("button:has-text('Detalle')").all()
            total_remates_pagina = len(botones_detalle)
            print(f"   Se detectaron {total_remates_pagina} remates en esta página.")
            
            for i in range(total_remates_pagina):
                espera_humana = random.uniform(3.0, 5.5)
                print(f"\n⏳ Pausa preventiva anti-radar de {espera_humana:.2f} segundos...")
                await asyncio.sleep(espera_humana)
                
                print(f"🚀 Extrayendo Información del Remate {i+1} de {total_remates_pagina} (Pág. {numero_pagina})...")
                try:
                    # --- CAPTURA COMERCIAL DE SUPERFICIE ---
                    tarjeta_titulo = page.locator("text=Remate N°").nth(i)
                    texto_tarjeta = await tarjeta_titulo.locator("xpath=../../..").inner_text()
                    texto_limpio_tarjeta = " ".join(texto_tarjeta.split())
                    
                    remate_match = re.search(r'(Remate N°\s*\d+)', texto_limpio_tarjeta, re.IGNORECASE)
                    num_remate = remate_match.group(1).strip() if remate_match else f"Remate_{i+1}_P{numero_pagina}"
                    
                    # --- NAVEGACIÓN PROFUNDA ---
                    print("   -> Accediendo a la ficha técnica interna...")
                    boton_actual = page.locator("button:has-text('Detalle')").nth(i)
                    await boton_actual.scroll_into_view_if_needed()
                    await boton_actual.click()
                    
                    # Verificación técnica de Captcha
                    await page.wait_for_timeout(2500)
                    if not page.url.endswith("mostrarDetalleRemate.xhtml"):
                        await resolver_captcha_manualmente(page)
                    
                    await page.wait_for_url("**/mostrarDetalleRemate.xhtml", timeout=12000)
                    await page.wait_for_load_state("networkidle")
                    
                    # Absorción de datos
                    texto_profundo_pagina = await page.locator("body").inner_text()
                    texto_limpio_profundo = " | ".join([linea.strip() for linea in texto_profundo_pagina.split('\n') if linea.strip()])
                    
                    # Extracción de campos
                    exp_match = re.search(r'Expediente\s*\|\s*([\d\-]+[\w\-]+)', texto_limpio_profundo, re.IGNORECASE)
                    expediente_judicial = exp_match.group(1).strip() if exp_match else "No localizado"
                    
                    precio_internomatch = re.search(r'Precio Base\s*\|\s*((?:S/\.|S/\s+|\$)\s*[\d,]+\.\d{2})', texto_limpio_profundo, re.IGNORECASE)
                    precio_base = precio_internomatch.group(1).strip() if precio_internomatch else "Revisar Ficha"
                    
                    tasacion_match = re.search(r'Tasación\s*\|\s*((?:S/\.|S/\s+|\$)\s*[\d,]+\.\d{2})', texto_limpio_profundo, re.IGNORECASE)
                    tasacion = tasacion_match.group(1).strip() if tasacion_match else "Revisar Ficha"

                    # --- REGRESO SEGURO USANDO EL BOTÓN NATIVO "REGRESAR" ---
                    print("   -> Retornando usando el botón 'Regresar' de la ficha...")
                    # Ubicamos el botón azul oficial 'Regresar' dentro del panel interno
                    await page.locator("button:has-text('Regresar')").first.click()
                    await page.wait_for_timeout(4500) # Estabilización de la tabla en su página actual
                    
                    lista_maestra_bloomberg.append({
                        "Código de Remate": num_remate,
                        "Número de Expediente": expediente_judicial,
                        "Precio Base": precio_base,
                        "Tasación Real": tasacion,
                        "Página Origen": numero_pagina,
                        "Información Ficha Interna (Completa)": texto_limpio_profundo,
                        "Información Tarjeta Externa (Comercial)": texto_limpio_tarjeta
                    })
                    print(f"   ✅ Indexado: {num_remate} | Exp. {expediente_judicial}")
                    
                except Exception as e:
                    print(f"   ⚠️ Reajuste de contingencia en elemento {i+1}: {e}")
                    try:
                        await page.goto("https://remaju.pj.gob.pe/remaju/pages/publico/mostrarRemates.xhtml")
                        await page.wait_for_load_state("networkidle")
                        await page.wait_for_timeout(4000)
                    except Exception:
                        pass
                    continue
            
            # --- EVALUACIÓN DE PAGINACIÓN GENERAL ---
            print(f"\n🔄 Evaluando si existe una página siguiente...")
            boton_siguiente = page.locator("a.ui-paginator-next").first
            
            if await boton_siguiente.count() > 0:
                clases = await boton_siguiente.get_attribute("class")
                if "ui-state-disabled" in clases:
                    print("🏁 ¡Fin del mapa! Se ha alcanzado la última página disponible de REMAJU.")
                    break
                else:
                    print("➡️ Avanzando de página de forma lineal...")
                    await asyncio.sleep(random.uniform(2.0, 4.0))
                    await boton_siguiente.click()
                    numero_pagina += 1
                    await page.wait_for_timeout(6000)
            else:
                print("🏁 No se localizó el componente de paginación. Proceso cerrado.")
                break
                
        # --- EXPORTACIÓN GENERAL ---
        if lista_maestra_bloomberg:
            df = pd.DataFrame(lista_maestra_bloomberg)
            df.to_excel("Bloomberg_Remates_Organizado.xlsx", index=False)
            print(f"\n📊 ¡MATRIZ FINANCIERA COMPLETADA!")
            print(f"   Extracción masiva exitosa. {len(lista_maestra_bloomberg)} registros guardados.")
        else:
            print("\n⚠️ Alerta: Matriz de almacenamiento vacía.")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(ejecutar_scraper())