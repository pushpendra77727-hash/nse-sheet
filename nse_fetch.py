import gspread, json, os, time
from nsepython import *
from datetime import datetime, timedelta
import pandas as pd

creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
gc = gspread.service_account_from_dict(creds_dict)
ws = gc.open('NSE Institutional Buying Tracker').sheet1

symbols = ['RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS','SBIN','AXISBANK','ITC','LT','BAJFINANCE']

ws.clear()
ws.append_row(['Symbol','Close','Delivery %','Delivery Qty','Traded Qty','OI','OI Change %','Price Change %','Signal','Date','Status'])

# Get today's date or last trading day
today = datetime.now()
if today.weekday() > 4:  # Sat=5, Sun=6
    days_to_subtract = today.weekday() - 4  # Last Friday
    trade_date = today - timedelta(days=days_to_subtract)
else:
    trade_date = today

date_str = trade_date.strftime("%d-%m-%Y")
print(f"Fetching data for {date_str}")

for sym in symbols:
    close = del_pct = del_qty = trd_qty = oi = oi_chg = p_chg = 'N/A'
    signal = status = ''

    try:
        # 1. Get EOD bhavcopy data - works after market close
        df = equity_history(sym, "EQ", date_str, date_str)
        if not df.empty:
            row = df.iloc[-1]
            close = row.get('CH_CLOSING_PRICE', 'N/A')
            del_qty = row.get('COP_DELIV_QTY', 'N/A')
            trd_qty = row.get('CH_TOT_TRADED_QTY', 'N/A')
            p_chg = row.get('CH_PCT_CHANGE', 'N/A')
            
            # Calculate delivery %
            if isinstance(del_qty, (int, float)) and isinstance(trd_qty, (int, float)) and trd_qty > 0:
                del_pct = round((del_qty / trd_qty) * 100, 2)
        
        # 2. Get F&O EOD data if available
        try:
            fo_df = derivative_history(sym, "OPTSTK", date_str, date_str)
            if not fo_df.empty:
                fo_row = fo_df.iloc[-1]
                oi = fo_row.get('FH_OPEN_INT', 'N/A')
                oi_chg = fo_row.get('FH_PCT_CHNG_IN_OI', 'N/A')
            else:
                oi = oi_chg = 'No F&O'
        except:
            oi = oi_chg = 'No F&O'

        # 3. Signal logic for EOD analysis
        try:
            if all(isinstance(x, (int, float)) for x in [del_pct, oi_chg, p_chg]):
                if del_pct > 50 and oi_chg > 5 and p_chg > 0:
                    signal = 'STRONG BUY'
                elif del_pct > 50 and oi_chg < -5 and p_chg > 0:
                    signal = 'Short Covering'
                elif oi_chg > 5 and p_chg < 0:
                    signal = 'Short Buildup'
                elif del_pct > 50 and p_chg > 1:
                    signal = 'Institutional Accumulation'
        except:
            pass

        status = 'OK'

    except Exception as e:
        status = f'Error: {str(e)[:60]}'

    ws.append_row([sym, close, del_pct, del_qty, trd_qty, oi, oi_chg, p_chg, signal, date_str, status])
    time.sleep(2) # NSE blocks if too fast

print("Done")
