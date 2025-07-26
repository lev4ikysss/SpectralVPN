import datetime
import json
import requests
import uuid
from typing import Dict

class X3API:
    def __init__(self, host: str, login: str, password: str):
        """
        Класс для взаимодействия с API 3x-ui
        
        :param host: URL сервера панели управления (https://example.com)
        :param login: Логин администратора
        :param password: Пароль администратора
        """
        self.host = host.rstrip('/')
        self.login = login
        self.password = password
        self.data = {"username": login, "password": password}
        self.session = requests.Session()
        self._authenticate()

    def _authenticate(self) -> None:
        """Выполняет аутентификацию при инициализации"""
        response = self.session.post(f"{self.host}/login", data=self.data)
        response.raise_for_status()

    def test_connection(self) -> requests.Response:
        """Проверка подключения к API"""
        return self.session.post(f"{self.host}/login", data=self.data)

    def list_clients(self) -> dict:
        """Получение списка всех клиентов"""
        response = self.session.get(
            f'{self.host}/panel/api/inbounds/list', 
            json=self.data
        )
        return response.json()

    def add_client(self, days: int, telegram_id: str, user_id: str) -> requests.Response:
        """
        Добавление нового клиента
        
        :param days: Количество дней подписки
        :param telegram_id: ID Telegram пользователя
        :param user_id: Уникальный ID пользователя
        """
        expire_time = self._calculate_expiry_time(days)
        client_uuid = str(uuid.uuid1())
        
        client_data = {
            "id": client_uuid,
            "alterId": 90,
            "email": user_id,
            "limitIp": 1,
            "totalGB": 0,
            "expiryTime": expire_time,
            "enable": True,
            "tgId": telegram_id,
            "subId": ""
        }

        payload = {
            "id": 1,
            "settings": json.dumps({"clients": [client_data]})
        }

        headers = {"Accept": "application/json"}
        return self.session.post(
            f'{self.host}/panel/api/inbounds/addClient',
            headers=headers,
            json=payload
        )

    def update_client(self, days: int, user_id: str, is_enable: bool) -> requests.Response:
        """
        Обновление данных клиента
        
        :param days: Количество дней для продления
        :param user_id: Уникальный ID пользователя
        """
        clients = self._get_client_info(user_id)
        if not clients:
            raise ValueError(f"Клиент {user_id} не найден")

        for client_id, expiry in clients.items():
            new_time = self._calculate_expiry_time(days, base_time=expiry)
            
            client_data = {
                "id": client_id,
                "alterId": 90,
                "email": user_id,
                "limitIp": 3,
                "totalGB": 0,
                "expiryTime": new_time,
                "enable": is_enable,
                "tgId": user_id,
                "subId": ""
            }

            payload = {
                "id": 1,
                "settings": json.dumps({"clients": [client_data]})
            }

            headers = {"Accept": "application/json"}
            response = self.session.post(
                f'{self.host}/panel/api/inbounds/updateClient/{client_id}',
                headers=headers,
                json=payload
            )
        return response

    def get_connection_link(self, user_id: str) -> str:
        """
        Генерация ссылки для подключения
        
        :param user_id: Уникальный ID пользователя
        :return: Строка с подключением
        """
        config = self.list_clients()['obj'][0]
        settings = json.loads(config['settings'])
        stream = json.loads(config['streamSettings'])

        for client in settings["clients"]:
            if client['email'] == user_id:
                return (
                    f"vless://{client['id']}@vpn-x3.ru:52687/"
                    f"?type={stream['network']}&security={stream['security']}&fp=chrome"
                    f"&pbk=T_95HnSovtH9WNr_XfaJ9iL7xnwp96p8E2A8Q3_t_xk"
                    f"&sni=microsoft.com&sid=24705084&spx=%2F"
                    f"#VPN-X3-{user_id}"
                )
        raise ValueError(f"Клиент {user_id} не найден")

    def get_subscription_status(self, user_id: str) -> Dict[str, str]:
        """
        Проверка статуса подписки
        
        :param user_id: Уникальный ID пользователя
        :return: Словарь с данными о подписке
        """
        clients = self._get_client_info(user_id)
        if not clients:
            return {"status": "not_registered", "expiry": "-"}

        status_data = {}
        for client_id, expiry in clients.items():
            current_time = self._current_millis()
            is_active = expiry > current_time
            
            status_data = {
                "status": "active" if is_active else "expired",
                "expiry": self._format_timestamp(expiry)
            }
        return status_data

    def get_active_subscriptions(self) -> Dict[str, int]:
        """
        Получение списка активных подписок
        
        :return: Словарь {email: остаток_дней}
        """
        subscriptions = {}
        settings = json.loads(self.list_clients()['obj'][0]['settings'])
        
        for client in settings["clients"]:
            if client['expiryTime'] > self._current_millis():
                expiry_dt = datetime.datetime.fromtimestamp(client['expiryTime'] / 1000)
                days_left = (expiry_dt - datetime.datetime.now()).days
                subscriptions[client['email']] = max(0, days_left)
                
        return subscriptions

    # ======= Вспомогательные методы =======
    def _current_millis(self) -> int:
        """Текущее время в миллисекундах с 1970-01-01"""
        return int(datetime.datetime.now().timestamp() * 1000)

    def _format_timestamp(self, ts_millis: int) -> str:
        """Форматирование временной метки"""
        ts_seconds = ts_millis / 1000 + 10800  # UTC+3
        return datetime.datetime.utcfromtimestamp(ts_seconds).strftime('%d-%m-%Y %H:%M') + ' МСК'

    def _calculate_expiry_time(self, days: int, base_time: int = None) -> int:
        """Вычисление времени окончания подписки"""
        base = base_time or self._current_millis()
        if days == 0 :
            return 0
        return base + 86400000 * days

    def _get_client_info(self, user_id: str) -> Dict[str, int]:
        """Поиск клиента по user_id"""
        clients = {}
        settings = json.loads(self.list_clients()['obj'][0]['settings'])
        
        for client in settings["clients"]:
            if client['email'] == user_id:
                clients[client['id']] = client['expiryTime']
                
        return clients
