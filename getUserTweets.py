"""
Program that uses the chrome webdriver to get historic tweet data

"""
from time import strptime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
from bs4 import BeautifulSoup
import calendar
import csv
import datetime
import re
import os
import argparse
import traceback
import urllib


TODAY_YEAR = time.strftime('%Y')
COUNTER = 1
OUT_FILE = 'tweets.csv'
current_path = os.path.dirname(os.path.realpath(__file__))
cp = os.path.dirname(os.path.realpath(__file__))+'/chromedriver'
p = datetime.datetime.now()
startYear = ''
endYear = ''
p = 0

def get_first_tweet_date(user_screen,driver):
    print('[*]Loading stats for {}'.format(user_screen))
    global startYear
    global endYear
    stats = {'tweets':0,'followers':0, 'following':0,'location':''}
    url = 'https://twitter.com/{}'.format(user_screen)
    driver.get(url)
    try:
        elem = WebDriverWait(driver, 4).until(EC.presence_of_element_located((By.CLASS_NAME,'ProfileHeaderCard-joinDateText')))
    finally:
        html = driver.page_source

    soup = BeautifulSoup(html, 'lxml')
    stats = soup.find('ul',class_='ProfileNav-list')
    lis = stats.find_all('li',class_='ProfileNav-item')
    data = []
    for item in lis:
        try:
            df = item.find('a')['title']
            p = df
            y = p.split(' ')
            data.append(y[0])
        except Exception:
            pass
    stats['tweets'] = data[0]
    stats['following'] = data[1]
    stats['followers'] = data[2]
    try:
        location = soup.find('div',{'class':'ProfileHeaderCard-location'})
        stats['location'] = location.text
    except AttributeError:
        pass
    date = soup.select('#page-container > div.AppContainer > div > div > div.Grid-cell.u-size1of3.u-lg-size1of4 > div > div > div > div.ProfileHeaderCard > div.ProfileHeaderCard-joinDate > span.ProfileHeaderCard-joinDateText.js-tooltip.u-dir')
    p = date[0]['title']
    p = p.split()
    year = p[5]
    month = strptime('{}'.format(p[4]), '%b').tm_mon
    day = p[3]
    startYear = str(year) +'-'+str(month)+'-'+str(day)
    endYear = time.strftime("%Y-%m-%d")
    print(endYear)
    driver.quit()
    return stats

def init_dr():
    """
    initiates selenium webdriver
    :return:
    """
    driver = webdriver.Chrome(cp)
    return driver


def return_soup(mention_, web_driver, dates,writer,stats):
    """
    :return a parsable page source of visited web page
    :param town
    :param country
    :param mention_
    :param web_driver:
    :param dates:
    :return:
    """
    p = 'https://twitter.com/search?f=tweets&vertical=default&q=from%3A{}%20since%3A{}%20until%3A{}&src=typd'.format(mention_,dates[0],dates[1])
    web_driver.get(p)
    print('Visiting history from {} to {}'.format(dates[0],dates[1]))
    print('>>Getting page source from {}'.format(p))

    try:
        web_driver.find_element_by_class_name("stream-end")
    except Exception:
        print('Oops no tweets here again just accounts')
        return
    lenOfPage = web_driver.execute_script(
        "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
    match = False
    while match == False:
        lastCount = lenOfPage
        time.sleep(3)
        lenOfPage = web_driver.execute_script(
            "window.scrollTo(0, document.body.scrollHeight);var lenOfPage=document.body.scrollHeight;return lenOfPage;")
        if lastCount == lenOfPage:
            match = True


    html = web_driver.page_source
    soup = BeautifulSoup(html, 'lxml')
    parse(soup,writer,stats)
    return


def parse(soup, writer,stats):
    """
    Find values required tweets,screen names etc
    :param soup:
    :param writer
    :return:
    """
    global COUNTER
    global TWEET_SAVER
    try:
        tweet_list = soup.find_all('li', {'class':'js-stream-item'})
        for tweet in tweet_list:
            if 'data-item-id' not in tweet.attrs:
                print('[ No tweets here for this day]')
                continue
            ld ={
                'user_id':'',
                'user_screen_name':'',
                'user_name':'',
                'tweet_text':'',
                'retweets':0,
                'favorites':0,
                'perma_link':'',
                'tweet_id':'',
                'replies':0,
                'mentions':'',
                'hashtags':'',
                'links_in_tweet':'',
                'isReply':'',
                'date':'',
                'time':'',



            }
            # https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names=konstrukto
            print('>>>>>Tweet number {}'.format(COUNTER))
            # tweet id
            tweet_id = tweet['data-item-id']
            TWEET_SAVER = tweet_id

            user_details_div = tweet.find("div", class_="tweet")
            if user_details_div is not None:
                ld['user_id'] = user_details_div['data-user-id']
                ld['user_screen_name'] = user_details_div['data-screen-name']
                ld['user_name'] = user_details_div['data-name']
                ld['perma_link'] = 'https://twitter'+user_details_div['data-permalink-path']
                if 'data-mentions' in user_details_div:
                    ld['mentions'] = user_details_div['data-mentions']

            content = tweet.find('div', {'class':'content'})
            if content is not None:
                text_ = content.find('p')
                ld['tweet_text'] = text_.text
                try:
                    hts = content.find_all('a',{'class','twitter-hashtag'})
                    hash_tags = [i.text for i in hts]
                    ld['hashtags'] = ' '.join(hash_tags)
                except AttributeError:
                    pass


            links = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ld['tweet_text'])
            pics = re.findall('pic.twitter.com/(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:a - fA - F][0 - 9a - fA - F]))+', ld['tweet_text'])
            all_links = [' '.join(pics),' '.join(links)]
            ld['links_in_tweet'] = ' '.join(all_links)


            date_span = tweet.find("span", class_="_timestamp")

            if date_span is not None:
                created_at = float(date_span['data-time-ms'])
                time_ = datetime.datetime.fromtimestamp(
                created_at / 1000)
                fmt = "%d/%m/%Y"
                fmtt = "%H:%M:%S"
                ld['date'] = time_.strftime(fmt)
                ld['time'] = time_.strftime(fmtt)
                # retweet
            retweet_span = content.select(
                    "span.ProfileTweet-action--retweet > span.ProfileTweet-actionCount")
            if retweet_span is not None and len(retweet_span) > 0:
                ld['retweets'] = int(
                        retweet_span[0]['data-tweet-stat-count'])

                # favorites
            favorite_span = content.select(
                    "span.ProfileTweet-action--favorite > span.ProfileTweet-actionCount")
            if favorite_span is not None and len(retweet_span) > 0:
                ld['favorites'] = int(
                        favorite_span[0]['data-tweet-stat-count'])

            reply_span = content.select(
                    "span.ProfileTweet-action--reply > span.ProfileTweet-actionCount")
            if reply_span is not None and len(retweet_span) > 0:
                ld['replies'] = int(
                        favorite_span[0]['data-tweet-stat-count'])

            rows = ["'{}".format(ld["user_id"]), ld['user_screen_name'], ld['user_name'], ld['tweet_text'], ld['retweets'],
                        ld['favorites'], ld['perma_link'],"'{}".format(tweet_id), ld['replies'], ld['mentions'],
                        ld['hashtags'], ld['links_in_tweet'], ld['date'],ld['time'],
                    stats['location'],stats['tweets'] ,stats['following'] , stats['followers']]
            writer.writerow(rows)

            COUNTER += 1


    except Exception as e:
        print('**************Found Error {}'.format(e))
        print(traceback.format_exc())


