import tweepy
import sys
import json
import locale
import datetime
# dotenv start
from dotenv import load_dotenv
import os
load_dotenv()
# dotenv end

# module_name, package_name, ClassName, method_name, ExceptionName,
# function_name, GLOBAL_CONSTANT_NAME, global_var_name, instance_var_name,
# function_parameter_name, local_var_name

locale.setlocale(locale.LC_ALL, "Turkish")

consumer_key = os.getenv('consumer_key')
consumer_secret = os.getenv('consumer_secret')
access_token = os.getenv('access_token')
access_token_secret = os.getenv('access_token_secret')

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
# Tweepy API, istek sınırına ulaştığında otomatik bekleme (uyku) yapar ve sona ermesinden sonra devam eder
api = tweepy.API(auth, wait_on_rate_limit=True,
                 wait_on_rate_limit_notify=True)
if not api:
    print("Bağlantıda sorun var")
    sys.exit(-1)

# Belirli bir ID'den sonraki sonuçlar gerekliyse, since_id'i bu ID'ye ayarlayın.
# varsayılan olarak alt sınır yoktur, API'nin izin verdiği kadar geriye gidin
sinceId = None
# Sonuçlar yalnızca belirli bir kimliğin altındaysa, max_id'i bu kimliğe ayarlayın.
# varsayılan olarak üst sınır yoksa, arama sorgusuyla eşleşen en son tweet ile başlayın.
maxId = 0

# toplam ne kadar tivit gelecek
maxTweets = 10
# apiden tek sorguda kaç tivit gelecek
tweetsPerQry = 5
tweetCount = 0
fName = 'tweets.txt'
screenName = os.getenv('screenName')


def datetime_to_srt(o):
    if isinstance(o, datetime.datetime):
        return o.replace(microsecond=0).__str__()


def get_new_tweets(screen_name, tweet_per_qry_count, tweet_mode='extended', since_id=None, max_id=0):
    return api.user_timeline(screen_name=screen_name, count=tweet_per_qry_count, tweet_mode=tweet_mode,
                             since_id=since_id, max_id=str(max_id - 1) if max_id > 0 else None)
    '''if maxId <= 0:
        if not sinceId:
            return api.user_timeline(screen_name=screen_name, count=tweet_per_qry_count, tweet_mode=tweet_mode)
        else:
            return api.user_timeline(screen_name=screen_name, count=tweet_per_qry_count,
                                     since_id=since_id, tweet_mode=tweet_mode)
    else:
        if not sinceId:
            return api.user_timeline(screen_name=screen_name, count=tweet_per_qry_count, tweet_mode=tweet_mode,
                                     max_id=str(max_id - 1))
        else:
            return api.user_timeline(screen_name=screen_name, count=tweet_per_qry_count, tweet_mode=tweet_mode,
                                     since_id=since_id, max_id=str(max_id - 1))'''


print("Downloading max {0} tweets".format(maxTweets))
with open(fName, 'w', encoding="utf-8") as f:
    while tweetCount < maxTweets:
        try:
            new_tweets = \
                get_new_tweets(screen_name=screenName, tweet_per_qry_count=tweetsPerQry, since_id=sinceId, max_id=maxId)
            if not new_tweets:
                print("No more tweets found")
                break
            for tweet in new_tweets:
                tweetJson = {"screen_name": tweet.user.screen_name, "name": tweet.user.name,
                             "user_id": tweet.user.id, "tweet_id": tweet.id, "full_text": tweet.full_text,
                             "created_at": datetime_to_srt(tweet.created_at),
                             "eklenme_tarihi": datetime_to_srt(datetime.datetime.utcnow())}
                f.write(
                    json.dumps(tweetJson, ensure_ascii=False, indent=4)
                )
            tweetCount += len(new_tweets)
            print("Downloaded {0} tweets".format(tweetCount))
            maxId = new_tweets[-1].id
        except tweepy.TweepError as e:
            # Just exit if any error
            print("some error : " + str(e))
            break

print("Downloaded {0} tweets, Saved to {1}".format(tweetCount, fName))
