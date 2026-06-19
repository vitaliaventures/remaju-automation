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
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        print("1. Conectando a REMAJU...")
        response = await page.goto("https://remaju.pj.gob.pe/remaju/pages/publico/mostrarRemates.xhtml", timeout=60000)
        print(f"   Status code: {response.status if response else 'No response'}")
        
        await page.wait_for_load_state("networkidle")
        await page.wait_for_timeout(5000)
        
        # Mostrar título y URL actual
        title = await page.title()
        print(f"   Título de la página: {title}")
        print(f"   URL actual: {page.url}")
        
        # Tomar screenshot para depuración
        await page.screenshot(path="debug.png")
        print("   📸 Screenshot guardado: debug.png")
        
        # Verificar contenido de la página
        body_text = await page.locator("body").inner_text()
        print(f"   Longitud del texto en body: {len(body_text)} caracteres")
        
        # Buscar "Remate N°" en el texto
        if "Remate N°" in body_text:
            print("   ✅ ¡Remates encontrados en el texto!")
        else:
            print("   ❌ No se encontró 'Remate N°' en el texto")
            print("   Primeros 500 caracteres del body:")
            print(body_text[:500])
            await browser.close()
            return
        
        print("2. Buscando remates...")
        
        # Intentar con diferentes selectores
        selectores = [
            "text=Remate N°",
            "a:has-text('Remate')",
            "button:has-text('Detalle')",
            ".ui-datatable-data",
            "table"
        ]
        
        for selector in selectores:
            try:
                count = await page.locator(selector).count()
                print(f"   Selector '{selector}': {count} elementos encontrados")
            except:
                print(f"   Selector '{selector}': ERROR")
        
        # Intentar con el selector que funciona
        try:
            await page.wait_for_selector("text=Remate N°", timeout=30000)
            print("   ✅ Remates encontrados con selector 'text=Remate N°'")
        except:
            print("   ❌ No se encontraron remates con selector 'text=Remate N°'")
            await browser.close()
            return
        
        lista_maestra_bloomberg = []
        numero_pagina = 1
        
        while True:
            print(f"\n📖 PÁGINA N° {numero_pagina}")
            
            # Contar remates
            remates_elementos = await page.locator("text=Remate N°").all()
            total_remates_pagina = len(remates_elementos)
            print(f"   {total_remates_pagina} remates en esta página.")
            
            if total_remates_pagina == 0:
                print("   No hay remates, saliendo...")
                break
            
            for i in range(total_remates_pagina):
                print(f"   Extrayendo remate {i+1}/{total_remates_pagina}...")
                try:
                    tarjeta_titulo = page.locator("text=Remate N°").nth(i)
                    texto_tarjeta = await tarjeta_titulo.locator("xpath=../../..").inner_text()
                    texto_limpio_tarjeta = " ".join(texto_tarjeta.split())
                    
                    remate_match = re.search(r'(Remate N°\s*\d+)', texto_limpio_tarjeta, re.IGNORECASE)
                    num_remate = remate_match.group(1).strip() if remate_match else f"Remate_{i+1}_P{numero_pagina}"
                    
                    print(f"      Remate encontrado: {num_remate}")
                    lista_maestra_bloomberg.append({
                        "Código de Remate": num_remate,
                        "Número de Expediente": "Pendiente",
                        "Precio Base": "Pendiente",
                        "Tasación Real": "Pendiente",
                        "Página Origen": numero_pagina,
                        "Información Ficha Interna (Completa)": "Pendiente",
                        "Información Tarjeta Externa (Comercial)": texto_limpio_tarjeta
                    })
                    
                except Exception as e:
                    print(f"      ⚠️ Error en remate {i+1}: {e}")
            
            # Paginación
            print(f"\n🔄 Buscando página siguiente...")
            try:
                boton_siguiente = page.locator("a.ui-paginator-next")
                if await boton_siguiente.count() > 0:
                    clases = await boton_siguiente.first.get_attribute("class") or ""
                    if "ui-state-disabled" in clases:
                        print("🏁 Última página.")
                        break
                    else:
                        await boton_siguiente.first.click()
                        await page.wait_for_load_state("networkidle")
                        await page.wait_for_timeout(3000)
                        numero_pagina += 1
                        continue
            except Exception as e:
                print(f"   Error en paginación: {e}")
            
            break
        
        if lista_maestra_bloomberg:
            df = pd.DataFrame(lista_maestra_bloomberg)
            df.to_excel("Bloomberg_Remates_Organizado.xlsx", index=False)
            print(f"\n📊 {len(lista_maestra_bloomberg)} registros en {numero_pagina} páginas.")
            
            print("📁 Directorio actual:", os.getcwd())
            print("📁 Archivos en el directorio:", os.listdir())
            
            if os.path.exists("Bloomberg_Remates_Organizado.xlsx"):
                print("✅ Excel guardado correctamente")
            else:
                print("❌ ERROR: El Excel NO se guardó")
        else:
            print("\n⚠️ No se extrajo ningún remate.")
            
        # Guardar screenshot como artefacto
        if os.path.exists("debug.png"):
            print("📸 Screenshot guardado: debug.png")
            
        await browser.close()

if __name__ == "__main__":
    asyncio.run(ejecutar_scraper())
