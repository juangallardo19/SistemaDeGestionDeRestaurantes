#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --noinput --settings=restaurante.settings.production

python manage.py migrate --settings=restaurante.settings.production

# Create superuser only if it doesn't already exist
if python manage.py shell --settings=restaurante.settings.production -c \
    "from django.contrib.auth import get_user_model; U=get_user_model(); exit(0 if U.objects.filter(username='$DJANGO_SUPERUSER_USERNAME').exists() else 1)" 2>/dev/null; then
    echo "Superuser '$DJANGO_SUPERUSER_USERNAME' already exists, skipping."
else
    python manage.py createsuperuser --noinput \
        --settings=restaurante.settings.production
    echo "Superuser '$DJANGO_SUPERUSER_USERNAME' created."
fi

# Load fixtures in order; skip any that don't exist yet
for fixture in 01_grupos 02_usuarios 03_menu 04_mesas 05_pedidos 06_reservas; do
    FIXTURE_FILE=$(find . -path "*/fixtures/${fixture}.json" 2>/dev/null | head -1)
    if [ -n "$FIXTURE_FILE" ]; then
        echo "Loading fixture: $FIXTURE_FILE"
        python manage.py loaddata "$FIXTURE_FILE" \
            --settings=restaurante.settings.production
    else
        echo "Fixture '$fixture' not found, skipping."
    fi
done
