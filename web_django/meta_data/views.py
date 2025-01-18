import os
import sys
import pandas as pd
import yfinance as yf
import fear_and_greed
from django.shortcuts import render
from datetime import datetime, timedelta

# from .models import StockMetaData
from price.models import PriceData, InstitutionalInvestorData

from .util import ROOT, get_stocks, get_meta_data, download_stock_price, download_institutional_investor, download_punishment
from .update_db import update_price_table, update_institutional_table

# root = Path(__file__).resolve().parent
# print(root)  # ../meta_data
print('-' * 20)
today = datetime.today() + timedelta(days=1)
previous = today - timedelta(days=10)
print('today: ', today)
print('previous_date: ', previous)

# meta_data = StockMetaData.objects.all()
stocks = []
if 'makemigrations' not in sys.argv and 'migrate' not in sys.argv:
    stocks = get_stocks()


def get_latest_data():  # 即時爬取大盤資料
    start_date = datetime.strftime(previous, '%Y-%m-%d')
    end_date = datetime.strftime(today, '%Y-%m-%d')

    data = yf.download("^TWII", start=start_date, end=end_date)
    data['Date'] = data.index.astype(str)
    data = data.reset_index(drop=True)
    print(data)
    # Retrieve the current Fear and Greed Index
    index = fear_and_greed.get()
    return {
        'date': data['Date'].iloc[-1],
        'yesterday_close': round(data['Close'].iloc[-2], 2),
        'today_close': round(data['Close'].iloc[-1], 2),
        'low': round(data['Low'].iloc[-1], 2),
        'high': round(data['High'].iloc[-1], 2),
        'open': round(data['Open'].iloc[1], 2),
        'value': round(index.value),
        'description': index.description,
        'last_updated': index.last_update,
    }

'''
def update_price_table(df, date):
    # 更新股價db
    for i in range(len(df)):
        first_row = PriceData.objects.all().filter(
            code=int(df.code[i])).order_by("date")[0]
        row = PriceData(code=int(df.code[i]),
                        date=date,
                        key=f"{int(df.code[i])} {date}",
                        Open=df.Open[i],
                        High=df.High[i],
                        Low=df.Low[i],
                        Close=df.Close[i],
                        Volume=df.Volume[i],
                        PE=df.PE[i])

        # print(first_row.__str__())
        first_row.delete()
        row.save()


def update_institutional_table(df, date):
    for i in range(len(df)):
        first_row = InstitutionalInvestorData.objects.all().filter(
            code=int(df.code[i])).order_by("date")[0]
        row = InstitutionalInvestorData(code=int(df.code[i]),
                                        date=date,
                                        key=f'{int(df.code[i])} {date}',
                                        foreign_buy=df.foreign_buy[i],
                                        foreign_sell=df.foreign_sell[i],
                                        invest_buy=df.invest_buy[i],
                                        invest_sell=df.invest_sell[i],
                                        dealer_buy=df.dealer_buy[i],
                                        dealer_sell=df.dealer_sell[i])
        first_row.delete()
        row.save()
'''

def update_data(compare_date, token):
    # 下載資料+更新db, table: 0/1
    table = {0: 'price', 1: 'institutional'}
    file_path = f"{ROOT}/data_date_record.txt"
    # Check if the file exists
    if not os.path.exists(file_path):
        print(f"{file_path} not found. Creating a new file.")
        with open(file_path, "w") as f:
            f.write("2024-01-01\n2024-01-01\n")  # Default content
    
    with open(file_path, "r") as f:
        contents = f.readlines()

    last_date = contents[token]
    last_date = datetime.strptime(last_date.strip(), '%Y-%m-%d')
    print('last record date: ', last_date)
    tracking_days = (compare_date - last_date).days  # - 1

    if tracking_days:  # table PriceData needs to be updated
        dates = []
        for d in range(1, tracking_days + 1):
            datestr = datetime.strftime(last_date + timedelta(days=d),
                                        '%Y-%m-%d')
            # download data and cleaning
            if token == 0:
                one_day_data = download_stock_price(datestr.replace('-', ''))
                if type(one_day_data) == pd.DataFrame:
                    print('updating db', datestr)
                    update_price_table(one_day_data, datestr)
                    dates.append(datestr)
            elif token == 1:
                one_day_data = download_institutional_investor(
                    datestr.replace('-', ''))
                if type(one_day_data) == pd.DataFrame:
                    print('updating db', datestr)
                    update_institutional_table(one_day_data, datestr)
                    dates.append(datestr)

        if len(dates):
            contents[token] = dates[-1] + '\n'
            print(contents)
            with open(file_path, 'w') as f:
                f.writelines(contents)
            print('creating daily report')

        sum_up()  # create daily report
        daily_correlation()
    else:
        print(f'{table[token]} data is already up to date')


