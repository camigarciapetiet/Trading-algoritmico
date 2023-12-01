from __future__ import (absolute_import, division, print_function,unicode_literals)
import datetime 
import os.path
import sys
import backtrader as bt

class SMAStrat(bt.Strategy):
    params = (('maperiod', 15),('printlog', False),)

    def log(self, txt, dt=None, doprint=False): #imprime por pantalla
        #if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close #precio de cierre de hoy

        ##inicializo las ordenes pendientes
        self.order = None
        self.buyprice = None
        self.buycomm = None

        #simple moving average 
        self.sma = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod)


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - no se hace nada
            return

        if order.status in [order.Completed]: #chequeamos si se completo una orden
            if order.isbuy():
                self.log( #compra
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % #costo = precio con comision
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm), doprint=False)
                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  #venta
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % #costo = precio con comision
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm))

            self.bar_executed = len(self) #longitud de vela o periodo

        elif order.status in [order.Canceled, order.Margin, order.Rejected]: #no se efectuo la orden
            self.log('Order Canceled/Margin/Rejected')

        #sin ordenes pendientes
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm))

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])

        if self.order: #chequeamos que no tengamos ninguna orden pendiente
            return

        if not self.position: #no estamos en mercado - en que orden estas en el book
            if self.dataclose[0] > self.sma[0]: #significa que el precio es mayor al promedio
                self.log('BUY CREATE, %.2f' % self.dataclose[0])

                self.order = self.buy() #llevar registro de la orden para que no se cree otra

        else: #estamos en mercado - primero en el book

            if self.dataclose[0] < self.sma[0] : #significa que el precio es menor al promedio
                self.log('SELL CREATE, %.2f' % self.dataclose[0])

                self.order = self.sell() #llevar registro de la orden para que no se cree otra

    def stop(self):
        self.log('(MA Period %2d) Ending Value %.2f' % (self.params.maperiod, self.broker.getvalue()), doprint=True)

class CrossMethodStrat(bt.Strategy):
    params = (('maperiod1', 50),('maperiod2', 200),('printlog', False),)

    def log(self, txt, dt=None, doprint=False): #imprime por pantalla
        #if self.params.printlog or doprint:
            dt = dt or self.datas[0].datetime.date(0)
            print('%s, %s' % (dt.isoformat(), txt))

    def __init__(self):
        self.dataclose = self.datas[0].close #precio de cierre de hoy

        ##inicializo las ordenes pendientes
        self.order = None
        self.buyprice = None
        self.buycomm = None

        #simple moving average 
        self.sma1 = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod1)
        self.sma2 = bt.indicators.SimpleMovingAverage(self.datas[0], period=self.params.maperiod2)


    def notify_order(self, order):
        if order.status in [order.Submitted, order.Accepted]:
            # Buy/Sell order submitted/accepted to/by broker - no se hace nada
            return

        if order.status in [order.Completed]: #chequeamos si se completo una orden
            if order.isbuy():
                self.log( #compra
                    'BUY EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % #costo = precio con comision
                    (order.executed.price,
                     order.executed.value,
                     order.executed.comm), doprint=False)

                self.buyprice = order.executed.price
                self.buycomm = order.executed.comm
            else:  #venta
                self.log('SELL EXECUTED, Price: %.2f, Cost: %.2f, Comm %.2f' % #costo = precio con comision
                         (order.executed.price,
                          order.executed.value,
                          order.executed.comm), doprint=False)

            self.bar_executed = len(self) #longitud de vela o periodo

        elif order.status in [order.Canceled, order.Margin, order.Rejected]: #no se efectuo la orden
            self.log('Order Canceled/Margin/Rejected')

        #sin ordenes pendientes
        self.order = None

    def notify_trade(self, trade):
        if not trade.isclosed:
            return

        self.log('OPERATION PROFIT, GROSS %.2f, NET %.2f' %
                 (trade.pnl, trade.pnlcomm), doprint=False)

    def next(self):
        self.log('Close, %.2f' % self.dataclose[0])

        if self.order: #chequeamos que no tengamos ninguna orden pendiente
            return

        if not self.position: #no estamos en mercado - en que orden estas en el book
            if self.sma1[0] > self.sma2[0]: #corto plazo cruza hacia arriba la de largo plazo -> alcista
                self.log('BUY CREATE, %.2f' % self.dataclose[0], doprint=False)

                self.order = self.buy() #llevar registro de la orden para que no se cree otra

        else: #estamos en mercado - primero en el book

            if self.sma1[0] < self.sma2[0]: #corto plazo cruza hacia abajo la de largo plazo -> bajista
                self.log('SELL CREATE, %.2f' % self.dataclose[0], doprint=False)

                self.order = self.sell() #llevar registro de la orden para que no se cree otra

    def stop(self):
        self.log('(MA Period 1 %2d MA Period 2 %2d) Ending Value %.2f' % (self.params.maperiod1, self.params.maperiod2, self.broker.getvalue()), doprint=True)

if __name__ == '__main__':

    cerebro = bt.Cerebro()

    strats1 = cerebro.addstrategy(SMAStrat,maperiod=20) #estrategia 1
    strats2 = cerebro.optstrategy(SMAStrat,maperiod=range(15, 31)) #estrategia 2
    strats3 = cerebro.addstrategy(CrossMethodStrat, maperiod1 = 20, maperiod2 = 200) #estrategia3

    modpath = os.path.dirname(os.path.abspath(sys.argv[0]))
    datapath = os.path.join(modpath, 'orcl-1995-2014.txt')

    data = bt.feeds.YahooFinanceCSVData(
        dataname=datapath,
        fromdate=datetime.datetime(2000, 1, 1),
        todate=datetime.datetime(2000, 12, 31),
        reverse=False)

    cerebro.adddata(data)

    cerebro.broker.setcash(100000.0) #presupuesto

    cerebro.addsizer(bt.sizers.FixedSize, stake=10) #que porcentaje del total se asigna a cada operacion

    cerebro.broker.setcommission(commission=0.001) #comision del broker
  
    cerebro.run(maxcpus=1) #un solo nucleo de CPU para la ejecucion

   