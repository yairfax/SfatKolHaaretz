import requests
import argparse
from time import sleep
from langdetect import detect
from pycountry import languages
from collections import Counter
import matplotlib.pyplot as plt

def get_args():
    parser = argparse.ArgumentParser()

    parser.add_argument("--api-key", required=True, action="store")
    parser.add_argument("--video-id", required=True, action="store")
    parser.add_argument("--num", action="store", type=int, default=100)
    parser.add_argument("--threshhold", action="store", type=int)
    parser.add_argument("--outfile", action="store")

    return parser.parse_args()

def get_comments_json(key, v_id, num):
    max_results = min(num, 100)
    i = 0

    url = "https://www.googleapis.com/youtube/v3/commentThreads?key=%s&textFormat=plainText&part=snippet&videoId=%s&maxResults=%d&part=snippet" % (key, v_id, max_results)
    total = []
    page_token = ""

    while i < num:
        r = requests.get(url + "&pageToken=" + page_token)
        res = r.json()
        if r.status_code != 200:
            print("Request failed, sleeping for 5 seconds")
            sleep(5)
            continue

        try:
            page_token = res["nextPageToken"]
        except:
            num = i + res["pageInfo"]["totalResults"]

        total += res["items"]

        i += max_results

    return total, num

def get_comments_text(coms_json):
    return [com["snippet"]["topLevelComment"]["snippet"]["textOriginal"] for com in coms_json]

def my_detect(txt):
    try:
        return detect(txt)
    except:
        return "Unknown"

def get_comment_lang(coms_txt):
    return [my_detect(txt) for txt in coms_txt]

def get_lang_readable(coms_lng):
    return [languages.get(alpha_2=lng).name if lng != "Unknown" else lng for lng in coms_lng]

def count_langs(coms_lng):
    return Counter(coms_lng)

def get_video_title(v_id, key):
    url = 'https://www.googleapis.com/youtube/v3/videos?part=snippet&id=%s&key=%s' % (v_id, key)
    
    r = requests.get(url)
    if r.status_code != 200:
        print("Couldn't get video name, sleeping and trying again")
        sleep(5)
        return get_video_title(v_id, key)

    res = r.json()
    return res["items"][0]["snippet"]["title"]

def plot(v_title, cntr, num, threshhold, outfile):
    if threshhold is None:
        threshhold  = num / 75
    to_plot = {lang: count for lang, count in cntr.items() if count >= threshhold}

    plt.bar(to_plot.keys(), to_plot.values())
    plt.title("Comments per langauge for video \"%s\" for the top %d comments" % (v_title, num))
    plt.xlabel("Langauge")
    plt.ylabel("Number of Comments")

    fig = plt.gcf()
    fig.set_size_inches(12, 7)

    if outfile is None:
        plt.show()
    else:
        plt.savefig(outfile)

def main(args):
    coms_json, total_num = get_comments_json(args.api_key, args.video_id, args.num)
    coms_txt = get_comments_text(coms_json)
    coms_lng = get_comment_lang(coms_txt)
    coms_lng_readable = get_lang_readable(coms_lng)

    cntr = Counter(coms_lng_readable)

    plot(get_video_title(args.video_id, args.api_key), cntr, total_num, args.threshhold, args.outfile)
    
if __name__ == "__main__":
    main(get_args())