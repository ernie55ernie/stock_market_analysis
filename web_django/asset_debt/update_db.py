import argparse
import requests
import numpy as np
import pandas as pd
from .models import *

# https://mops.twse.com.tw/mops/web/t163sb05
url = 'https://mops.twse.com.tw/mops/web/ajax_t163sb05'

company_columns = {
    'nonstandard':
    ['公司代號', '資產總額', '資產總計', '負債總額', '負債總計', '權益總額', '權益總計', '股本', '每股參考淨值']
}
company_columns['standard'] = company_columns['nonstandard'] + [
    '流動資產', '非流動資產', '流動負債', '非流動負債'
]

company_columns_renames = {
    'nonstandard': ['資產總額', '負債總額', '權益總額', '股本', '每股參考淨值']
}
company_columns_renames['standard'] = company_columns_renames[
    'nonstandard'] + ['流動資產', '非流動資產', '流動負債', '非流動負債']

company_type = {1: 'bank', 3: 'standard', 4: 'holdings', 5: 'insurance'}

# 上櫃
# 流動資產	非流動資產	資產合計	流動負債	非流動負債	負債合計	股本	資本公積	保留盈餘（或累積虧損）	其他權益	庫藏股票	歸屬於母公司業主權益合計	共同控制下前手權益	合併前非屬共同控制股權	權益合計	待註銷股本股數（單位：股）	預收股款（權益項下）之約當發行股數（單位：股）	母公司暨子公司持有之母公司庫藏股股數（單位：股）	每股參考淨值
# 流動資產	非流動資產	資產總額	流動負債	非流動負債	負債總額	股本	資本公積	保留盈餘	其他權益	庫藏股票	歸屬於母公司業主之權益合計	共同控制下前手權益	合併前非屬共同控制股權	非控制權益	權益總額	待註銷股本股數（單位：股）	預收股款（權益項下）之約當發行股數（單位：股）	母公司暨子公司所持有之母公司庫藏股股數（單位：股）	每股參考淨值
# 流動資產	非流動資產	資產總額	流動負債	非流動負債	負債總額	股本	資本公積	保留盈餘	其他權益	庫藏股票	歸屬於母公司業主之權益合計	共同控制下前手權益	非控制權益	權益總額	待註銷股本股數（單位：股）	預收股款（權益項下）之約當發行股數（單位：股）	母公司暨子公司所持有之母公司庫藏股股數（單位：股）	每股參考淨值

# TODO: valid after 102, 1, before use https://mops.twse.com.tw/mops/web/ajax_t51sb12
def crawl(year, season):
    dfs = {}
    form = {
        'encodeURIComponent': 1,
        'step': 1,
        'firstin': 1,
        'off': 1,
        'TYPEK': 'sii',
        'year': year,
        'season': season,
    }
    r = requests.post(url, form)
    r.encoding = 'utf8'
    df = pd.read_html(r.text, header=None)
    for token in company_type:
        print('   parsing', company_type[token])
        df[token].columns = [col.replace(' ', '') for col in df[token].columns]
        if company_type[token] == 'standard':
            candidate_columns = company_columns['standard']
            renamed_columns = company_columns_renames['standard']
        else:
            candidate_columns = company_columns['nonstandard']
            renamed_columns = company_columns_renames['nonstandard']
        selected_columns = [
            col for col in candidate_columns if col in df[token].columns
        ]
        one_df = df[token][selected_columns]
        one_df.columns = ['code'] + renamed_columns
        dfs[token] = one_df

    return dfs


def create_row(row, company_type, season):
    code = int(row['code'])
    if company_type == 'standard':
        try:
            noncurrent_debt = float(row['非流動負債'])
        except ValueError:
            noncurrent_debt = 0
        one_row = StandardAssetDebtData(code=code,
                                        season=season,
                                        current_assets=row['流動資產'],
                                        noncurrent_assets=row['非流動資產'],
                                        total_assets=row['資產總額'],
                                        current_debt=row['流動負債'],
                                        noncurrent_debt=noncurrent_debt,
                                        total_debt=row['負債總額'],
                                        total_equity=row['權益總額'],
                                        share_capital=row['股本'],
                                        PBR=row['每股參考淨值'])

    else:
        one_row = NonStandardAssetDebtData(code=code,
                                           season=season,
                                           total_assets=row['資產總額'],
                                           total_debt=row['負債總額'],
                                           total_equity=row['權益總額'],
                                           share_capital=row['股本'],
                                           PBR=row['每股參考淨值'])
    one_row.save()


def delete_data(year, season):
    NonStandardAssetDebtData.objects.filter(season=f"{year}_{season}").delete()
    StandardAssetDebtData.objects.filter(season=f"{year}_{season}").delete()


def main(action, year, season):
    if action == 'add_data':
        print('crawling....')
        dfs = crawl(year, season)
        for token in dfs:
            for i in range(len(dfs[token])):
                create_row(dfs[token].iloc[i], company_type[token],
                           f"{year}_{season}")
            print(company_type[token], f"{year} {season}", 'done')
    elif action == 'delete_data':
        delete_data(year, season)


if __name__ == "__name__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--action', type=str, default='add_data')
    parser.add_argument('--year', type=str, required=True)
    parser.add_argument('--season', type=str, required=True)
    args = parser.parse_args()
    main(args.action, args.year, args.season)
