#!/bin/sh

if [ -z "$POSTGRES_HOST" ]; then
  export POSTGRES_HOST="postgres"
fi

while ! nc -z ${POSTGRES_HOST} 5432; do
  echo "Waiting for Postgres server at '$POSTGRES_HOST' to accept connections on port 5432..."
  sleep 1s
done

if [ "x$DJANGO_MIGRATE" = 'xyes' ]; then
    python manage.py migrate --noinput
fi

if [ "x$DJANGO_LOAD_INITIAL_FIXTURES" = 'xyes' ]; then
    python manage.py load_initial_fixtures
fi

case "$1" in
    migrate)
        exec python manage.py migrate --noinput
        ;;
    run)
        exec uwsgi uwsgi.ini
        ;;
    runserver)
        exec python manage.py runserver 0.0.0.0:8000
        ;;
    *)
esac
