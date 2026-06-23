import gspread, json, os, time
from datetime import datetime, timedelta
import requests
import pandas as pd

creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
gc = gspread.service_account_from_dict(creds_dict)
ws = gc.open('NSE Institutional Buying Tracker').sheet1

symbols = ['RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS','SBIN','AXISBANK','ITC','LT','BAJFINANCE']

ws.clear()
ws.append_row(['Symbol','Close','Delivery %','Change %','Signal','Date','Status'])

# Get last trading day
date = datetime.now()
if date.hour < 18:
    date = date - timedelta(days=1)
while date.weekday() > 4:
    date = date - timedelta(days=1)

date_str = date.strftime("%d%b%Y").upper() # 23JUN2026

# NSE Bhavcopy URL - direct download, no API
url = f"https://archives.nseindia.com/content/historical/EQUITIES/{date.year}/{date.strftime('%b').upper()}/cm{date_str}bhav.csv.zip"

try:
    df = pd.read_csv(url, compression='zip')
    df = df[df['SERIES'] == 'EQ']
    status = 'Bhavcopy OK'
except Exception as e:
    status = f'Download Error: {str(e)[:40]}'
    df = pd.DataFrame()

for sym in symbols:
    close = del_pct = chg_pct = 'N/A'
    signal = ''

    try:
        if not df.empty:
            row = df[df['SYMBOL'] == sym]
            if not row.empty:
                r = row.iloc[0]
                close = r['CLOSE']
                del_qty = r['DELIV_QTY']
                trd_qty = r['TTL_TRD_QNTY']
                chg_pct = ((r['CLOSE'] - r['PREVCLOSE']) / r['PREVCLOSE'] * 100) if r['PREVCLOSE'] > 0 else 0

                if trd_qty > 0:
                    del_pct = round((del_qty / trd_qty) * 100, 2)

                if isinstance(del_pct, (int, float)):
                    if del_pct > 60 and chg_pct > 1:
                        signal = 'Strong Accumulation'
                    elif del_pct > 50:
                        signal = 'Buy'
    except:
        pass

    ws.append_row([sym, close, del_pct, round(chg_pct, 2) if isinstance(chg_pct, (int, float)) else chg_pct, signal, date_str, status if close == 'N/A' else 'OK'])
    time.sleep(1)

print("Done")
