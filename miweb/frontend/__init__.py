"""
frontend
========

Este módulo contiene toda la lógica de presentación de la aplicación web. Forma parte de la arquitectura MVC (Modelo-Vista-Controlador)
de Django, encargándose específicamente de la "Vista".

Componentes incluidos:
- `views.py`: Archivo que gestiona todas las consultas a la base de datos y prepara los datos que se mostrarán en las plantillas.
- `urls.py`: Define las rutas (endpoints) accesibles desde el navegador y las asocia a las vistas correspondientes.
- `templates/`: Contiene las plantillas HTML que definen la estructura visual del sitio web.
- `static/`: Recursos estáticos como hojas de estilo, scripts JavaScript, imágenes, íconos, etc.
- `templatetags/`: Filtros personalizados y etiquetas reutilizables en las plantillas.

Este módulo está diseñado para presentar de manera clara y dinámica los datos almacenados en la base de datos, permitiendo a los usuarios explorar estadísticas, partidos, jugadores y más información del entorno competitivo de League of Legends.
"""