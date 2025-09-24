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


def get_time_series(access_token: str, ts_id: int) -> dict | None:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BACKEND_URL}/time_series/{ts_id}",
            headers=headers,
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def get_all_models(access_token: str) -> list[dict] | None:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BACKEND_URL}/models",
            headers=headers,
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def delete_time_series(access_token: str, ts_id: int, user_id: int) -> bool:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.delete(
            f"{BACKEND_URL}/time_series/{ts_id}",
            params={"user_id": user_id},
            headers=headers,
        )

        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def create_time_series(access_token: str, ts_data: dict) -> dict | None:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{BACKEND_URL}/time_series",
            json=ts_data,
            headers=headers,
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def get_analysis_task_status(access_token: str, ts_id: int) -> dict | None:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BACKEND_URL}/analysis_task_status/{ts_id}",
            headers=headers,
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def start_analysis_task(access_token: str, ts_id: int) -> dict | None:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.post(
            f"{BACKEND_URL}/analyze_time_series",
            params={"ts_id": ts_id},
            headers=headers,
        )

        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.exceptions.RequestException:
        return None


def get_forecast_task_status(access_token: str, ts_id: int) -> dict | None:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BACKEND_URL}/forecast_task_status/{ts_id}", headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def get_forecast_data(access_token: str, forecast_id: int) -> dict | None:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(
            f"{BACKEND_URL}/forecast_data/{forecast_id}", headers=headers
        )
        if response.status_code == 200:
            return response.json()
        return None
    except requests.exceptions.RequestException:
        return None


def create_forecast_task(
    access_token: str, ts_id: int, model: str, fh: int, cost: float
) -> tuple[bool, dict | str]:
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        params = {"ts_id": ts_id, "model": model, "fh": fh, "cost": cost}
        response = requests.post(
            f"{BACKEND_URL}/forecast_time_series", headers=headers, params=params
        )
        return response.status_code == 200, (
            response.json() if response.status_code == 200 else response.text
        )
    except requests.exceptions.RequestException as e:
        return False, str(e)
