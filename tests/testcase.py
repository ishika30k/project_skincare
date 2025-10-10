import pytest 
from app import app

def test_homepage(client):
    response = client.get('/')
    assert response.status_code == 200


def test_valid_login(client):
    """Test login with valid cred"""
    response=client.post('/login', data={
        "username":"ishika12",
        "password":"Ishika12"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Skin Info" in response.data

def test_login_invalid_password(client):
    """Login with Invalid Password"""
    response=client.post("/login", data={
        "username":"ishika12",
        "password":"wrongpass"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

def test_login_empty_fields(client):
    """Test login with empty fields"""
    response=client.post("/login", data={
        "username":"",
        "password":""
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"Invalid username or password" in response.data

# def test_valid_signin(client):
#     """Test signin with valid cred"""
#     response=client.post('/signin', data={
#         "username":"girl123",
#         "name":"girl g",
#         "password":"Girl1235",
#         "phone":"8327927365",
#         "email":"girl30@gmail.com",
#         "gender":"female",
#         "age":"23"
#     }, follow_redirects=True)
#     assert response.status_code == 200
#     assert b"Account created successfully! Please login." in response.data

def test_signin_existing_username(client):
    """Test signin with existing username"""
    response=client.post('/signin', data={
        "username":"ishika12",
        "name":"ishika g",
        "password":"Ishika123",
        "phone":"8327927364",
        "email":"ishika30@gmail.com",
        "gender":"female",
        "age":"23"
    }, follow_redirects=True)
    assert response.status_code == 200
    assert b"This username is already taken. Please choose another." in response.data

def 



