import os

import requests
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL")


def login_user(username: str, password: str) -> dict | None:
    try:
        form_data = {"username": username, "password": password}

        response = requests.post(
            f"{BACKEND_URL}/token",
            data=form_data,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def get_user_info(access_token: str) -> dict | None:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BACKEND_URL}/get_current_user_by_access_token", headers=headers
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def register_user(login: str, password: str, name: str) -> dict | None:
    try:
        user_data = {"login": login, "password": password, "name": name}

        response = requests.post(
            f"{BACKEND_URL}/register",
            json=user_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            return None
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"detail": str(e)}


def top_up_balance(access_token: str, amount: float) -> dict | None:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{BACKEND_URL}/top_up_balance",
            params={"amount": amount},
            headers=headers,
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None
