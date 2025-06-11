#!/bin/bash

echo " Aplicando migraciones..."
python manage.py collectstatic --noinput
sleep 2

python manage.py makemigrations database --noinput
python manage.py migrate --noinput
sleep 2

echo " Ejecutando servidor Django en 0.0.0.0:8000..."
python manage.py runserver 0.0.0.0:8000