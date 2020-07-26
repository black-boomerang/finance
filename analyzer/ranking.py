import os
import sys
from datetime import datetime

import pandas as pd
import requests
from bs4 import BeautifulSoup

from analyzer.cloud_manager import upload_to_cloud


def get_ranks_dict(order_filter, table_type, param):
    start_url = 'https://finviz.com/screener.ashx?v=1' + str(
        table_type) + '1ft=3&o={}&r='.format(order_filter)
    rangs = dict()
    params = dict()

    for i in range(1, 7531, 20):
        if i % 400 == 1:
            print(i * 100 // 7531, '%')

        url = start_url + str(i)
        head = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)         Chrome/83.0.4103.116 Safari/537.36'}
        page = requests.get(url, headers=head)

        soup = BeautifulSoup(page.text, 'lxml')
        tbl = soup.find('table', bgcolor='#d3d3d3')
        rows = tbl.findAll('tr', valign='top')
        for row in rows:
            tds = row.findAll('td')
            rangs[tds[1].text] = int(tds[0].text)
            params[tds[1].text] = float(tds[param].text.strip('%') + '0')

    return rangs, params


if __name__ == '__main__':
    if datetime.today().weekday() > 4:
        sys.exit()

    white_list = pd.read_excel(
        os.path.join('resources', 'white_list.xlsx'))
    tickers = white_list['Торговый код'].to_list()

    pe_rangs, pe = get_ranks_dict('pe', 1, 7)
    roe_rangs, roe = get_ranks_dict('-roe', 6, 5)

    ep_rang_series = pd.Series(pe_rangs, name='E/P rang')
    ep_series = (1 / pd.Series(pe, name='E/P (%)')) * 100
    roe_rang_series = pd.Series(roe_rangs, name='ROE rang')
    roe_series = pd.Series(roe, name='ROE (%)')

    rangs = pd.concat([ep_rang_series, ep_series, roe_rang_series, roe_series],
                      axis=1, sort=False)
    rangs['Summary rang'] = rangs['E/P rang'] + rangs['ROE rang']

    filename = 'ordered_rangs_' + datetime.today().strftime(
        '%Y_%m_%d') + '.xlsx'
    rangs.loc[rangs.index.intersection(tickers)].sort_values(
        'Summary rang').dropna().to_excel(filename)

    upload_to_cloud(filename)
    os.remove(filename)

    print('Ranking in done!')