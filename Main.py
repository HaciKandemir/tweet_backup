import tweepy
import sys
import json
import datetime
import time
import logging
# dotenv start
from dotenv import load_dotenv
import os
load_dotenv()
# dotenv end

# module_name, package_name, ClassName, method_name, ExceptionName,
# function_name, GLOBAL_CONSTANT_NAME, global_var_name, instance_var_name,
# function_parameter_name, local_var_name

logging.basicConfig(filename='log.txt', level=logging.INFO)

consumer_key = os.getenv('consumer_key')
consumer_secret = os.getenv('consumer_secret')
access_token = os.getenv('access_token')
access_token_secret = os.getenv('access_token_secret')

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
# Tweepy API, istek sınırına ulaştığında otomatik bekleme (uyku) yapar ve sona ermesinden sonra devam eder
api = tweepy.API(auth, wait_on_rate_limit=True,
                 wait_on_rate_limit_notify=True)  # tweepy.API(auth, parser=tweepy.parsers.JSONParser())
if not api:
    print("Bağlantıda sorun var")
    sys.exit(-1)

# toplam ne kadar tivit gelecek
maxTweets = 10
# apiden tek sorguda kaç tivit gelecek
tweetsPerQry = 5
allTweetCount = 0
fName = 'tweets.txt'
screenName = os.getenv('screenName')


def datetime_to_srt(o):
    if isinstance(o, datetime.datetime):
        return str(o.replace(microsecond=0))


# twitterden tweetleri alıp geri döndürüyor
def get_timeline_tweets(screen_name, tweet_per_qry_count, tweet_mode='extended', since_id=None, max_id=None):
    return api.user_timeline(screen_name=screen_name, count=tweet_per_qry_count, tweet_mode=tweet_mode,
                             since_id=since_id or None, max_id=str(max_id-1) if max_id > 0 else None)


class TweetFormat(object):
    def __init__(self, data):
        self.__dict__ = data

    # 'if in' için
    def __contains__(self, key):
        return key in self.__dict__

    def __setitem__(self, key, value):
        self.__dict__[key] = value

    # 'for in' için
    def __iter__(self):
        return iter(self.__dict__.items())

    def to_json(self):
        return json.dumps(self, default=lambda o: o.__dict__, indent=4, ensure_ascii=False)


# dosyadaki json formatındaki verileri okuyup döndürüyor
def read_json_file(file_name=fName):
    try:
        with open(file_name, 'r', encoding='utf-8') as f:
            convert = json.load(f)
            return TweetFormat(convert)
    except ValueError:
        return {}


def convert_tweet_format(ob):
    deger = json.loads(json.dumps(ob))
    return TweetFormat(deger)


def write_json_file(json_data, file_name=fName):
    with open(file_name, 'w', encoding="utf-8") as f:
        f.write(
            json_data
        )


# gelen geriyi dosyada kaydedilecek şekilde kişiselleştirip json olarak geri döndürüyor
def tweet_json_format(json_tweet):
    return {"screen_name": json_tweet.user.screen_name, "name": json_tweet.user.name,
            "user_id": json_tweet.user.id, "tweet_id": json_tweet.id, "full_text": json_tweet.full_text,
            "created_at": datetime_to_srt(json_tweet.created_at),
            "eklenme_tarihi": datetime_to_srt(datetime.datetime.utcnow())}


tweetDb = {}
apiReqTweets = {}
newTweets = {}
loadFile = True
dongu = 0
# Belirli bir ID'den sonraki sonuçlar gerekliyse, since_id'i bu ID'ye ayarlayın.
# varsayılan olarak alt sınır yoktur, API'nin izin verdiği kadar geriye gidin
sinceId = None
# Sonuçlar yalnızca belirli bir kimliğin altındaysa, max_id'i bu kimliğe ayarlayın.
# varsayılan olarak üst sınır yoksa, arama sorgusuyla eşleşen en son tweet ile başlayın.
maxId = 0
logging.info("###############################Program başladı####################################")
while True:
    print("{0}. döngü".format(dongu))
    if loadFile:
        loadFile = False
        tweetDb = read_json_file()
    tweetCount = 0

    print("Downloading max {0} new tweets".format(maxTweets))
    while tweetCount < maxTweets:
        try:
            apiReqTweets = get_timeline_tweets(
                screen_name=screenName, tweet_per_qry_count=tweetsPerQry, since_id=sinceId, max_id=maxId
            )
            if not apiReqTweets:
                print("No more tweets found")
                break
            for apiTweet in apiReqTweets:
                if not apiTweet.id_str in tweetDb:
                    newTweets[apiTweet.id] = tweet_json_format(apiTweet)
            tweetCount += len(apiReqTweets)
            allTweetCount += len(newTweets)
            print("Download {0} tweet, Found {1} new tweets".format(tweetCount, len(newTweets)))
            #maxId = apiReqTweets[-1].id
            sinceId = apiReqTweets[0].id
        except tweepy.TweepError as e:
            logging.error(str(e))
            # Just exit if any error
            print("some error : " + str(e))
            break
    for tweet in newTweets:
        tweetDb.__setitem__(tweet, newTweets[tweet])

    if not len(newTweets) < 1:
        write_json_file(tweetDb.to_json())
        loadFile = True
        print(
            "Found {0} new tweets and all found {1} tweets, Saved to {2}".format(len(newTweets), allTweetCount, fName))
    logging.info("{0}-) <----{1}----> yeni tweet eklendi. Toplam = {2} ({3})".format(dongu, len(newTweets), allTweetCount, datetime.datetime.utcnow().replace(microsecond=0)))
    newTweets.clear()
    dongu = dongu+1
    time.sleep(20)
