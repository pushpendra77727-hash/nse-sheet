import gspread, json, os, time, requests, zipfile, io
from datetime import datetime, timedelta
import pandas as pd

creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
gc = gspread.service_account_from_dict(creds_dict)
ws = gc.open('NSE Institutional Buying Tracker').sheet1

symbols = ['RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS','SBIN','AXISBANK','ITC','LT','BAJFINANCE']

ws.clear()
ws.append_row(['Symbol','Close','Delivery %','Del Qty','Traded Qty','Change %','Signal','Date','Status'])

# Get last trading day
trade_date = datetime.now()
if trade_date.hour < 19: # Before 7 PM, use yesterday
    trade_date = trade_date - timedelta(days=1)
while trade_date.weekday() > 4: # Skip weekends
    trade_date = trade_date - timedelta(days=1)

date_str = trade_date.strftime("%d%m%Y")
date_display = trade_date.strftime("%d-%m-%Y")

# Download NSE bhavcopy zip
url = f"https://archives.nseindia.com/content/historical/EQUITIES/{trade_date.strftime('%Y')}/{trade_date.strftime('%b').upper()}/cm{date_str}bhav.csv.zip"
headers = {'User-Agent': 'Mozilla/5.0'}

try:
    r = requests.get(url, headers=headers, timeout=10)
    z = zipfile.ZipFile(io.BytesIO(r.content))
    df = pd.read_csv(z.open(z.namelist()[0]))
    df = df[df['SERIES'] == 'EQ']
    df['SYMBOL'] = df['SYMBOL'].str.strip()
    status = 'OK'
except Exception as e:
    ws.append_row(['ALL', '', '', '', '', '', '', date_display, f'Download Error: {str(e)[:50]}'])
    exit()

for sym in symbols:
    try:
        row = df[df['SYMBOL'] == sym].iloc[0]
        close = row['CLOSE']
        del_qty = row['DELIV_QTY']
        trd_qty = row['TOTTRDQTY']
        chg_pct = ((row['CLOSE'] - row['PREVCLOSE']) / row['PREVCLOSE']) * 100

        del_pct = round((del_qty / trd_qty) * 100, 2) if trd_qty > 0 else 0

        signal = ''
        if del_pct > 60 and chg_pct > 1:
            signal = 'Strong Accumulation'
        elif del_pct > 50 and chg_pct > 0:
            signal = 'BUY'
        elif del_pct < 30 and chg_pct < -1:
            signal = 'Distribution'

        ws.append_row([sym, close, del_pct, int(del_qty), int(trd_qty), round(chg_pct,2), signal, date_display, 'OK'])
    except:
        ws.append_row([sym, 'N/A', 'N/A', 'N/A', '', date_display, 'Not Traded'])

time.sleep(1)
print("Done")
