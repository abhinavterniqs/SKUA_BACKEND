import os
import django
import json

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from rest_framework.test import APIClient
from rest_framework import status

def run_verification():
    print("Starting Verification...")
    client = APIClient()

    # 1. Login
    print("\n1. Testing Admin Login...")
    login_data = {
        'email': 'admin@skua.com',
        'password': 'admin'
    }
    response = client.post('/api/auth/login/', login_data, format='json')
    if response.status_code == 200:
        print("Login Successful.")
        token = response.data['access']
        client.credentials(HTTP_AUTHORIZATION='Bearer ' + token)
        
        # Verify Response Structure
        if 'user' in response.data and response.data['user']['role'] == 'admin':
            print("Response structure verified (User data present).")
        else:
             print("FAILED: Response structure mismatch.")
    else:
        print(f"FAILED: Login failed with {response.status_code} - {response.data}")
        return

    # 2. Create Role
    print("\n2. Testing Role Creation...")
    role_data = {'name': 'Manager'}
    response = client.post('/api/roles/', role_data, format='json')
    if response.status_code == 201:
        print("Role 'Manager' created.")
        manager_role_id = response.data['id']
    else:
        print(f"FAILED: Role creation failed - {response.data}")
        manager_role_id = None

    # 3. Create Department
    print("\n3. Testing Department Creation...")
    dept_data = {'name': 'Sales'}
    response = client.post('/api/departments/', dept_data, format='json')
    if response.status_code == 201:
        print("Department 'Sales' created.")
        sales_dept_id = response.data['id']
    else:
         print(f"FAILED: Department creation failed - {response.data}")
         sales_dept_id = None

    # 4. Create User
    print("\n4. Testing User Creation...")
    if manager_role_id and sales_dept_id:
        user_data = {
            'email': 'manager@skua.com',
            'username': 'manager',
            'password': 'password123',
            'role': manager_role_id,
            'department': sales_dept_id,
            'first_name': 'John',
            'last_name': 'Doe'
        }
        response = client.post('/api/users/', user_data, format='json')
        if response.status_code == 201:
            print("User 'manager' created successfully.")
        else:
            print(f"FAILED: User creation failed - {response.data}")
    else:
        print("Skipping User Creation due to previous failures.")

    # 5. List Users
    print("\n5. Testing List Users...")
    response = client.get('/api/users/')
    if response.status_code == 200:
        count = len(response.data)
        # Should be at least 2 (admin + manager)
        print(f"List Users successful. Count: {count}")
    else:
        print(f"FAILED: List Users failed - {response.status_code}")

    print("\nVerification Complete.")

if __name__ == '__main__':
    run_verification()
