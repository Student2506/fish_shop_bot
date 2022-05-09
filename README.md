# Проект телеграм-бота продающего рыбок из интернет-магазина  
## Цель  
Создать бота с возможностью взаимодействовать с магазином Motlin (Elasticpath).  

## Технологии  
- Telegram  
- Python 3.9  
- Redis  
- Elasticpath API


## Инсталляция  
1. Создать окружение  
```
python -m venv venv  
source venv/bin/activate  
```
2. Установить зависимости  
```
python -m pip install --upgrade pip  
pip install -r requirements.txt  
```
3. Завести (создать) переменные среды окружения (токены):  

API Motlin  
- FISH_SHOP_CLIENT_ID=

База Redis  
- FISH_SHOP_DATABASE_HOST=  
- FISH_SHOP_DATABASE_PASSWORD=  
- FISH_SHOP_DATABASE_PORT=  

Токен Telegram  
- FISH_SHOP_TG_BOTID=  

4. Создать товары через админку сайта

5. Запустить бота  
```
python shop_bot_tg.py  
```

[Пример бота](https://t.me/selling_fish_student83_bot)  
 