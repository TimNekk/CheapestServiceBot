from enum import Enum
from typing import Union

import requests


class ApiKeyNotFound(Exception):
    pass


class IdNumNotFound(Exception):
    pass


class NoNumber(Exception):
    pass


class NoCode(Exception):
    pass


class Status(Enum):
    RESEND = "send"
    CANCEL = "end"
    BAD = "bad"


class VakSMSApi:
    BASE_URL = "https://vak-sms.com/api"
    GET_STATUS_URL = BASE_URL + "/getSmsCode"
    BALANCE_URL = BASE_URL + "/getBalance"
    PROLONG_URL = BASE_URL + "/prolongNumber"
    SET_STATUS_URL = BASE_URL + "/setStatus"

    def __init__(self, api_key: str):
        self.api_key = api_key
        self._data = {
            "apiKey": api_key
        }

        self._check_api_key()

    def _check_api_key(self) -> None:
        response = requests.get(self.BALANCE_URL, params=self._data)
        if response.json().get("error") == "apiKeyNotFound":
            raise ApiKeyNotFound()

    def get_code(self, id_num: str, all: bool = False) -> Union[str, tuple[str]]:
        data = self._data.copy()
        data["idNum"] = id_num
        if all:
            data["all"] = "1"

        response = requests.get(self.GET_STATUS_URL, params=data)
        response_json: dict = response.json()

        if response_json.get("error") == "idNumNotFound":
            raise IdNumNotFound()

        if "smsCode" in response_json.keys() and not response_json.get("smsCode"):
            raise NoCode()

        return response_json.get("smsCode")

    def prolong_number(self, number: Union[str, int], service: str) -> str:
        data = self._data.copy()
        data["service"] = service
        data["tel"] = str(number)

        response = requests.get(self.PROLONG_URL, params=data)
        response_json: dict = response.json()

        if response_json.get("error") == "noNumber":
            raise NoNumber()

        return response_json.get("idNum")

    def set_status(self, id_num: str, status: Status) -> None:
        data = self._data.copy()
        data["idNum"] = id_num
        data["status"] = status.value

        requests.get(self.SET_STATUS_URL, params=data)
