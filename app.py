import os
import sys
from flask import Flask, render_template, request, redirect, url_for
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import NoSuchElementException, TimeoutException, NoSuchWindowException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta
import pandas as pd
import urllib.parse

app = Flask(__name__)

def get_chromedriver_path():
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, 'chromedriver.exe')
    return 'chromedriver.exe'

chrome_driver_path = get_chromedriver_path()

def login_to_twitter(driver, username_input, password_input, certification_input, max_retries=3):
    retries = 0
    while retries < max_retries:
        try:
            driver.get('https://twitter.com/login')
            WebDriverWait(driver, 30).until(EC.presence_of_element_located((By.NAME, 'text')))

            time.sleep(1)
            username = driver.find_element(By.NAME, 'text')
            username.send_keys(username_input)

            next_button = driver.find_element(By.XPATH, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/button[2]')
            next_button.click()

            time.sleep(1)

            try:
                auth_input = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, 'text')))
                auth_input.clear()
                auth_input.send_keys(certification_input)

                auth_next_button = driver.find_element(By.XPATH, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/button')
                auth_next_button.click()

            except (NoSuchElementException, TimeoutException):
                pass

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.NAME, 'password')))
            password = driver.find_element(By.NAME, 'password')
            password.send_keys(password_input)

            login_button = driver.find_element(By.XPATH, '//*[@id="layers"]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]/div/div/button')
            login_button.click()

            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//div[@data-testid="primaryColumn"]')))
            return True
        except NoSuchElementException as e:
            print(f"Login attempt {retries + 1} failed: {e}")
            retries += 1
            time.sleep(2)
    return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    username_input = request.form['username']
    password_input = request.form['password']
    certification_input = request.form['certification']
    excel_filename = request.form['excel_filename']
    keywords = request.form.getlist('keyword')
    keyword_types = request.form.getlist('keyword_type')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    min_likes = request.form.get('min_likes')
    min_retweets = request.form.get('min_retweets')
    min_replies = request.form.get('min_replies')

    service = Service(chrome_driver_path)
    chrome_options = Options()
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        logged_in = login_to_twitter(driver, username_input, password_input, certification_input)
        if not logged_in:
            return render_template('finish.html', message="Failed to log in to Twitter after multiple attempts.")

        start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date() if start_date else None
        end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date() if end_date else None
        tweet_data = []

        search_query = []

        for keyword, keyword_type in zip(keywords, keyword_types):
            if keyword:
                if keyword_type == "mention":
                    search_query.append(f'@{keyword}')
                elif keyword_type == "hashtag":
                    search_query.append(f'#{keyword}')
                elif keyword_type == "from":
                    search_query.append(f'from:{keyword}')
                elif keyword_type == "retweets_of":
                    search_query.append(f'retweets_of:{keyword}')
                else:
                    search_query.append(keyword)

        if start_date_obj:
            search_query.append(f'since:{start_date}')

        if end_date_obj:
            search_query.append(f'until:{end_date}')

        if min_likes:
            search_query.append(f'min_faves:{min_likes}')

        if min_retweets:
            search_query.append(f'min_retweets:{min_retweets}')

        if min_replies:
            search_query.append(f'min_replies:{min_replies}')

        search_query_str = " ".join(search_query)
        encoded_search_query_str = urllib.parse.quote(search_query_str)

        search_url = f'https://twitter.com/search?q={encoded_search_query_str}&src=typed_query&f=live'
        print(search_url)  # 디버깅을 위해 URL을 출력
        driver.get(search_url)

        try:
            WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '//div[@data-testid="cellInnerDiv"]')))
        except TimeoutException:
            return render_template('finish.html', message=f"No tweets found for the given criteria.")

        collected_tweets = set()
        scroll_pause_time = 7
        last_height = driver.execute_script("return document.body.scrollHeight")
        new_tweets_loaded = True

        while new_tweets_loaded:
            tweets = driver.find_elements(By.XPATH, '//div[@data-testid="cellInnerDiv"]')

            for tweet in tweets:
                try:
                    username_element = tweet.find_element(By.XPATH, './/div[@data-testid="User-Name"]/div[2]/div/div[1]/a/div/span')
                    username = username_element.text

                    try:
                        content_element = tweet.find_element(By.XPATH, './/div[@data-testid="tweetText"]')
                    except NoSuchElementException:
                        content_element = tweet.find_element(By.XPATH, './/div[@lang]')
                    content = content_element.text

                    date_element = tweet.find_element(By.XPATH, './/time')
                    date_str = date_element.get_attribute('datetime')
                    tweet_date = datetime.fromisoformat(date_str[:-1]).date()

                    tweet_link = tweet.find_element(By.XPATH, './/a[contains(@href, "/status/")]').get_attribute('href')

                    if content not in collected_tweets:
                        collected_tweets.add(content)

                        try:
                            retweets_button = tweet.find_element(By.XPATH, './/button[@data-testid="retweet"]')
                            retweets_count = retweets_button.text if retweets_button else "0"
                        except NoSuchElementException:
                            retweets_count = "0"

                        try:
                            likes_button = tweet.find_element(By.XPATH, './/button[@data-testid="like"]')
                            likes_count = likes_button.text if likes_button else "0"
                        except NoSuchElementException:
                            likes_count = "0"

                        try:
                            replies_button = tweet.find_element(By.XPATH, './/button[@data-testid="reply"]')
                            replies_count = replies_button.text if replies_button else "0"
                        except NoSuchElementException:
                            replies_count = "0"

                        if not start_date_obj or start_date_obj <= tweet_date <= end_date_obj:
                            tweet_info = {
                                "UserName": username,
                                "Date": date_str,
                                "Content": content,
                                "Link": tweet_link,
                                "Retweets": int(retweets_count.replace(",", "") or 0),
                                "Likes": int(likes_count.replace(",", "") or 0),
                                "Replies": int(replies_count.replace(",", "") or 0)
                            }
                            tweet_data.append(tweet_info)

                except NoSuchElementException as e:
                    print(f"NoSuchElementException: {e}")
                except Exception as e:
                    print(f"Error: {e}")
                    continue

            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")

            if new_height == last_height:
                new_tweets_loaded = False
            else:
                last_height = new_height

        if tweet_data:
            df = pd.DataFrame(tweet_data)
            df.to_excel(f"{excel_filename}.xlsx", index=False)
            return render_template('finish.html', message="Excel file has been saved.")
        else:
            return render_template('finish.html', message="No tweets found. Excel file has not been saved.")

    except NoSuchWindowException:
        return redirect(url_for('index'))
    finally:
        try:
            driver.quit()
        except NoSuchWindowException:
            pass

if __name__ == '__main__':
    app.run(debug=True)
