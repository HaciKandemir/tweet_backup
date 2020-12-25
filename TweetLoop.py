import tweepy
import json
import os
from datetime import datetime
import time
import logging
import sys
from dotenv import load_dotenv

load_dotenv()


class CustomDataFormat(dict):
    def __init__(self, data):
        self["tweet_id"] = data["id"]
        self["tweet_id_str"] = data["id_str"]
        self["screen_name"] = data["user"]["screen_name"]
        self["name"] = data["user"]["name"]
        self["user_id"] = data["user"]["id"]
        self["user_id_str"] = data["user"]["id_str"]
        self["full_text"] = data["full_text"]
        self["created_at"] = str(datetime.strptime(data["created_at"], '%a %b %d %H:%M:%S +0000 %Y'))
        self["eklenme_tarihi"] = str(datetime.utcnow().replace(microsecond=0))
        # eğer bu varsa tweet bir yanıtttır. mesajı yazdığı kişinin id si
        if data["in_reply_to_user_id"] is not None:
            self["in_reply_to_user_id"] = data["in_reply_to_user_id"]
            self["in_reply_to_user_id_str"] = data["in_reply_to_user_id_str"]
            self["in_reply_to_screen_name"] = data["in_reply_to_screen_name"]
            self["in_reply_to_status_id"] = data["in_reply_to_status_id"]
            self["in_reply_to_status_id_str"] = data["in_reply_to_status_id_str"]
        # Tweeti yorumlu RT etmiş ise.
        # yorumu self["full_text"] de
        if data["is_quote_status"]:
            # RT edilen tweet metini
            self["quoted_status_full_text"] = data["quoted_status"]["full_text"]
            self["quoted_status_screen_name"] = data["quoted_status"]["in_reply_to_screen_name"]
            self["quoted_status_name"] = data["quoted_status"]["user"]["name"]
        # bu key sadece RT edilen tweetlerde oluyor
        if "retweeted_status" in data:
            # yorum katmadan sadece RT edilmiş tweetin metni
            self["retweeted_status_full_text"] = data["retweeted_status"]["full_text"]


logging.basicConfig(filename='log.txt', level=logging.INFO, format='%(asctime)s-%(levelname)s: %(message)s ',
                    datefmt='%Y-%m-%d %H:%M:%S')
logging.info('############# Program Başladı #############')

CONSUMER_KEY = os.getenv('consumer_key')
CONSUMER_SECRET = os.getenv('consumer_secret')
screen_name = os.getenv('screenName')

auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
api = tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True, parser=tweepy.parsers.JSONParser())

if not api:
    logging.critical('twitter bağlantısında sorun var')
    sys.exit(-1)

tweets_per_qry = 5
total_new_tweet_count = 0
new_tweet_count = 0
db_filename = "tweets.txt"
# üst üste belirli bir süre yeni tweet bulunmaz ise bekleme sürerisi arttırmada kontrol amaçlı kullanılıyor.
# (step,mükerrer)
step = 0
mükerrer = 0
sleep_second = 20

since_id = None
max_id = 0

customized_api_response = list()
local_tweets = list()

# dosyanın içinde veri varsa onu yeni veriler ile karşılaştırmak için listeye ekliyor
if os.stat(db_filename).st_size != 0:
    with open(db_filename, 'r', encoding="utf-8") as db_file:
        local_tweets = json.load(db_file)
        # dosyada en yeni veri en sonda olduğu için -1 ile ulaşıyorum
        since_id = local_tweets[-1]["tweet_id"]

while True:
    # api_res kendisi list içinde 0,1,2 indexlerinde dict şeklinde tweetleri saklıyor
    api_res = api.user_timeline(screen_name=screen_name, count=tweets_per_qry, tweet_mode="extended",
                                since_id=since_id, max_id=str(max_id - 1) if max_id > 0 else None)

    # api_res içerisindeki ihtiyacım olan verilerden daha minik bir dict oluşturup listeye ekliyorum
    for api_res_json in api_res:
        customized_api_response.append(CustomDataFormat(api_res_json))

    # daha önceden dosyaya yazdığım veriler ile api den gelen tweetleri karşılaştırıyorum.
    # yeni tweetler varsa onları da dosyadaki verilerden oluşan listeye ekliyorum
    for api_tweet in customized_api_response:
        if not api_tweet["tweet_id"] in [ids["tweet_id"] for ids in local_tweets]:
            local_tweets.append(dict(api_tweet))
            new_tweet_count += 1

    # bu döngüde yeni tweet var ise en son yazılan tweet en sona gelecek şekilde sıralıyorum.
    # daha sonra bunu listeyi dosyaya yazdırıyorum.
    if new_tweet_count > 0:
        local_tweets = sorted(local_tweets, key=lambda x: x["tweet_id"])
        # listenin içindeki dict leri yazdırıyor
        with open(db_filename, 'w', encoding="utf-8") as db_file:
            json.dump(local_tweets, db_file, indent=4, ensure_ascii=False)
        mükerrer = 0
    else:
        mükerrer += 1

    # 60 dk boyunca yeni tweet gelmediyse bundan sonra bekleme süresini 20 saniyeden 30dk ya çıkarıyor.
    # büyük sayılarla uğraşmamak için saniyeyi 60 a bölüp dk cinsinden kontrol ediyorum
    if mükerrer*(sleep_second/60) > 60:
        # 30 dk = 1800 saniye
        # 20 = 1200
        sleep_second = 1200
    else:
        sleep_second = 20

    total_new_tweet_count += new_tweet_count

    logging.info('%s-> bu döngüde eklenen: %s, toplam eklenen: %s', step, new_tweet_count, total_new_tweet_count)

    # api res de tweetler varsa bunu yapsın.
    if api_res and since_id:
        # gelen veride en eski veri en sonda olduğu için -1 ile ulaşıyorum
        max_id = api_res[-1]["id"]
    # eğer yok ise uygulama kapalı kaldığı süre boyunca atılan tweetlerin hepsi indirilmiştir.
    else:
        # bundan sonra sadece en son atılan tweetleri almak için atamlar yapılıyor.
        since_id = local_tweets[-1]["tweet_id"]
        max_id = 0
    step += 1
    new_tweet_count = 0
    customized_api_response.clear()
    time.sleep(sleep_second)
