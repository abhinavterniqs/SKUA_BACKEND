import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from adminpanel.models import Role, Department
from users.models import User

def seed():
    # Create Roles
    admin_role, created = Role.objects.get_or_create(name='admin')
    if created:
        print("Role 'admin' created.")
    
    user_role, created = Role.objects.get_or_create(name='user')
    if created:
        print("Role 'user' created.")

    # Create Departments
    dept_it, created = Department.objects.get_or_create(name='IT')
    if created:
        print("Department 'IT' created.")

    dept_hr, created = Department.objects.get_or_create(name='HR')
    if created:
        print("Department 'HR' created.")

    # Create Superuser
    email = 'admin@skua.com'
    password = 'admin'
    username = 'admin'
    
    if not User.objects.filter(email=email).exists():
        user = User.objects.create_superuser(
            email=email,
            username=username,
            password=password,
            role=admin_role,
            department=dept_it
        )
        print(f"Superuser created: {email} / {password}")
    else:
        print("Superuser already exists.")

if __name__ == '__main__':
    seed()
