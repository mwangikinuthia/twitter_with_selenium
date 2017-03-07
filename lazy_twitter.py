"""
Program that uses the chrome webdriver to get historic tweet data
of a mention from agiven dates. in yyyy-m-d

"""
from selenium import webdriver
import time
from bs4 import BeautifulSoup
import calendar
import csv
import datetime
import re
import os
from functools import lru_cache
import argparse
import requests
import traceback


TODAY_YEAR = time.strftime('%Y')
COUNTER = 1
TWEET_SAVER=''
current_path = os.path.dirname(os.path.realpath(__file__))
cp = os.path.dirname(os.path.realpath(__file__))+'/chromedriver'
p = datetime.datetime.now()


def init_dr():
    """
    initiates selenium webdriver
    :return:
    """
    driver = webdriver.Chrome(cp)
    return driver


def return_soup(mention_, web_driver, dates,writer):
    """
    :return a parsable page source of visited web page
    :param town
    :param country
    :param mention_
    :param web_driver:
    :param dates:
    :return:
    """

    if type(mention_) is list:
        p='https://twitter.com/search?l=&q={}%20{}%20since%3A2017-02-13%20until%3A2017-02-18&src=typd'\
            .format(mention_[0],mention_[1],dates[0],dates[1])
    else:
        p = 'http://twitter.com/search?l=en&q={}%20since%3A{}%20until%3A{}&src=typd'.format(mention_, dates[0],
                                                                                               dates[1])

    web_driver.get(p)
    print('Visiting history from {} to {}'.format(dates[0],dates[1]))
    print('^^Getting page source from {}^^'.format(p))

    try:
        web_driver.find_element_by_class_name("stream-end")
    except Exception:
        return
    # z = web_driver.execute_script("arguments[0].scrollIntoView(true);", p)

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
    parse(soup,writer)
    return

def parse(soup, writer):
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
                if 'data-is-reply-to' in user_details_div:
                    ld['isReply'] = user_details_div['data-is-reply-to']

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
            p = get_values(ld['user_id'])

            rows = [ld["user_id"], ld['user_screen_name'], ld['user_name'], ld['tweet_text'], ld['retweets'],
                    ld['favorites'], p['followers'], p['following'], p['isVerified'], p['tweets'],
                    ld['perma_link'], tweet_id, ld['replies'], ld['mentions'],
                    ld['hashtags'], ld['links_in_tweet'], ld['isReply'], ld['date'], ld['time']]
            writer.writerow(rows)

            COUNTER += 1


    except Exception as e:
        print('**************Found Error {}'.format(e))
        print(traceback.format_exc())
        pass


def get_date_year(years_list):
    # Gets date values from a list of years.
    if (int(years_list[1]) - int(years_list[0])) > 1:
        o = int(years_list[1]) - int(years_list[0])
        p = years_list[0]
        years_list = []
        for i in range(0, o+1):
            print(i)
            years_list.append(int(p)+i)
    print(years_list)

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

        if int(year) <= int(TODAY_YEAR):
            p=dates_2(months)
            all_dates.append(p)
        else:
            raise ValueError('Enter a valid end Year')
    print(all_dates)
    return all_dates


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
    year = td[0]
    month = td[1]
    if month[0] == '0':
        month = month.replace('0','')
    day = td[2]
    if day[0] == '0':
        day.replace('0','')
    p = complete_dates.index(year+'-'+month+'-'+day)
    if p:
        complete_dates = complete_dates[:p]
    q = complete_dates.index(date)
    complete_dates = complete_dates[q:]
    doubles = []
    for i in range(len(complete_dates)):
        try:
            y = complete_dates [i:i+2]
            doubles.append(y)
            i +=1
        except IndexError:
            pass
    return doubles[:-1]


@lru_cache(200)
def get_values(userid):
    global TWEET_SAVER
    caller = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36'
    data_dict = {'followers': '', 'following': '', 'tweets': '', 'isVerified': 'No'}
    headers = {'User-Agent': caller,'X-Requested-With': 'XMLHttpRequest'}

    base_url = 'https://twitter.com/i/profiles/popup?user_id={}&wants_hovercard=true&_={}'.format(userid,TWEET_SAVER)
    print('>>Getting user stats of user {}'.format(TWEET_SAVER))
    p = requests.get(base_url, headers=headers)
    data = p.json()
    soup = BeautifulSoup(data['html'], 'lxml')
    stats = soup.find_all('a', class_='ProfileCardStats-statLink')
    f = str(stats[2]['title'])
    Following = f.split(' ')[0]
    fw = str(stats[1]['title'])
    Followers = fw.split(' ')[0]
    tw = str(stats[0]['title'])
    isVerified = soup.find('div', class_="ProfileNameTruncated-badges")
    data_dict['followers'] =  Following
    data_dict['following'] = Followers
    data_dict['tweets']=tw.replace('Tweets','')
    if isVerified is not None:
        data_dict['isVerified'] = 'Yes'
    return data_dict

if __name__ == '__main__':
    parser = argparse.ArgumentParser(prog="Tweet mention search")
    parser.add_argument('startDate', help='The date you want to begin search in YYYY-M-D')
    parser.add_argument('endDate',  help='The date you want to begin search in YYYY-M-D')
    parser.add_argument('-m','--mention',help="If you want to enter one screen name here eg @Brexit")
    parser.add_argument('-f','--file',nargs='?', help='enter the name of text file with screen names.REMEMBER the  path' )
    args = parser.parse_args()

    startYear = args.startDate
    endYear = args.endDate
    if args.mention:
        mention = args.mention.replace('@', '')
    screenFile = args.file

    years_one = startYear.split('-')[0]
    end_year = endYear.split('-')[0]
    date = startYear
    date_ = startYear
    TODAY_YEAR = endYear.split('-')[0]
    years = get_date_year([int(years_one),int(TODAY_YEAR)])
    driver = init_dr()
    sliding_dates = get_twins(years)
    if args.mention:
        with open(mention+'_all.csv', "a") as f:
            writer = csv.writer(f)
            writer.writerow(
                    ["user_id", 'user_screen_name', 'user_name', 'tweet_text', 'retweets', 'favorites', 'followers',
                     'following', 'isVerified', 'tweets', 'perma_link', 'tweet_id', 'replies', 'mentions',
                     'hashtags', 'links_in_tweet', 'isReply', 'date', 'time'])
            for pair in sliding_dates:
                return_soup(mention, driver,pair,writer)
    if args.file:
        with open(args.file,'r') as f:
            names = f.readlines()
            for screenname in names:
                screenname = screenname.replace('@', '')
                with open(screenname+'_all.csv', "a") as f:
                    writer = csv.writer(f)
                    writer.writerow(
                            ["user_id", 'user_screen_name', 'user_name', 'tweet_text', 'retweets', 'favorites',
                             'followers', 'following', 'isVerified', 'tweets', 'perma_link', 'tweet_id', 'replies',
                             'mentions',
                             'hashtags', 'links_in_tweet', 'isReply', 'date', 'time'])
                    for pair in sliding_dates:
                        return_soup(screenname, driver, pair, writer)

    driver.quit()
