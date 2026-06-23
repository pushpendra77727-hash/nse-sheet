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
    ltp = del_pct = p_chg = oi_chg = 'N/A'
    signal = status = ''

    try:
        # Get equity data
        q = nse_quote(sym)
        ltp = q.get('lastPrice', 'N/A')
        del_pct = q.get('deliveryToTradedQuantity', 'N/A')
        p_chg = q.get('pChange', 'N/A')

        # Get F&O data - skip if not available
        try:
            fo = nse_quote_derivative(sym)
            if fo and 'data' in fo and len(fo['data']) > 0:
                oi_chg = fo['data'][0].get('pchangeinOpenInterest', 'N/A')
            else:
                oi_chg = 'No F&O'
        except:
            oi_chg = 'No F&O'

        # Signal logic only if we have numbers
        if isinstance(del_pct, (int, float)) and isinstance(oi_chg, (int, float)) and isinstance(p_chg, (int, float)):
            if del_pct > 50 and oi_chg > 5 and p_chg > 0:
                signal = 'STRONG BUY'
            elif oi_chg > 5 and p_chg < 0:
                signal = 'Short Buildup'
            elif del_pct > 50 and oi_chg < -5 and p_chg > 0:
                signal = 'Short Covering'

        status = 'OK'

    except Exception as e:
        status = f'Error: {str(e)[:80]}'

    ws.append_row([sym, ltp, del_pct, oi_chg, p_chg, signal, str(datetime.now())[:16], status])
    time.sleep(2) # Wait 2 sec between stocks so NSE doesn't block

print("Done")
