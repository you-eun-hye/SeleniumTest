import undetected_chromedriver as uc
from bs4 import BeautifulSoup as bs
import pickle
import time
import pymysql

if __name__ == '__main__':

    # mysql 연결
    conn = pymysql.connect(
        user="유저명",
        password="비밀번호",
        host="127.0.0.1",
        db="디비명",
        charset="utf8"
    )
    cursor = conn.cursor()

    # cookie 확인
    browser = uc.Chrome()
    browser.get('로그인 URL')

    cookies = pickle.load(open("cookies.pkl", "rb"))

    for cookie in cookies:
        cookie['domain'] = ".google.com"

        try:
            browser.add_cookie(cookie)
        except Exception as e:
            print(e)


    # cookie 정보로 자동로그인
    browser.get('로그인이 필요한 URL')
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
    payment_soup = soup.select('.U6fuTe') # 크롤링한 데이터가 있는 반복 구간 ex) <tr>

    # 크롤링
    for li in payment_soup:
        payment_price = li.find('div', class_='mshXob').get_text()
        if(li.find('a', class_='XqqpEd XX5fi')):
            payment_name = li.find('a', class_='XqqpEd XX5fi').get_text()
        else:
            payment_name = li.find('span', class_='XqqpEd').get_text()
        payment_date = li.find('div', class_='V8HwNc').get_text()

        # 디비에 저장
        sql = "INSERT INTO payment (name, date, price) VALUES (%s, %s, %s)"
        cursor.execute(sql, (payment_name, payment_date, payment_price))
        conn.commit()
    conn.close()