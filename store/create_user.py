#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'store.settings')
django.setup()

from django.contrib.auth.models import User

username = 'shinano'
email = 'shinano@example.com'
password = 'IJN_shinano03'

# Check if user already exists
if User.objects.filter(username=username).exists():
    print(f"Error: User '{username}' already exists.")
else:
    # Create superuser
    user = User.objects.create_superuser(username=username, email=email, password=password)
    print(f"✓ Superuser created successfully!")
    print(f"  Username: {user.username}")
    print(f"  Email: {user.email}")
    print(f"  Is Staff: {user.is_staff}")
    print(f"  Is Superuser: {user.is_superuser}")
