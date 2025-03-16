from fastapi import FastAPI, Query, HTTPException, Request, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
import ccxt
import pandas as pd
import os
from datetime import datetime

app = FastAPI()

# Template setup
templates = Jinja2Templates(directory="templates")

# Static files setup
app.mount("/static", StaticFiles(directory="static"), name="static")

DATA_FOLDER = "/data"
os.makedirs(DATA_FOLDER, exist_ok=True)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/fetch", response_class=HTMLResponse)
async def fetch_data(
    request: Request,
    symbol: str = Form(...),
    timeframe: str = Form(...),
    start_date: str = Form(...),
    end_date: str = Form(...)
):
    exchange = ccxt.binance({'enableRateLimit': True})

    try:
        since = exchange.parse8601(f"{start_date}T00:00:00Z")
        end_timestamp = exchange.parse8601(f"{end_date}T23:59:59Z")
    except:
        raise HTTPException(status_code=400, detail="Invalid date format.")

    ohlcv_data = []

    while since < end_timestamp:
        data = exchange.fetch_ohlcv(symbol, timeframe, since, limit=1000)
        if not data:
            break
        ohlcv_data += data
        since = data[-1][0] + exchange.parse_timeframe(timeframe)*1000

    if not ohlcv_data:
        raise HTTPException(status_code=404, detail="No data found.")

    df = pd.DataFrame(ohlcv_data, columns=['Time', 'Open', 'High', 'Low', 'Close', 'Volume'])
    df['Time'] = pd.to_datetime(df['Time'], unit='ms')

    file_name = f"{symbol.replace('/', '-')}_{timeframe}_{start_date}_{end_date}.csv"
    file_path = os.path.join(DATA_FOLDER, file_name)
    df.to_csv(file_path, index=False)

    return templates.TemplateResponse("download.html", {
        "request": request,
        "file_name": file_name
    })

@app.get("/download/{file_name}")
async def download(file_name: str):
    file_path = os.path.join(DATA_FOLDER, file_name)
    return FileResponse(file_path, filename=file_name)
