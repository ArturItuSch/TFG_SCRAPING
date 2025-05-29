#!/bin/bash

# Salir si cualquier comando falla
set -e

echo "🛠️ Aplicando migraciones..."
python manage.py makemigrations
python manage.py migrate

echo "🔍 Recolectando archivos estáticos..."
python manage.py collectstatic --noinput

echo "🚀 Iniciando servidor..."
python manage.py runserver 0.0.0.0:8000