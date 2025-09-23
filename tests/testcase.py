import pytest 

def valid_login(client):
    """Test login with valid cred"""
    response=client.post("/login", data={
        "username":"ishika12",
        "password":"Ishika12"
    })
    assert response.status_code == 200
    assert b"dashboard" in response.data

def login_invalid_password(client):
    """Login with Invalid Password"""
    response=client.post("/login", data={
        "username":"ishika12",
        "password":"wrongpass"
    })
    assert response.status_code == 200
    assert b"Incorrect password" in response.data

def login_empty_fields(client):
    """Test login with empty fields"""
    response=client.post("/login", data={
        "username":"",
        "password":""
    })
    assert response.status_code == 200
    assert b"Fields cannot be empty" in response.data