# def get_followers(screanname):
#     url = 'https://cdn.syndication.twimg.com/widgets/followbutton/info.json?screen_names={}'.format(screanname)
#     response = urllib.request.urlopen(url).read().decode('utf8')
#     data = json.loads(response)
#     followers = data[0]
#     num = followers['followers_count']
#     return num


def get_date_year(years_list):
    # Gets date values from a list of years.
    global p
    if (int(years_list[1]) - int(years_list[0])) > 1:
        o = int(years_list[1]) - int(years_list[0])
        p = years_list[0]
        years_list = []
        for i in range(0, o+1):
            years_list.append(int(p)+i)
    all_dates = []
    months = [1,2,3,4,5,6,7,8,9,10,11,12]
    for year in years_list:
        def dates_2(months_values):
            date_l =[]
            for month in months_values:
                sample = calendar.monthcalendar(year,month)
                for i in sample:
                    for date in i:
                        if date != 0:
                            y = str(year) + '-' + str(month) + '-'+ str(date)
                            date_l.append(y)

            return date_l
        p = (int(TODAY_YEAR)-int(year))*12
        if int(year) <= int(TODAY_YEAR):
            p=dates_2(months)
            all_dates.append(p)
        else:
            raise ValueError('Enter a valid end Year')
    return all_dates

def get_set(seq):
    if len(seq) < 365:
        num = 3
    else:
        num = 30
    avg = len(seq) / float(num)
    out = []
    last = 0.0

    while last < len(seq):
        out.append(seq[int(last):int(last + avg)])
        last += avg-1
    if len(out[len(out)-1]) <=1:
        return out[:-1]
    return out


def get_twins(p):
    """
    Return a dates in pairs of [a,b],[b,c],[c,d]
    This is to allow to query the with since and until parameters in the twitter search.
    :param p:
    :return:
    """
    complete_dates = []
    for elem in p:
        complete_dates.extend(elem)

    td = str(endYear).split('-')
    fd = date.split('-')
    year = td[0]
    month = td[1]

    if month[0] == '0':
        month = month.replace('0','')

    day = td[2]
    if day[0] == '0':
        day=day.replace('0','')

    p = complete_dates.index(year+'-'+month+'-'+day)
  

    if p:
        complete_dates = complete_dates[:p]
    q = complete_dates.index(date)
    complete_dates = complete_dates[q:]
    dates_=get_set(complete_dates)
    if len(dates_[len(dates_)-1]) < 2:
        return date_[:-1]
    print(dates_)
    return dates_
 

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="Tweet mention search")
    parser.add_argument('-s','--screenname',help="If you want to enter one screen name here eg @Brexit")
    args = parser.parse_args()
    mention = args.screenname.replace('@', '')
    stats = get_first_tweet_date(mention, init_dr())
    years_one = startYear.split('-')[0]
    end_year = endYear.split('-')[0]
    date = startYear
    date_ = startYear
    TODAY_YEAR = endYear.split('-')[0]
    years = get_date_year([int(years_one),int(TODAY_YEAR)])
    sliding_dates = get_twins(years)
    driver = init_dr()
    with open(mention+'.csv', "a") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["userId", 'userScreenName', 'userName', 'tweetText', 'retweets', 'favorites', 'permaLink', 'tweetId', 'replies', 'mentions',
             'hashtags', 'linksInTweet', 'date', 'time', 'location', 'numOfTweets', 'following', 'followers'])
        for pair in sliding_dates:
            return_soup(mention, driver,[pair[0], pair[len(pair)-1]],writer,stats)
    driver.quit()
