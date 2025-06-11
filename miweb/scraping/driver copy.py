import undetected_chromedriver as UC
import os
import sys
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)
# Obtener ruta del script y archivos
script_dir = os.path.dirname(os.path.abspath(__file__))
chromedriver_path = os.path.join(script_dir, "ChromeDriver", "chromedriver.exe")
extension_path = os.path.join(script_dir, "Extension", "uBlock-Origin-Lite")
print(extension_path)

def iniciar_driver(): 
    try:
        # Verificar que la extensión tenga el archivo manifest.json
        if not os.path.exists(os.path.join(extension_path, "manifest.json")):
            print("El archivo manifest.json no se encuentra en la extensión")
            return
        # Configurar opciones de Chrome
        chrome_options = UC.ChromeOptions()
        chrome_options.add_experimental_option(
            "prefs",
            {
                "credentials_enable_service": False,
                "profile.password_mager_enabled": False,
            }
        )
        chrome_options.add_argument("--password-store-basic")
        chrome_options.add_argument(f'--load-extension={extension_path}') 
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")    
        chrome_options.add_argument("--headless") 
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        UC.TARGET_VERSION = 85
        driver = UC.Chrome(executable_path=chromedriver_path, options=chrome_options)
        return driver
    except Exception as e:
        print(f"❌ Error al iniciar ChromeDriver: {e}")

        # Verificar si el error es por incompatibilidad de versiones
        if "only supports Chrome version" in str(e):
            print("⚠ Parece que ChromeDriver y Google Chrome tienen versiones diferentes.")
            print("🔄 Intenta actualizar Chrome o usa WebDriver Manager para manejarlo automáticamente.")

        elif "cannot connect to chrome" in str(e):
            print("⚠ No se pudo conectar a Chrome. Asegúrate de que no haya instancias abiertas y vuelve a intentarlo.")

        print("❌ No se pudo iniciar el driver. Cerrando el programa...")
        

    