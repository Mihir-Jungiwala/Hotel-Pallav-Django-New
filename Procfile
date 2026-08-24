web: gunicorn Main.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --log-file -
release: python manage.py migrate --noinput
