from configparser import ConfigParser
from bs4 import BeautifulSoup
import requests
import json
import redis
from datetime import datetime


class APIException(Exception):
    pass


class CurrencyAPI:
    def __init__(self, cfg: ConfigParser) -> None:
        self.__api = cfg['default']['API']
        self.__url = cfg[f'api.{self.__api}']['URL']

        self.__currency = {}
        for cur in cfg['currency']:
            self.__currency[cur.upper()] = cfg['currency'][cur]

        if self.__api == 'CBRF':
            self.__cache = redis.Redis(
                host=cfg[f'api.{self.__api}']['REDIS_ADDR'],
                port=int(cfg[f'api.{self.__api}']['REDIS_PORT']),
                password=cfg[f'api.{self.__api}']['REDIS_PASSWORD']
            )
            self.update_cbrf_courses()

    def __str__(self) -> str:
        text = f'API = {str(self.api)}\n'
        text = text + f'url = {str(self.url)}\n'
        if self.api == 'CBRF':
            delta = int(datetime.now().timestamp() - float(self.__cache.get("cbrf_timestamp")))
            text = text + f'Кэш обновлялся {delta} сек назад'
        return text

    def update_cbrf_courses(self) -> None:
        courses = {'RUB': 1.0}

        html = requests.get(self.__url).content
        soup = BeautifulSoup(html, 'lxml')
        div = soup.find('div', class_='table-wrapper')
        rows = div.find_all('tr')

        for row in rows:
            cols: list[str] = row.getText().split('\n')
            if cols[2] in self.currency:
                courses[cols[2]] = float(cols[5].replace(',', '.')) / int(cols[3])

        self.__cache.set('cbrf_courses', json.dumps(courses))
        self.__cache.set('cbrf_timestamp', datetime.now().timestamp())

    def get_price(self, base: str, quote: str, amount: str) -> float:
        price = None
        base = base.upper()
        quote = quote.upper()
        try:
            amount = float(amount)
        except ValueError:
            raise APIException(f'Указано некорректное количество валюты: {amount}')

        match self.api:
            case 'CBRF':
                if datetime.now().timestamp() - float(self.__cache.get('cbrf_timestamp')) > 600:
                    self.update_cbrf_courses()

                try:
                    base_course = float(json.loads(self.__cache.get('cbrf_courses'))[base])
                except KeyError:
                    raise APIException(f'Невозможно найти курс валюты {base}')

                try:
                    quote_course = float(json.loads(self.__cache.get('cbrf_courses'))[quote])
                except KeyError:
                    raise APIException(f'Невозможно найти курс валюты {quote}')

                price = base_course / quote_course * amount

            case 'CCDATA':
                try:
                    r = requests.get(self.__url + f'fsym={base}&tsyms={quote}')
                    course = json.loads(r.content)
                    price = course[quote] * amount
                except KeyError:
                    raise APIException(f'Не удалось найти курс для пары валют {base}/{quote}')

        if price is not None:
            return price
        else:
            raise APIException(f'Не удалось обработать запрос: {base} {quote} {amount}')

    @property
    def api(self) -> str:
        return self.__api.upper()

    @property
    def url(self) -> str:
        return self.__url

    @property
    def currency(self) -> list[str]:
        return list(self.__currency.keys())

    def currency_desc(self, cur: str) -> str:
        return self.__currency[cur.upper()]

