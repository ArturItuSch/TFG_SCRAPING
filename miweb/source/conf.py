# -- Project information -----------------------------------------------------
project = 'ScrapingLOL'
copyright = '2025, Artur Schuldt Iturri'
author = 'Artur Schuldt Iturri'
release = '1.0'

# -- General configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.napoleon',  # Si usas Google-style docstrings
    'sphinx.ext.todo',      # Para la administración de tareas
]

latex_elements = {
    'papersize': 'a4paper',  # Configura el tamaño de papel, puedes cambiarlo si lo necesitas
    'fontpkg': r'\usepackage{times}',  # Usa la fuente Times New Roman
    # Puedes agregar otras configuraciones de LaTeX aquí
}

latex_documents = [
    ('index', 'ScrapingLOL.tex', 'ScrapingLOL Documentation', 'Artur Schuldt Iturri', 'manual'),
]

templates_path = ['_templates']
exclude_patterns = []

language = 'es'

# -- Options for HTML output -------------------------------------------------
html_theme = 'alabaster'
html_static_path = ['_static']
