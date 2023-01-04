import requests
import os
from datetime import datetime, timedelta
import vonage

STOCK_NAME = 'TSLA'
COMPANY_NAME = "Tesla Inc"
price_api_key = os.environ.get('PRICE_API_KEY')
news_api_key = os.environ.get('NEWS_API_KEY')
secret_key = os.environ.get('SECRET_KEY')
sms_api_key = os.environ.get('SMS_API_KEY')
USER = 'anujadilshan8@gmail.com'
PASSWORD = os.environ.get('EMAIL_PASSWORD')

client = vonage.Client(key=sms_api_key, secret=secret_key)
sms = vonage.Sms(client)

STOCK_ENDPOINT = "https://www.alphavantage.co/query"
NEWS_ENDPOINT = "https://newsapi.org/v2/everything"

date_today = datetime.now().date()
yesterday = f"{date_today - timedelta(days=1)}"
day_before_yesterday = f'{date_today - timedelta(days=2)}'

percentage_difference = 0
last_fluctuation_date = ''

stock_parameters = {
    'function': 'TIME_SERIES_DAILY_ADJUSTED',
    'symbol': STOCK_NAME,
    'interval': '60min',
    'apikey': price_api_key
}

news_parameters = {
    'q': 'Tesla Inc',
    'apikey': news_api_key,
    'from': day_before_yesterday,
    'to': yesterday,
    'sortBy': 'popularity',
    'searchIn': 'title,description'
}
request_stock_price = requests.get(url=STOCK_ENDPOINT, params=stock_parameters)
request_stock_price.raise_for_status()
stock_price_data = request_stock_price.json()
print(stock_price_data)


def yesterday_close_price_detector():
    global yesterday
    try:
        y_close_price = stock_price_data['Time Series (Daily)'][yesterday]['4. close']
    except KeyError:
        return f'Market was close at {yesterday}'
    else:
        return float(y_close_price)


def d_b_y_price_detector():
    global day_before_yesterday
    try:
        d_b_y_close_price = stock_price_data['Time Series (Daily)'][day_before_yesterday]['4. close']
    except KeyError:
        return f'Market was close at {day_before_yesterday}'
    else:
        return float(d_b_y_close_price)


def price_compare(y_close_price: float, d_b_y_close_price: float):
    global percentage_difference
    global last_fluctuation_date

    difference_of_values = y_close_price - d_b_y_close_price
    if difference_of_values < 0:
        difference_of_values2 = -difference_of_values
        percentage_difference = round((difference_of_values2 / d_b_y_close_price) * 100, 2)

    else:
        percentage_difference = round((difference_of_values / d_b_y_close_price) * 100, 2)

    if percentage_difference >= 5:
        with open('data.txt', 'w') as data_file:
            last_fluctuation_date = f'{yesterday}/{day_before_yesterday}:'
            data_file.write(last_fluctuation_date)
        if difference_of_values > 0:
            with open('msg.txt', 'w') as msg_file1:
                msg_file1.write(f'TSLA: UP by {percentage_difference}%\n\n{yesterday} closing price: ${y_close_price}\n'
                                f'{day_before_yesterday} closing price: ${d_b_y_close_price}\n\n')
            with open('data.txt', 'a') as data_file:
                data_file.write(f"{percentage_difference}\n")
            return percentage_difference

        else:
            with open('msg.txt', 'w') as msg_file1:
                msg_file1.write(
                    f'TSLA: Down by {percentage_difference}%\n\n{yesterday} closing price: ${y_close_price}\n'
                    f'{day_before_yesterday} closing price: ${d_b_y_close_price}\n\n')
            with open('data.txt', 'a') as data_file:
                data_file.write(f"{percentage_difference}\n")
            return percentage_difference

    else:
        return None


yesterday_close_price = yesterday_close_price_detector()
day_before_yesterday_close_price = d_b_y_price_detector()

if type(yesterday_close_price) == float and type(day_before_yesterday_close_price) == float:
    percentage_difference = price_compare(yesterday_close_price, day_before_yesterday_close_price)
    if percentage_difference is not None:
        news_response = requests.get(url="https://newsapi.org/v2/everything", params=news_parameters)
        news_response.raise_for_status()
        news_data = news_response.json()['articles'][:3]
        news_titles = [news['title'] for news in news_data]
        news_descriptions = [news['content'] for news in news_data]
        for i in range(3):
            with open('msg.txt', 'a') as msg_file:
                if i != 2:
                    msg_file.write(
                        f'Headline: {news_titles[i]}\nBrief: {news_descriptions[i]}\n_____________________________\n')
                else:
                    msg_file.write(f'Headline: {news_titles[i]}\nBrief: {news_descriptions[i]}\n')
        with open('msg.txt', 'r') as msg_file:
            msg = msg_file.read()
            print(msg)
        responseData = sms.send_message(
            {
                "from": "94772644436",
                "to": "94755124038",
                "text": msg,
            }
        )

        if responseData["messages"][0]["status"] == "0":
            print("Message sent successfully.")
        else:
            print(f"Message failed with error: {responseData['messages'][0]['error-text']}")
else:
    with open('data.txt', 'r') as data_file:
        x = data_file.read().splitlines()[0].split(':')
        last_fluctuation_date = x[0]
        percentage_difference = x[1]
    if type(yesterday_close_price) is str and type(day_before_yesterday_close_price) is str:
        with open('msg.txt', 'w') as msg_file:
            msg_file.write(f'{yesterday} and {day_before_yesterday} the market was close.\n'
                           f'Last recorded noticeable fluctuation is {percentage_difference}% at {last_fluctuation_date}')

    elif type(yesterday_close_price) is str and type(day_before_yesterday_close_price) is not str:
        with open('msg.txt', 'w') as msg_file:
            msg_file.write(f'{yesterday}, the market was close. The last close price was '
                           f'${day_before_yesterday_close_price} recorded at {day_before_yesterday}\n'
                           f'Last recorded noticeable fluctuation is {percentage_difference}% at {last_fluctuation_date}')
    else:
        with open('msg.txt', 'w') as msg_file:
            msg_file.write(f'{day_before_yesterday}, the market was close. The last close price was '
                           f'${yesterday_close_price} recorded at {yesterday}\n'
                           f'Last recorded noticeable fluctuation is {percentage_difference}% at {last_fluctuation_date}')

    with open('msg.txt', 'r') as msg_file:
        msg = msg_file.read()
    responseData = sms.send_message(
        {
            "from": "94772644436",
            "to": "94755124038",
            "text": msg,
        }
    )

    if responseData["messages"][0]["status"] == "0":
        print("Message sent successfully.")
    else:
        print(f"Message failed with error: {responseData['messages'][0]['error-text']}")