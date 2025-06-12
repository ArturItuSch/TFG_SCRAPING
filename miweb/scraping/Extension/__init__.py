"""
El submódulo `Extension` contiene archivos relacionados con la extensión de navegador **uBlock Origin**,
utilizada durante el proceso de scraping con navegador automatizado.

### Propósito

La extensión uBlock se emplea para bloquear anuncios, popups y scripts no deseados que puedan interferir
con el scraping o ralentizar la carga de páginas. Esto garantiza una ejecución más estable, rápida y libre
de elementos que podrían alterar la estructura del DOM de las webs objetivo.

### Uso

Esta extensión es cargada por el navegador controlado desde el módulo `driver.py` al iniciar una sesión de scraping. 
Se monta como extensión externa en la instancia de Chrome automatizada.

**Nota:** No contiene lógica Python, pero es un componente clave para asegurar la fiabilidad del scraping.
"""