#        sum_up()  # create daily report


def sum_up():
    # 製作每日報告
    price_data = PriceData.objects.all().order_by('-date')
    dates = price_data.values('date').distinct()

    print(f"Distinct dates: {dates}")

    # Check if there are any dates
    if not dates.exists():
        print("No price data available.")
        return

    today = dates[0]  # Fetch the most recent date
    print(f"Today's date: {today}")
    previous_day = price_data.values('date').distinct()[1]
    # print(today, previous_day)
    today_price_data = price_data.filter(date=today['date'])
    # Query the latest institutional investor data
    today_data = InstitutionalInvestorData.objects.order_by('-date').values('date').distinct()

    if not today_data.exists():  # Check if any data exists
        print("No institutional investor data found.")
        return  # Or handle this case appropriately

    # Access the first element if data exists
    today = today_data[0]
    institutional_data = InstitutionalInvestorData.objects.filter(
        date=today['date'])

    meta_data = get_meta_data()
    price_df = [[
        row.code,
        meta_data.filter(code=row.code)[0].name,
        meta_data.filter(code=row.code)[0].industry_type, row.Close,
        row.Volume, row.PE
    ] for row in today_price_data if len(meta_data.filter(code=row.code)) > 0]
    price_df = pd.DataFrame(price_df,
                            columns=[
                                'code', 'name', 'industry_type', 'today_close',
                                'volume', 'PE'
                            ])
    previous_close = []
    for stock_code in price_df['code'].values:
        row = price_data.filter(date=previous_day['date']).filter(
            code=stock_code)
        if len(row):
            previous_close.append([stock_code, row[0].Close])

    institutional_df = [[
        row.code,
        row.foreign_buy - row.foreign_sell,
        row.invest_buy - row.invest_sell,
        row.dealer_buy - row.dealer_sell,
    ] for row in institutional_data]
    institutional_df = pd.DataFrame(
        institutional_df, columns=['code', 'foreign', 'insvest', 'dealer'])
    df = price_df.merge(pd.DataFrame(previous_close,
                                     columns=['code', 'previous_close']),
                        how='left')
    df = df.merge(institutional_df, how='left')
    df['volume'] = df['volume'] / 1000
    df['updowns'] = round(df['today_close'] - df['previous_close'], 2)
    df['fluctuation'] = round((df['today_close'] - df['previous_close']) *
                              100 / df['previous_close'], 2)
#     df['code'] = df['code'] + ' ' + df['name']
#     del df['name']
    # print(df)
    df.to_csv(f"{ROOT}/daily_report.csv", index=False)


def daily_correlation():
    df_closing = []
    for code in stocks:
        code = code.split(' ')[0]
        query_set = PriceData.objects.filter(code=code).order_by('date')
        if not query_set.exists():
            print(f"No data found for stock code: {code}")
            continue
        dates, close = [], []
        for row in query_set:
            dates.append(row.date)
            close.append(row.Close)
        if dates and close:
            df_closing.append(pd.DataFrame(close, index=dates, columns=[code]))
        else:
            print(f"No valid closing data for stock code: {code}")
    # Check if df_closing is empty
    if not df_closing:
        print("No data available for correlation. Skipping concatenation.")
        return
    df_closing = pd.concat(df_closing, axis=1)
    corr = df_closing.corr()
    #    print(corr)
    #    df_closing.to_csv(f"{ROOT}/daily_corr.csv")
    corr.to_csv(f"{ROOT}/daily_corr.csv")


def main(request):
    print('-' * 10, 'downloading latest data')
    data = get_latest_data()
    download_punishment(data['date'].replace('-', ''))
    if datetime.now().time().hour >= 14 or datetime.now().time(
    ).hour <= 9:  # 每天兩點以後更新股價
        print('-' * 10, 'updating stock price')
        update_data(datetime.strptime(data['date'], '%Y-%m-%d'), 0)

    if datetime.now().time().hour >= 17 or datetime.now().time(
    ).hour <= 9:  # 每天五點以後更新三大法人
        print('-' * 10, 'updating institutional transaction data')
        update_data(datetime.strptime(data['date'], '%Y-%m-%d'), 1)
    if data['today_close'] > data['yesterday_close']:
        trend_light = 'pink'
        trend = 'red'
    elif data['today_close'] < data['yesterday_close']:
        trend_light = 'lightgreen'
        trend = 'green'
    else:
        trend_light = 'lightgrey'
        trend = 'gold'
    data['trend'] = trend
    data['trend_background'] = trend_light
    print('-' * 20)
    print(data)
    #   print(stocks[0])
    data['stock_list'] = stocks
    return render(request, 'index.html', context=data)
