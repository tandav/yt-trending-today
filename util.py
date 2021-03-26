import requests
import itertools
import functools
import datetime
import dateutil.parser
import dateutil.tz

# https://more-itertools.readthedocs.io/en/stable/api.html
def take(n, iterable): return list(itertools.islice(iterable, n))


def chunked(iterable, n): return iter(functools.partial(take, n, iter(iterable)), [])


def ago(e):
    # e: pass timedelta between timestamps in 1579812524 format
    e *= 1000  # convert to 1579812524000 format
    t = round(e / 1000)
    n = round(t / 60)
    r = round(n / 60)
    o = round(r / 24)
    i = round(o / 30)
    a = round(i / 12)
    if e < 0:
        return 'just now'
    elif t < 10:
        return 'just now'
    elif t < 45:
        return str(t) + ' seconds ago'
    elif t < 90:
        return 'a minute ago'
    elif n < 45:
        return str(n) + ' minutes ago'
    elif n < 90:
        return 'an hour ago'
    elif r < 24:
        return str(r) + ' hours ago'
    elif r < 36:
        return 'a day ago'
    elif o < 30:
        return str(o) + ' days ago'
    elif o < 45:
        return 'a month ago'
    elif i < 12:
        return str(i) + ' months ago'
    elif i < 18:
        return 'a year ago'
    else:
        return str(a) + ' years ago'


def trending_videos(api_key, regionCode='US'):
    '''regionCode: https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes'''
    print('start loading trending_videos')

    def _load():
        URL = 'https://www.googleapis.com/youtube/v3/videos'
        payload = dict(
            part='snippet,statistics',
            maxResults=50,
            key=api_key,
            chart='mostPopular',
            regionCode=regionCode,
        )
        r = requests.get(URL, params=payload).json()
        videos = r['items']
        # do while emulation
        while 'nextPageToken' in r:
            payload['pageToken'] = r['nextPageToken']
            r = requests.get(URL, params=payload).json()
            videos += r['items']
        return videos

    def _clean(videos):
        '''delete useless information'''
        V = []
        for v in videos:
            snippet = v['snippet']
            statistics = v['statistics']
            del statistics['favoriteCount']
            w = {'id': v['id'], 'title': snippet['title'], 'channelTitle': snippet['channelTitle'],
                 'publishedAt': snippet['publishedAt'],
                 'viewCount': int(statistics.get('viewCount', 0)),
                 'likeCount': int(statistics.get('likeCount', 0)),
                 'dislikeCount': int(statistics.get('dislikeCount', 0)),
                 'commentCount': int(statistics.get('commentCount', 0)),
                 }
            V.append(w)
        return V

    videos = _clean(_load())
    print('end loading trending_videos')
    return videos


def videos_info(videos, api_key):
    if isinstance(videos, list) and len(videos) > 50:  # yt api limit
        _ = chunked(videos, 50)
        _ = map(lambda x: videos_info(x, api_key), _)
        _ = itertools.chain.from_iterable(_)
        _ = list(_)
        return _

    URL = 'https://www.googleapis.com/youtube/v3/videos'
    payload = dict(
        part='snippet,statistics',
        maxResults=50,
        key=api_key,
        id=','.join(videos)
    )
    r = requests.get(URL, params=payload).json()
    videos = r['items']
    # do while emulation
    while 'nextPageToken' in r:
        payload['pageToken'] = r['nextPageToken']
        r = requests.get(URL, params=payload).json()
        videos += r['items']
    return videos


def playlists(channelId, api_key):
    payload = {
        'part': 'snippet',
        'channelId': channelId,
        'maxResults': 50,
        'key': api_key,
    }

    r = requests.get('https://www.googleapis.com/youtube/v3/playlists', params=payload).json()
    playlists = r['items']

    while 'nextPageToken' in r:
        payload['pageToken'] = r['nextPageToken']
        r = requests.get('https://www.googleapis.com/youtube/v3/playlistItems', params=payload).json()
        playlists += r['items']

    return playlists


def videos(playlistId, api_key, limit=False):
    payload = {
        'part': 'snippet',
        'playlistId': playlistId,
        'maxResults': 50,
        'key': api_key,
    }

    r = requests.get('https://www.googleapis.com/youtube/v3/playlistItems', params=payload).json()
    videos = r['items']

    # do while emulation
    while 'nextPageToken' in r:
        payload['pageToken'] = r['nextPageToken']
        r = requests.get('https://www.googleapis.com/youtube/v3/playlistItems', params=payload).json()
        videos += r['items']
        if limit and len(videos) >= limit:
            break
    return videos


def top_recent(playlistId, api_key, recent_days=1):
    def _days_ago_published(v):
        return (datetime.datetime.now(datetime.timezone.utc) - dateutil.parser.parse(v['snippet']['publishedAt'])).days

    payload = {'part': 'snippet', 'playlistId': playlistId, 'maxResults': 50, 'key': api_key, }
    url = 'https://www.googleapis.com/youtube/v3/playlistItems'
    r = requests.get(url, params=payload).json()
    r = r['items']
    videos = [v for v in r if _days_ago_published(v) <= recent_days]

    # do while emulation
    while 'nextPageToken' in r:
        payload['pageToken'] = r['nextPageToken']
        r = requests.get(url, params=payload).json()['items']
        is_recent = [_days_ago_published(v) <= recent_days for v in r]
        if any(is_recent):
            videos += list(itertools.compress(r, is_recent))
            break
        else:
            videos += r

    videos = [v['snippet']['resourceId']['videoId'] for v in videos]
    vi = videos_info(videos, api_key)
    return vi



def compress(videos, compress_schema):
    return [[v.get(k) for k in compress_schema] for v in videos]
    # return list(map(lambda v: [v.get(k) for k in compress_schema], videos))


def uploads_playlist(channelId, api_key):
    return requests.get(
        'https://www.googleapis.com/youtube/v3/channels',
        params={'id': channelId, 'part': 'contentDetails', 'key': api_key, }
    ).json()['items'][0]['contentDetails']['relatedPlaylists']['uploads']


