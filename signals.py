#!/usr/bin/env python3

import math
import random
import yfinance as yf
import pandas as pd
from datetime import date, timedelta
import plotly.graph_objects as go
# from pandas_datareader import data as pdr
from pandas_datareader import data as pdr


def lambda_handler(events, context):
    # override yfinance with pandas – seems to be a common step
    yf.pdr_override()

    # Get stock data from Yahoo Finance – here, asking for about 10 years of Amazon
    today = date.today()
    decadeAgo = today - timedelta(days=3652)

    data = pdr.get_data_yahoo('CSCO', start=decadeAgo, end=today).reset_index()
    # Other symbols: CSCO – Cisco, NFLX – Netflix, INTC – Intel, TSLA - Tesla
    # print(data)

    # Add two columns to this to allow for Buy and Sell signals
    # fill with zero
    data['Buy'] = 0
    data['Sell'] = 0

    # data = data.set_index(data.DatetimeIndex(data['Date']))

    # Find the 4 different types of signals – uncomment print statements
    # if you want to look at the data these pick out in some another way
    for i in range(len(data)):
        # Hammer
        realbody = math.fabs(data.Open[i] - data.Close[i])
        bodyprojection = 0.1 * math.fabs(data.Close[i] - data.Open[i])

        if data.High[i] >= data.Close[i] and data.High[i] - bodyprojection <= data.Close[i] and data.Close[i] > data.Open[
            i] and data.Open[i] > data.Low[i] and data.Open[i] - data.Low[i] > realbody:
            data.at[data.index[i], 'Buy'] = 1
            # print("H", data.Open[i], data.High[i], data.Low[i], data.Close[i])

        # Inverted Hammer
        if data.High[i] > data.Close[i] and data.High[i] - data.Close[i] > realbody and data.Close[i] > data.Open[i] and \
                data.Open[i] >= data.Low[i] and data.Open[i] <= data.Low[i] + bodyprojection:
            data.at[data.index[i], 'Buy'] = 1
            # print("I", data.Open[i], data.High[i], data.Low[i], data.Close[i])

        # Hanging Man
        if data.High[i] >= data.Open[i] and data.High[i] - bodyprojection <= data.Open[i] and data.Open[i] > data.Close[
            i] and data.Close[i] > data.Low[i] and data.Close[i] - data.Low[i] > realbody:
            data.at[data.index[i], 'Sell'] = 1
            # print("M", data.Open[i], data.High[i], data.Low[i], data.Close[i])

        # Shooting Star
        if data.High[i] > data.Open[i] and data.High[i] - data.Open[i] > realbody and data.Open[i] > data.Close[i] and \
                data.Close[i] >= data.Low[i] and data.Close[i] <= data.Low[i] + bodyprojection:
            data.at[data.index[i], 'Sell'] = 1
            # print("S", data.Open[i], data.High[i], data.Low[i], data.Close[i])

    # Data now contains signals, so we can pick signals with a minimum amount
    # of historic data, and use shots for the amount of simulated values
    # to be generated based on the mean and standard deviation of the recent history

    minhistory = int(events['minhistory'])
    shots = int(events['shots'])
    for i in range(minhistory, len(data)):
        if data.Buy[i] == 1:  # if we’re interested in Buy signals
            mean = data.Close[i - minhistory:i].pct_change(1).mean()
            std = data.Close[i - minhistory:i].pct_change(1).std()
            # generate much larger random number series with same broad characteristics
            simulated = [random.gauss(mean, std) for x in range(shots)]
            # sort and pick 95% and 99%  - not distinguishing long/short here
            simulated.sort(reverse=True)
            var95 = simulated[int(len(simulated) * 0.95)]
            var99 = simulated[int(len(simulated) * 0.99)]

            # print(var95, var99)  # so you can see what is being produced

    print(data)
    figure = go.Figure(
        data=[
            go.Candlestick(
                x=data['Date'],
                open=data['Open'],
                low=data['Low'],
                high=data['High'],
                close=data['Close']
            )
        ]
    )
    figure.show()

# events = {
#   "minhistory": "100",
#   "shots": "1000000",
# }
