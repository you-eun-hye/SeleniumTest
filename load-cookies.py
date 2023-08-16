from selenium.webdriver.support import expected_conditions as EC

import undetected_chromedriver as uc
from selenium import webdriver
from bs4 import BeautifulSoup as bs
import pickle
import time
import pymysql
from flask import Flask, request
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route("/")
def hello_world():
    return 'Hello World'

def saveCookies(email, password):
    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    browser = uc.Chrome(
        options=options,
    )
    browser.get('https://accounts.google.com/InteractiveLogin/identifier?continue=https%3A%2F%2Fplay.google.com%2Fweb%2Fstore%2Faccount%2Forderhistory%3Fhl%3Dko&followup=https%3A%2F%2Fplay.google.com%2Fweb%2Fstore%2Faccount%2Forderhistory%3Fhl%3Dko&hl=ko&osid=1&passive=1209600&ifkv=AXo7B7UCFiK2ivtbA7mO0r9f7Q1TG_QVb8RgSFY2HEjJpE-QZ5uEXnVEMfu7BVLAzECt3UI3n_Bo&flowName=GlifWebSignIn&flowEntry=ServiceLogin')

    # ID와 PASSWORD 자동 입력
    browser.find_element(By.ID, 'identifierId').send_keys(email)

    browser.find_element(
        By.CSS_SELECTOR, '#identifierNext > div > button > span').click()

    password_selector = "#password > div.aCsJod.oJeWuf > div > div.Xb9hP > input"

    WebDriverWait(browser, 10).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, password_selector)))

    browser.find_element(
        By.CSS_SELECTOR, password_selector).send_keys(password)

    browser.find_element(
        By.CSS_SELECTOR, '#passwordNext > div > button > span').click()

    time.sleep(10)

    # 쿠키 접근 후 저장
    cookies = browser.get_cookies()
    pickle.dump(cookies, open("cookies.pkl", "wb"))

@app.route("/test", methods=["GET"])
def load_cookie():

    # mysql 연결
    conn = pymysql.connect(
        user="",
        password="",
        host="127.0.0.1",
        db="GooGoo",
        charset="utf8"
    )
    cursor = conn.cursor()

    # user 정보 가져옴
    userId = request.args.get("id");
    userEmail = request.args.get("email");
    userPassword = request.args.get("password");

    options = webdriver.ChromeOptions()
    options.add_argument('headless')

    browser = uc.Chrome(
        options=options,
    )
    browser.get('https://accounts.google.com/InteractiveLogin/identifier?continue=https%3A%2F%2Fplay.google.com%2Fweb%2Fstore%2Faccount%2Forderhistory%3Fhl%3Dko&followup=https%3A%2F%2Fplay.google.com%2Fweb%2Fstore%2Faccount%2Forderhistory%3Fhl%3Dko&hl=ko&osid=1&passive=1209600&ifkv=AXo7B7UCFiK2ivtbA7mO0r9f7Q1TG_QVb8RgSFY2HEjJpE-QZ5uEXnVEMfu7BVLAzECt3UI3n_Bo&flowName=GlifWebSignIn&flowEntry=ServiceLogin')

    # cookie 확인
    try:
        cookies = pickle.load(open("cookies.pkl", "rb"))
    except:
        saveCookies(userEmail, userPassword)
        cookies = pickle.load(open("cookies.pkl", "rb"))

    for cookie in cookies:
        cookie['domain'] = ".google.com"

        try:
            browser.add_cookie(cookie)
        except Exception as e:
            print(e)


    # cookie 정보로 자동로그인
    browser.get('https://play.google.com/store/account/orderhistory?hl=ko-KR')
    browser.implicitly_wait(60)

    # 무한 스크롤
    prev_height = browser.execute_script('return document.body.scrollHeight')
    while True:
        browser.execute_script('window.scrollTo(0, document.body.scrollHeight)')
        browser.implicitly_wait(10)
        current_height = browser.execute_script('return document.body.scrollHeight')
        if prev_height == current_height:
            break
        prev_height = current_height
    time.sleep(3)

    # html 가져옴
    soup = bs(browser.page_source, 'html.parser')
    payment_soup = soup.select('.U6fuTe')

    # 크롤링
    for li in payment_soup:
        # 이미지
        payment_img = li.find('img', class_='T75of p36pgb').get("src")

        # 가격
        payment_price = li.find('div', class_='mshXob').get_text()
        if(payment_price == '₩0' or payment_price == 'US$0.00'):
            payment_price = 0;
        else:
            priceList = list(payment_price)
            payment_price = ''
            for piece in priceList:
                if(piece == '₩' or piece == 'U' or piece == 'S'or piece == '$' or piece == ',' or piece == '.'):
                    continue
                else:
                    payment_price += piece

        # 유료 어플일 경우 제품명
        if(li.find('a', class_='XqqpEd XX5fi')):
            payment_name = li.find('a', class_='XqqpEd XX5fi').get_text()
        # 무료어플의 유료서비스일 경우 제품명
        else:
            payment_name = li.find('span', class_='XqqpEd').get_text()

        # 결제일
        payment_date = li.find('div', class_='V8HwNc').get_text()
        date_list = payment_date.split('.')
        payment_year = date_list[0]
        payment_month = date_list[1]
        payment_date = date_list[2]
        print("SUCCESS Crawalling")

        # DB 저장
        # SELECT 결과가 0이라면 첫 사용자니까 전부 INSERT
        # SELECT 결과가 0이 아니라면 새로운 값만 INSERT
        checkSQL = "SELECT COUNT(*) FROM payment"
        if(cursor.execute(checkSQL) == 0):
            sql = "INSERT INTO payment (img_src, name, price, year, month, date, user_id) VALUES (%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (payment_img, payment_name, payment_price, payment_year, payment_month, payment_date, userId))
            conn.commit()
        else:
            sql = "INSERT INTO payment (img_src, name, price, year, month, date, user_id) VALUES(%s, %s, %s, %s, %s, %s, %s)"
            cursor.execute(sql, (payment_img, payment_name, payment_price, payment_year, payment_month, payment_date, userId))
            conn.commit()
    conn.close()
    return "SUCCESS"

app.run(debug=True, host="127.0.0.1", port=5000)