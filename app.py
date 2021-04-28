import threading
from binance_f.model import OrderSide, OrderType
from flask import Flask, render_template, request, jsonify
import datetime
import binance_f
from tinydb import Query, TinyDB
import os

app = Flask(__name__)
isLogedIn = False
lastCode = ''
pathPrefix = "" # Working Dir path
dbMain = TinyDB(pathPrefix + "usersData.json")
queryMain = Query()
select = "D"


def Reverse(lst):
    return [ele for ele in reversed(lst)]


def getApis():
    return [dbMain.all()[0]["api"], dbMain.all()[0]["secAPI"]]


@app.route("/checkFile", methods=["GET"])
def checkfilechange():
    if request.method == 'GET':
        return jsonify({"isChange": str(dbMain.all()[0]["isChange"])})


@app.route("/changeKey", methods=["POST"])
def changeKey():
    global isLogedIn
    if isLogedIn:
        dbMain.update({"token": str(request.form.get("tokenKey"))})
        return "<script>alert('CHANGED !');window.location='/'</script>"
    else:
        return "<script>window.location='/'</script>"


@app.route("/changePass", methods=["POST"])
def changePass():
    global isLogedIn
    if isLogedIn:
        newPass = request.form.get("newPass")
        repPass = request.form.get("renewPass")
        if newPass != repPass:
            return "<script>alert('Password Dont Match !');window.location='/changepassword'</script>"
        dbMain.update({"pass": str(newPass)})

        return "<script>alert('PASSWORD CHANGED !');window.location='/'</script>"
    else:
        return "<script>window.location='/'</script>"


@app.route("/changepassword")
def CP():
    global isLogedIn
    if isLogedIn:
        return render_template("changepassword.html")
    else:
        return "<script>window.location='/'</script>"


@app.route("/changeAPIS")
def CAPI():
    global isLogedIn
    if isLogedIn:
        return render_template("changeAPI.html")
    else:
        return "<script>window.location='/'</script>"


@app.route("/changeptoken")
def CT():
    global isLogedIn
    if isLogedIn:
        return render_template("changeToken.html")
    else:
        return "<script>window.location='/'</script>"


@app.route("/changeAPI", methods=["POST"])
def changeAPI():
    global isLogedIn
    if isLogedIn:
        dbMain.update({"api": str(request.form.get("api")), "secAPI": str(request.form.get("secAPI"))})
        return "<script>alert('API Keys Changed !');window.location='/'</script>"
    else:
        return "<script>window.location='/'</script>"


@app.route("/runCode", methods=['POST'])
def runCode():
    code = request.form.get("code")
    global lastCode
    lastCode = code
    try:
        exec(code)
    except:
        return "<script>alert('SOME ERROR !');window.location='/'</script>"
    return "<script>alert('EXECUTED !');window.location='/'</script>"


@app.route("/changeLev")
def CL():
    global isLogedIn
    if isLogedIn:
        return render_template("changeLeverage.html")
    else:
        return "<script>window.location='/'</script>"


@app.route("/changeLev", methods=["POST"])
def changeLeverage():
    apis = getApis()
    try:
        binance_f.RequestClient(api_key=apis[0], secret_key=apis[0]).change_initial_leverage(
            str(request.form.get("symbolLev")), int(request.form.get("leverage")))
    except Exception as e:
        return "<script>alert('" + str(e) + "');window.location='/'</script>"

    return "<script>alert('Changed !');window.location='/'</script>"


def closeOrder(dictonary):
    side = OrderSide.INVALID
    if dictonary["SIGNAL"] == "CLOSE_LONG":
        side = OrderSide.SELL

    elif dictonary["SIGNAL"] == "CLOSE_SHORT":
        side = OrderSide.BUY

    q = float(round(float(dictonary["QTY"]), 6))
    apis = getApis()
    binance = binance_f.RequestClient(api_key=apis[0], secret_key=apis[1])

    for i in binance.get_position():
        j: binance_f.model.position.Position = i
        if j.positionAmt != 0.0:
            if j.symbol == dictonary["SYMBOL"]:
                if j.positionAmt < 0:
                    openedSide = OrderSide.SELL
                else:
                    openedSide = OrderSide.BUY
                if side != openedSide:
                    order: binance_f.model.order.Order = binance.post_order(symbol=dictonary["SYMBOL"],
                                                                            ordertype=OrderType.MARKET,
                                                                            quantity=q,
                                                                            positionSide=binance_f.model.PositionSide.BOTH,
                                                                            side=side)
                    price = order.price
                    threading.Thread(target=updateClosePosition, args=[side, price, dictonary]).start()
                    dbMain.update({"isChange": "t"})


