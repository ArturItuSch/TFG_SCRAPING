"""
Módulo `driver`

Este módulo configura e inicia una instancia de `undetected_chromedriver` (UC) con 
opciones personalizadas y una extensión integrada (uBlock Origin Lite) para realizar 
scraping de forma más anónima y sin bloqueos publicitarios.

Funciones:
----------

- `iniciar_driver() -> webdriver.Chrome or None`:
    Inicializa un navegador Chrome en modo headless con varias configuraciones anti-detección.
    
    Configuraciones aplicadas:
    - Desactiva el almacenamiento de contraseñas y servicios de credenciales de Chrome.
    - Carga la extensión `uBlock-Origin-Lite` para bloquear anuncios.
    - Añade argumentos de seguridad y rendimiento (`--no-sandbox`, `--disable-gpu`, etc.).
    - Usa `undetected_chromedriver` para evitar detección en páginas protegidas.

    Returns:
        Instancia de Chrome configurada, o `None` si hubo algún error.

Constantes:
-----------
- `extension_path`: Ruta absoluta a la extensión uBlock-Origin-Lite dentro de la carpeta `Extension`.
"""
import undetected_chromedriver as UC
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
script_dir = os.path.dirname(os.path.abspath(__file__))
extension_path = os.path.join(script_dir, "Extension", "uBlock-Origin-Lite")

def iniciar_driver():
    """
    Inicializa y devuelve una instancia de Chrome con configuración personalizada usando `undetected_chromedriver`.

    Esta función está diseñada para realizar scraping evitando mecanismos de detección automatizada por parte de los sitios web.
    Además, carga la extensión uBlock Origin Lite para reducir el ruido visual y los tiempos de carga derivados de anuncios.

    Flujo de trabajo:
    -----------------
    - Verifica que exista `manifest.json` dentro de la carpeta de la extensión (`extension_path`).
    - Configura preferencias y argumentos de Chrome:
        - Desactiva el gestor de contraseñas.
        - Carga extensión `uBlock-Origin-Lite`.
        - Añade argumentos para ejecución headless, rendimiento y evitar detección (`--headless=new`, `--no-sandbox`, etc.).
    - Inicializa el navegador con `undetected_chromedriver` apuntando a `/usr/bin/google-chrome`.

    Returns:
        UC.Chrome: instancia de navegador Chrome configurada, lista para usar.
        None: si ocurre algún error al iniciar el navegador o no se encuentra el `manifest.json`.

    Ejemplo de uso:
    ---------------
    >>> driver = iniciar_driver()
    >>> if driver:
    >>>     driver.get("https://example.com")
    >>>     driver.quit()

    Requiere:
    ---------
    - Google Chrome y ChromeDriver instalados en `/usr/bin/google-chrome`.
    - Extensión `uBlock-Origin-Lite` en la ruta `scraping/Extension`.

    """
    try:
        # Verifica si la extensión es válida
        manifest = os.path.join(extension_path, "manifest.json")
        if not os.path.exists(manifest):
            print("❌ No se encontró manifest.json en la extensión.")
            return None

        chrome_options = UC.ChromeOptions()
        chrome_options.binary_location = "/usr/bin/google-chrome"

        chrome_options.add_experimental_option("prefs", {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False,
        })

        chrome_options.add_argument("--password-store=basic")
        chrome_options.add_argument(f"--load-extension={extension_path}")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")

        # No uses executable_path si ChromeDriver ya está en PATH o manejado por UC
        driver = UC.Chrome(
            options=chrome_options,
            browser_executable_path="/usr/bin/google-chrome"
        )
        return driver

    except Exception as e:
        print(f"❌ Error al iniciar ChromeDriver: {e}")
        return None

if __name__ == '__main__':
    driver = iniciar_driver()
    if driver:
        print("✅ ChromeDriver iniciado correctamente.")
        driver.quit()
