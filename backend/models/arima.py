import yfinance as yf
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA

def predict_arima(ticker, days=5):
    stock = yf.Ticker(ticker)
    data = stock.history(period="1y")['Close']

    model = ARIMA(data, order=(5,1,0))  # ARIMA(5,1,0) is a standard configuration
    model_fit = model.fit()

    forecast = model_fit.forecast(steps=days)
    return forecast.tolist()