#!/usr/bin/env python
"""
Script to check Django version and run basic project checks
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'studybud.settings')
    
    try:
        django.setup()
        print(f"Django version: {django.get_version()}")
        print("Django setup successful!")
        
        # Run system check
        print("\nRunning system check...")
        execute_from_command_line(['manage.py', 'check'])
        
        print("\nProject is ready for Django 5.1!")
        
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)