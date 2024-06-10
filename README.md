# telegram_bot

## Источники данных
Бот имеет возможность получать данные из двух источников данных:
1. CryptoCompare powered by CCDATA ([httpcryptocompare.com](https://www.cryptocompare.com/) с использованием API
2. Центробанк России с использованием парсинга HTML-страницы

Источник данных (тип API) выбирается в конфигурационном файле:
```
[default]
API = CBRF
```

## Кэширование информации
Если выбран источник данных CBRF (Центробанк России), то для кэширования данных применяется Redis. Его параметры должны быть указаны в конфигурационном файле:
```
[api.CBRF]
REDIS_ADDR = host.domain
REDIS_PORT = 6379
REDIS_PASSWORD = Pa$$w0RD
```
