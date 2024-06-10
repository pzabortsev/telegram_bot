from telebot import TeleBot, ExceptionHandler, types
from configparser import ConfigParser
from extensions import CurrencyAPI

greetings_text = '''
Вас приветствует бот - калькулятор валют!

Доступные команды:
/values - бот покажет, с какими валютами он может работать
/api_info - информация об используемом API
/start или /help - вывод этого сообщения

[<i>Исходная валюта</i>] [<i>целевая валюта</i>] [<i>количество исходной валюты</i>]
- это и есть основной функционал бота

Пример:
    <b>USD RUB 100</b> - сколько стоит 100 usd в рублях
    <b>RUB EUR 3000</b> - сколько ЕВРО можно купить за 3000 рублей
'''


class MyExceptionHandler(ExceptionHandler):
    def handle(self, exception) -> bool:
        print("ОШИБКА: ", exception)
        return True


class MyTelegramBot(TeleBot):
    def __init__(self, config_file: str) -> None:
        cfg = ConfigParser()
        cfg.read(config_file, encoding='utf-8')
        self.__token = cfg['default']['TOKEN']
        super().__init__(self.__token, exception_handler=MyExceptionHandler())
        self.__currency_api = CurrencyAPI(cfg)

        @self.message_handler(commands=['start', 'help'])
        def start_help_handler(message: types.Message):
            username = f'{message.chat.first_name} {message.chat.last_name}'
            self.send_message(message.chat.id, f'{username}, {greetings_text}', parse_mode='HTML')

        @self.message_handler(commands=['values'])
        def values_handler(message: types.Message):
            text = 'Перечень поддерживаемых валют:\n'
            i = 1
            for cur in self.api.currency:
                text = f'{text}{i}. {self.api.currency_desc(cur)} ({cur})\n'
                i += 1
            self.send_message(message.chat.id, text)

        @self.message_handler(commands=['api_info'])
        def debug_handler(message: types.Message):
            self.send_message(message.chat.id, str(self.api))

        @self.message_handler(content_types=['text'])
        def main_handler(message: types.Message):
            _data = message.text.split(' ')
            if len(_data) > 3:
                self.send_message(message.chat.id, 'Слишком много параметров. Используйте команду /help')
            elif len(_data) < 3:
                self.send_message(message.chat.id, 'Недостаточно параметров. Используйте команду /help')
            else:
                try:
                    base, quote, amount = _data
                    price = self.api.get_price(base, quote, amount)
                    self.send_message(message.chat.id,
                                      f'Стоимость {amount} {self.api.currency_desc(base)}'
                                      f' составляет {price:,.2f} {self.api.currency_desc(quote)}')
                except Exception as e:
                    self.send_message(message.chat.id, f'Произошла ошибка: {e}')

    @property
    def api(self) -> CurrencyAPI:
        return self.__currency_api

    def run(self) -> None:
        self.infinity_polling()


if __name__ == '__main__':
    bot = MyTelegramBot('telegram_bot.ini')
    bot.run()