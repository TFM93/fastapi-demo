from fastapi.testclient import TestClient
import string
import random
from main import app

client = TestClient(app)


def test_register():
    response = client.post("/register/", json={"email": "", "tenant": ""})
    assert response.status_code == 422

    response = client.post(
        "/register/", json={"email": "tttt", "tenant": "123"}
    )
    assert response.status_code == 422

    randomName = "".join(
        random.choice(string.ascii_uppercase + string.digits)
        for _ in range(10)
    )

    response = client.post(
        "/register/",
        json={"email": f"{randomName}@email.com", "tenant": "123"},
    )
    assert response.status_code == 200
