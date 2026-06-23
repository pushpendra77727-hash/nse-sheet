import gspread, json, os, time
from nsepython import *
from datetime import datetime

creds_dict = json.loads(os.environ['GOOGLE_CREDS'])
gc = gspread.service_account_from_dict(creds_dict)
ws = gc.open('NSE Institutional Buying Tracker').sheet1

symbols = ['RELIANCE','HDFCBANK','ICICIBANK','INFY','TCS','SBIN','AXISBANK','ITC','LT','BAJFINANCE']

ws.clear()
ws.append_row(['Symbol','LTP','Delivery %','OI Change %','Price Change %','Signal','Updated At','Status'])

for sym in symbols:
    try:
        print(f"Fetching {sym}...")
        q = nse_quote(sym)
        time.sleep(1) # Wait 1 sec between calls

        fo = nse_quote_derivative(sym)
        time.sleep(1)

        ltp = q.get('lastPrice', 'N/A')
        del_pct = q.get('deliveryToTradedQuantity', 'N/A')
        p_chg = q.get('pChange', 'N/A')
        oi_chg = fo['data'][0].get('pchangeinOpenInterest', 'N/A')

        signal = ''
        if isinstance(del_pct, (int, float)) and isinstance(oi_chg, (int, float)) and isinstance(p_chg, (int, float)):
            if del_pct > 50 and oi_chg > 5 and p_chg > 0:
                signal = 'STRONG BUY'
            elif oi_chg > 5 and p_chg < 0:
                signal = 'Short Buildup'

        ws.append_row([sym, ltp, del_pct, oi_chg, p_chg, signal, str(datetime.now())[:16], 'OK'])

    except Exception as e:
        error_msg = str(e)[:100]
        print(f"Error for {sym}: {error_msg}")
        ws.append_row([sym, '', '', '', '', '', str(datetime.now())[:16], f'Error: {error_msg}'])
        time.sleep(2)

print("Done")
