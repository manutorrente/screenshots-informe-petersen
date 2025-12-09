from playwright.sync_api import sync_playwright
import time
import os
import re

def tomar_captura_kibana(url, nombre_archivo, output_dir="output"):
    with sync_playwright() as p:
        # Crear directorio de salida si no existe
        os.makedirs(output_dir, exist_ok=True)
        
        # headless=False para ver el proceso (cambiar a True cuando funcione bien)
        browser = p.chromium.launch(headless=False) 
        
        # Ajustar el tamaño del viewport para que la captura salga en HD
        context = browser.new_context(viewport={"width": 1920, "height": 1080})
        page = context.new_page()
        
        # 1. Ir a la URL. Si pide login, Kibana te redirigirá al login
        print(f"Navegando a {url}...")
        page.goto(url)

        # 2. MANEJO DE LOGIN (Ajustar selectores según tu Kibana)
        # Si la URL cambia a 'login', llenamos los datos
        if "login" in page.url:
            print("Detectado login, ingresando credenciales...")
            # Esperar que aparezca el campo de usuario
            page.wait_for_selector("input[name='username']", timeout=10000)
            
            page.fill("input[name='username']", "elastic")
            page.fill("input[name='password']", "qZm6hg_uamPr3Lo7NQa*")
            page.click("button[type='submit']") # O el selector del botón de entrar
            
            # Esperar a que redirija post-login
            page.wait_for_url(url, timeout=30000)

        # 3. ESPERA INTELIGENTE
        print("Esperando que cargue el dashboard...")
        
        # Opción A: Esperar a que no haya tráfico de red por 500ms (ideal para Kibana)
        page.wait_for_load_state("networkidle", timeout=60000)

        # Opción B: Esperar un selector más genérico de Kibana si .euiChart falla
        # 'canvas' suele estar en todos los gráficos, o la clase del panel principal
        try:
            # Intentamos esperar algo visual clave
            page.wait_for_selector("canvas, .euiPanel", state="visible", timeout=30000)
        except:
            print("Warning: No se detectó el selector específico, sacando foto igual...")

        # Un sleep extra de seguridad por si las animaciones de carga tardan
        time.sleep(10)

        # 3.5. Aplicar zoom para mejorar la claridad del texto
        page.evaluate("document.body.style.zoom = '150%'")
        time.sleep(2)  # Esperar a que se aplique el zoom

        # 4. Extraer el panel ID de la URL y sacar screenshot del panel específico
        import re
        panel_id_match = re.search(r'/view/[^/]+/([a-f0-9\-]+)', url)
        if panel_id_match:
            panel_id = panel_id_match.group(1)
            panel_selector = f"#panel-{panel_id} > div > div.euiPanel.euiPanel--plain.embPanel"
            output_path = os.path.join(output_dir, f"{nombre_archivo}.png")
            page.locator(panel_selector).screenshot(path=output_path)
        else:
            # Fallback a screenshot completo si no se encuentra el panel ID
            output_path = os.path.join(output_dir, f"{nombre_archivo}.png")
            page.screenshot(path=output_path, full_page=True)
        print(f"Captura guardada: {output_path}")
        
        browser.close()

# Ejecutar con múltiples URLs
urls = {
    "2_nifi_totales": "http://172.30.215.74:5601/app/dashboards#/view/424da3d5-da5b-456d-8f14-316245bf3465/5ae34707-af68-4df4-8af6-c43a1bff6808?_g=(refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "3_kifi1" : "http://172.30.215.74:5601/app/dashboards#/view/424da3d5-da5b-456d-8f14-316245bf3465/b83b2d6e-0b97-42fc-9a9b-02e76f722368?_g=(filters:!(),refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "4_kifi2" : "http://172.30.215.74:5601/app/dashboards#/view/424da3d5-da5b-456d-8f14-316245bf3465/3deb7bfc-149c-4dc6-ba54-11c062cd2d7b?_g=(filters:!(),refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "5_nifi_prod" : "http://172.30.215.74:5601/app/dashboards#/view/424da3d5-da5b-456d-8f14-316245bf3465/c91f9ce9-819e-48ae-ad18-40303c0f8554?_g=(filters:!(),refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "6_prod_standalone" : "http://172.30.215.74:5601/app/dashboards#/view/424da3d5-da5b-456d-8f14-316245bf3465/6a1dbd9d-5c1d-4faf-b860-e9439f9a6118?_g=(filters:!(),refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "7_kifi_dis" : "http://172.30.215.74:5601/app/dashboards#/view/424da3d5-da5b-456d-8f14-316245bf3465/c3660adb-4716-4a5f-9d95-997df7d873a4?_g=(filters:!(),refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "8_fraude" : "http://172.30.215.74:5601/app/dashboards#/view/424da3d5-da5b-456d-8f14-316245bf3465/4781872a-91fb-4bbd-998a-efbcb826f73c?_g=(filters:!(),refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "9_heap" : "http://172.30.215.74:5601/app/dashboards#/view/2c0917b0-29dd-11f0-a0d3-6bbe8930ff1a/c77dc7b0-6b23-4160-9bce-0cd2c39db28c?_g=(refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "10_impala_en_ejecucion" : "http://172.30.215.74:5601/app/dashboards#/view/c9a6a391-c283-4d98-ae3d-9902a2a43105/447a8242-e8be-4927-9531-314663bdc902?_g=(refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "11_impala_por_estado" : "http://172.30.215.74:5601/app/dashboards#/view/c9a6a391-c283-4d98-ae3d-9902a2a43105/1efc9ca9-b0a3-46fb-a788-37a43e458536?_g=(refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "12_impala_encoladas" : "http://172.30.215.74:5601/app/dashboards#/view/c9a6a391-c283-4d98-ae3d-9902a2a43105/5101fdc7-c24f-4ddc-929c-1c4c0a26ec9b?_g=(refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "13_yarn_por_estado" : "http://172.30.215.74:5601/app/dashboards#/view/55243110-36ae-11f0-a0d3-6bbe8930ff1a/50b86b5b-2308-43e4-b4f0-6c1c4924c079?_g=(refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "14_yarn_completadas" : "http://172.30.215.74:5601/app/dashboards#/view/55243110-36ae-11f0-a0d3-6bbe8930ff1a/213e232f-467b-41a4-b6e0-f6795fb0b4e5?_g=(refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
    "15_yarn_aceptadas_ejecucion" : "http://172.30.215.74:5601/app/dashboards#/view/55243110-36ae-11f0-a0d3-6bbe8930ff1a/7ac1bd80-c6a5-41dd-bbde-1ce51adc7727?_g=(refreshInterval:(pause:!f,value:1800000),time:(from:now-5d,to:now))",
}

for nombre, url in urls.items():
    tomar_captura_kibana(url, nombre)