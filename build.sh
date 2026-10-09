#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate
python seed_db.py

# --- AUTO-CONFIGURE SITE DOMAIN FOR GOOGLE OAUTH ---
# Sets the Django Site record to match the Render hostname so 
# Google OAuth callback URLs resolve correctly in production.
python manage.py shell -c "
from django.contrib.sites.models import Site
import os
hostname = os.getenv('RENDER_EXTERNAL_HOSTNAME', 'learning-365-ccs7.onrender.com')
site, created = Site.objects.get_or_create(id=1)
site.domain = hostname
site.name = 'Learning-365'
site.save()
print(f'[OK] Site domain set to: {hostname}')
"
