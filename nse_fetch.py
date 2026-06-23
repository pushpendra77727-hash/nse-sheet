import gspread, json, os, time
from nsepython import *
from datetime import datetime, timedelta
import pandas as pd

creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
gc = gspread.service_account_from_dict(creds_dict)
ws = gc.open('NSE Institutional Buying Tracker').sheet1

symbols = ['RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS','SBIN','AXISBANK','ITC','LT','BAJFINANCE']

ws.clear()
ws.append_row(['Symbol','Close Price','Delivery %','Del Qty','Traded Qty','Change %','Signal','Date','Status'])

# Get last trading day automatically
today = datetime.now()
if today.hour < 18:  # If before 6 PM, use yesterday
    trade_date = today - timedelta(days=1)
else:
    trade_date = today

# Skip weekends - go to Friday
while trade_date.weekday() > 4:
    trade_date = trade_date - timedelta(days=1)

date_str = trade_date.strftime("%d-%m-%Y")
print(f"Fetching EOD data for {date_str}")

for sym in symbols:
    close = del_pct = del_qty = trd_qty = chg_pct = 'N/A'
    signal = status = ''
    
    try:
        # Use equity_history - this works 24x7
        df = equity_history(sym, series="EQ", start_date=date_str, end_date=date_str)
        
        if df is not None and not df.empty:
            row = df.iloc[-1]
            close = float(row.get('CH_CLOSING_PRICE', 0))
            del_qty = int(row.get('COP_DELIV_QTY', 0))
            trd_qty = int(row.get('CH_TOT_TRADED_QTY', 0))
            chg_pct = float(row.get('CH_PCT_CHANGE', 0))
            
            # Calculate delivery %
            if trd_qty > 0:
                del_pct = round((del_qty / trd_qty) * 100, 2)
            
            # Signal for EOD analysis
            if isinstance(del_pct, (int, float)) and del_pct > 60 and chg_pct > 1:
                signal = 'Institutional Accumulation'
            elif isinstance(del_pct, (int, float)) and del_pct > 50 and chg_pct > 0:
                signal = 'BUY'
            elif isinstance(del_pct, (int, float)) and del_pct < 30 and chg_pct < -1:
                signal = 'Distribution'
                
            status = 'OK'
        else:
            status = 'No Data for Date'
            
    except Exception as e:
        status = f'Error: {str(e)[:50]}'

    ws.append_row([sym, close, del_pct, del_qty, trd_qty, chg_pct, signal, date_str, status])
    time.sleep(2)

print("Done")
