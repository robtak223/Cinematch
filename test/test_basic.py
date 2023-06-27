from conftest import test_client


# Ensure get homepage succeeds
def test_home_page(test_client):
    response = test_client.get('/')
    assert response.status_code == 200
    assert b"cheatsheet" in response.data

# Ensure cannot post to homepage
def test_home_page_post(test_client):
    response = test_client.post('/')
    assert response.status_code == 405
    assert b"cheatsheet" not in response.data