def updateClosePosition(side, price, dictonary):
    time.sleep(1)
    apis = getApis()
    binance = binance_f.RequestClient(api_key=apis[0], secret_key=apis[1])

    dbHistory = TinyDB(pathPrefix + "history.json")

    try:
        if side == OrderSide.SELL:
            pl = float(dbHistory.search(queryMain.symbol == dictonary["SYMBOL"])[0]["price"]) - float(price)
        elif side == OrderSide.BUY:
            pl = float(price) - float(dbHistory.search(queryMain.symbol == dictonary["SYMBOL"])[0]["price"])
        pass
    except:
        pass
    i = binance.get_account_trades(symbol=dictonary["SYMBOL"])
    Reverse(i)
    orderId = float(dbHistory.search(queryMain.symbol == dictonary["SYMBOL"] and queryMain.pl == "-")[0]["id"])
    for j in range(1, len(i)):
        k: binance_f.model.mytrade.MyTrade = i[j]
        if k.orderId == orderId and k.side != side and str(dictonary["QTY"]) == str(k.qty):
            pl = i[j + 1].realizedPnl
            break

    plPer = (pl / float(binance.get_account_information().totalWalletBalance)) * 100

    dbHistory.update({
        "timeC": str(datetime.datetime.now()),
        "typeC": dictonary["SIGNAL"],
        "priceC": binance.get_symbol_price_ticker(dictonary["SYMBOL"])[0].price,
        "pl": pl,
        "plPer": plPer,
        "accBal": binance.get_account_information().totalWalletBalance
    }, (queryMain.symbol == dictonary["SYMBOL"] and queryMain.pl == "-"))
    dbMain.update({"isChange": "t"})


def openOrder(dictonary):
    apis = getApis()
    try:
        side = OrderSide.INVALID
        if dictonary["SIGNAL"] == "LONG":
            side = OrderSide.BUY
        elif dictonary["SIGNAL"] == "SHORT":
            side = OrderSide.SELL

        q = float(round(float(dictonary["QTY"]), 4))
        binance = binance_f.RequestClient(api_key=apis[0], secret_key=apis[1])
        order: binance_f.model.order.Order = binance.post_order(symbol=dictonary["SYMBOL"], ordertype=OrderType.MARKET,
                                                                quantity=q,
                                                                positionSide=binance_f.model.PositionSide.BOTH,
                                                                side=side)

        orderID = order.orderId
        status = order.status
        origQty = order.origQty
        price = binance.get_symbol_price_ticker(dictonary["SYMBOL"])[0].price

        dbHistory = TinyDB(pathPrefix + "history.json")
        dbHistory.insert({
            "timeO": str(datetime.datetime.now()),
            "timeC": "0",
            "typeO": dictonary["SIGNAL"],
            "typeC": "0",
            "priceO": str(price),
            "priceC": "0",
            "pl": "-",
            "plPer": "-",
            "symbol": dictonary["SYMBOL"],
            "qty": dictonary["QTY"],
            "accBal": binance.get_account_information().totalWalletBalance,
            "id": str(orderID)
        })
        dbMain.update({"isChange": "t"})
    except Exception as e:
        print(e)
    dbMain.update({"isChange": "t"})


def runTask(dictonary):
    if dictonary["EXCHANGE"] == "BINANCE":
        if dictonary["SIGNAL"] == "LONG":
            openOrder(dictonary)
        elif dictonary["SIGNAL"] == "SHORT":
            openOrder(dictonary)
        elif dictonary["SIGNAL"] == "CLOSE_LONG":
            closeOrder(dictonary)
        elif dictonary["SIGNAL"] == "CLOSE_SHORT":
            closeOrder(dictonary)


@app.route("/select", methods=["POST"])
def selector():
    selected = request.form.get("selector")
    global select
    if selected == "day":
        select = "D"
    elif selected == "week":
        select = "W"
    else:
        select = "A"
    return "<script>window.location='/'</script>"


@app.route("/loginN", methods=['POST'])
def login():
    global isLogedIn
    uName = request.form.get("username")
    password = request.form.get("password")

    if isLogedIn:
        return "<script>window.location = '/'</script>"
    else:
        if uName == str(dbMain.all()[0]["userName"]) and password == str(
                dbMain.all()[0]["pass"]):
            isLogedIn = True
            return "<script>window.location = '/'</script>"
        else:
            return "<script>alert('Invalid Candinate Failed !');window.location='/'</script>"


@app.route("/logout")
def logout():
    global isLogedIn
    isLogedIn = False
    return "<script>window.location = '/'</script>"


