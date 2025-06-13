import undetected_chromedriver as UC
import os

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
script_dir = os.path.dirname(os.path.abspath(__file__))
extension_path = os.path.join(script_dir, "Extension", "uBlock-Origin-Lite")

def iniciar_driver():
    try:
        # Verifica si la extensión es válida
        manifest = os.path.join(extension_path, "manifest.json")
        if not os.path.exists(manifest):
            print("❌ No se encontró manifest.json en la extensión.")
            return None

        chrome_options = UC.ChromeOptions()
        #chrome_options.binary_location = "/usr/bin/google-chrome"

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
            #browser_executable_path="/usr/bin/google-chrome"
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
