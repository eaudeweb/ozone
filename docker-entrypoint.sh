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

# This will only have effect if there translations repo has been
# clones and copied as well.
python manage.py compilemessages

if [ "x$DJANGO_COLLECT_STATIC" = "xyes" ]; then
  python manage.py collectstatic --noinput
fi

if [ "x$DJANGO_LOAD_INITIAL_FIXTURES" = 'xyes' ]; then
    python manage.py load_initial_fixtures
fi

case "$1" in
    manage)
        exec python manage.py "$1"
        ;;
    run)
        exec python manage.py runserver 0.0.0.0:${REPORTEK_GUNICORN_PORT:-8000}
        ;;
    *)
esac
