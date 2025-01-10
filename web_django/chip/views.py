import requests
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
from django.shortcuts import render
from meta_data.models import StockMetaData
from price.models import PriceData, InstitutionalInvestorData
from .util import create_dash
from dashboard_utils.common_functions import create_price_sequence

meta_data = StockMetaData.objects.all()
price_data = PriceData.objects.all()
institutional_data = InstitutionalInvestorData.objects.all()


# Create your views here.
def download(stock_code):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Referer": "https://concords.moneydj.com/",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
    }
    url1 = f"https://concords.moneydj.com/z/zc/zcj/zcj_{stock_code}.djhtm"
    url2 = f"https://concords.moneydj.com/z/zc/zcm/zcm_{stock_code}.djhtm"
    url3 = f"https://concords.moneydj.com/z/zc/zco/zco_{stock_code}.djhtm"
    res = requests.get(url1, headers=headers)
    soup = BeautifulSoup(res.text, "lxml")
    table = soup.select('table')[-1]
    date = table.find_all("div", "t11")[0].text
    data = table.find_all("td", class_=['t3n1', 't3t1', 't3r1'])
    data = np.array([cell.text for cell in data]).reshape(-1, 4)
    data = pd.DataFrame(data, columns=['term', 'amount', 'increment', 'ratio'])
    data['amount'] = data['amount'].apply(lambda x: x.replace(',', ''))
    data['increment'] = data['increment'].apply(lambda x: x.replace(',', ''))
    data['ratio'] = data['ratio'].apply(lambda x: x.replace('%', ''))
    data = data.replace('', '0.0')
    res = requests.get(url2, headers=headers)
    soup = BeautifulSoup(res.text, "lxml")
    total_amount = soup.select('table')[-1].find_all(
        'td', class_='t3n1')[0].text.replace(',', '')
    total_amount = int(total_amount)
    data = data.append(
        {
            'term':
            '其他',
            'amount':
            total_amount - data['amount'].astype(int).sum(),
            'ratio':
            (total_amount - data['amount'].astype(int).sum()) / total_amount,
        },
        ignore_index=True)
    # Fetch data from url3
    res = requests.get(url3, headers=headers)
    soup = BeautifulSoup(res.text, "lxml")
    table = soup.find("table", {"id": "oMainTable"})
    
    # Extract data for "買超" and "賣超"
    rows = table.find_all("tr")[3:]  # Skip header rows
    buy_sell_data = []
    for row in rows:
        cells = row.find_all("td", class_=["t4t1", "t3n1"])
        if len(cells) >= 10:
            buy_sell_data.append({
                "buy_broker": cells[0].text.strip(),
                "buy_in": cells[1].text.strip(),
                "buy_out": cells[2].text.strip(),
                "buy_net": cells[3].text.strip().replace(',', ''),
                "buy_ratio": cells[4].text.strip(),
                "sell_broker": cells[5].text.strip(),
                "sell_in": cells[6].text.strip(),
                "sell_out": cells[7].text.strip(),
                "sell_net": cells[8].text.strip().replace(',', ''),
                "sell_ratio": cells[9].text.strip(),
            })
    
    buy_sell_df = pd.DataFrame(buy_sell_data)
    return date, data, total_amount, buy_sell_df

def get_institutional(stock_code):
    institutional = institutional_data.filter(
        code=stock_code).order_by('-date')
    df = []
    columns = list(institutional[0].get_values().keys())
    for row in institutional:
        values = row.get_values()
        df.append([row.date] + [values[k] for k in values])
    df = pd.DataFrame(df, columns=['date'] + columns)
    df['foreign'] = df['foreign_buy'] - df['foreign_sell']
    df['invest'] = df['invest_buy'] - df['invest_sell']
    df['dealer'] = df['dealer_buy'] - df['dealer_sell']
    return df[['date', 'foreign', 'invest', 'dealer']]


def main(request, stock_id):
    info = meta_data.filter(code=stock_id)[0]
    same_trade = meta_data.filter(industry_type=info.industry_type)
    date, chip_df, total, buy_sell_df = download(stock_id)
    institution_df = get_institutional(stock_id)
    price = price_data.filter(code=stock_id).order_by('-date')
    price_df = create_price_sequence(price)
    data = {}
    data['stock_id'] = f"{stock_id} {info.name}"
    data['listed_date'] = info.listed_date
    data['industry_type'] = info.industry_type
    data['same_trade'] = same_trade
    data['stock_list'] = meta_data
    data['stock_info'] = info
    app = create_dash(chip_df, institution_df, price_df, buy_sell_df)
    print(date)
    print(chip_df)
    print(buy_sell_df)
    print(total)
    return render(request, 'chip_dashboard.html', context=data)