@app.route('/')
def dashboard():
    try:
        global select
        if isLogedIn:
            if select == "D":
                data = TinyDB(pathPrefix + "history.json").all()

                date = datetime.datetime.strptime(str(datetime.datetime.now()).split(".")[0], '%Y-%m-%d %H:%M:%S').day
                selected = list()
                for i in data:
                    if datetime.datetime.strptime(str(i["timeO"]).split(".")[0], '%Y-%m-%d %H:%M:%S').day == date:
                        selected.append(i)
            elif select == "W":
                data = TinyDB(pathPrefix + "history.json").all()
                date = datetime.datetime.strptime(str(datetime.datetime.now()).split(".")[0], '%Y-%m-%d %H:%M:%S').day
                selected = list()
                for i in data:
                    if int(datetime.datetime.strptime(str(i["timeO"]).split(".")[0], '%Y-%m-%d %H:%M:%S').day) > int(
                            int(date) - 7):
                        selected.append(i)
            else:
                selected = TinyDB(pathPrefix + "history.json").all()
            sendLst = list()
            totalPlain = 0
            sn = 1

            # l.append(float(round(float(i["price"]), 6)))
            # l.append(i["status"])
            # l.append(float(round(float(i["pl"]), 4)))
            # l.append(str(float(round(float(i["plPer"]), 4))) + "%")

            for i in selected:
                li = list()
                li.append(str(sn))  # 0
                if i["timeO"] != "0":  # 1
                    li.append(i["timeO"].split(".")[0])
                else:
                    li.append(None)

                if i["timeC"] != "0":  # 2
                    li.append(i["timeC"].split(".")[0])
                else:
                    li.append(None)

                if i["typeO"] != "0":  # 3
                    li.append(i["typeO"])
                else:
                    li.append(None)

                if i["typeC"] != "0":  # 4
                    li.append(i["typeC"])
                else:
                    li.append(None)

                if i["priceO"] != "0":  # 5
                    li.append(float(round(float(i["priceO"]), 2)))
                else:
                    li.append(None)

                if i["priceC"] != "0":  # 6
                    li.append(float(round(float(i["priceC"]), 2)))
                else:
                    li.append(None)
                if i["pl"] != "-":
                    li.append(float(round(float(i["pl"]), 2)))
                    li.append(str(float(round(float(i["plPer"]), 2))) + "%")
                else:
                    li.append(None)
                    li.append(None)
                li.append(i["symbol"])
                li.append(i["qty"])  # 12

                li.append(str(float(round(float(i["accBal"]), 2))) + "USD")
                if i["pl"] != "-":
                    totalPlain += float(i["pl"])
                    # if float(i["pl"]) < 0:
                    #    l.append("style=color:red;")
                    # else:
                    #    l.append("style=color:green;")

                sendLst.append(li)
                sn += 1
            try:
                total_per = (totalPlain / float(binance_f.RequestClient(api_key=getApis()[0], secret_key=getApis()[
                    1]).get_account_information().totalWalletBalance)) * 100
            except Exception as e:
                total_per = "0"
                open("er.txt", 'w').write(str(e) + str(e.args) + " 2st")

            total_per = float(round(float(total_per), 2))
            totalPlain = float(round(float(totalPlain), 2))
            if totalPlain < 0:
                total_plain_color = "style=color:red;"
            else:
                total_plain_color = "style=color:green;"
            if total_per < 0:
                total_percentage_color = "style=color:red;"
            else:
                total_percentage_color = "style=color:green;"
            try:
                dbMain.update({"isChange": "f"})
            except Exception as e:
                open("er.txt", 'w').write(str(e) + str(e.args) + " 3rd")
            try:
                apis = getApis()
            except Exception as e:
                accBalance = 0
                open("er.txt", 'w').write(str(e) + str(e.args) + " 5rd")

            try:
                accBalance = binance_f.RequestClient(api_key=apis[0],
                                                     secret_key=apis[1]).get_account_information().totalWalletBalance
            except Exception as e:
                accBalance = 0
                open("er.txt", 'w').write(str(e) + str(e.args) + " 4rd")

            return render_template("dashboard.html", wholeData=sendLst, total_percentage=str(total_per),
                                   total_plain=str(totalPlain),
                                   total_plain_color=total_plain_color, total_percentage_color=total_percentage_color,
                                   account_balance=accBalance)

        else:
            return render_template("login.html", lastCode=lastCode)
    except Exception as e:
        return "" + str(e)
        open("er.txt", 'w').write(str(e) + str(e.args))


@app.route('/webhook', methods=['POST'])
def webhook():
    dictonary = dict()
    for i in request.data.decode().split("\n"):
        dictonary[i.split("=")[0].strip()] = i.split("=")[1].strip()
    for j in dictonary:
        dictonary[j] = dictonary[j].strip()
    if str(dbMain.all()[0]["token"]) == str(dictonary["TOKEN"]):
        runTask(dictonary)
    else:
        return '200'
    return '200'


import time


def printAllTradesCurrent():
    time.sleep(1)
    binance = binance_f.RequestClient(api_key=getApis()[0], secret_key=getApis()[1])

    for i in binance.get_position():
        j: binance_f.model.position.Position = i
        print(j.positionAmt, j.symbol)

    pass


if __name__ == "__main__":
    app.run(debug=True)
