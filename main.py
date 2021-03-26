import requests
import string
from credentials import api_key

import util
import itertools

playlists = [
    'UUdubelOloxR3wzwJG9x8YqQ', # tvrain uploadas
    'UUo4GExFphiUnNiMMExvFWdg', # echo msk uploadas
    'PLgMaGEI-ZiiZ0ZvUtduoDRVXcU5ELjPcI', # trending russia
]

recent = itertools.chain.from_iterable(util.top_recent(p, api_key, recent_days=1) for p in playlists)
recent = list(recent)

min_viewCount = 100_000
top = [v for v in recent if int(v['statistics']['viewCount']) > min_viewCount]
top = sorted(top, key=lambda v: int(v['statistics']['viewCount']), reverse=True)

for v in top:
    vc = int(v['statistics']['viewCount'])
    print(f"{vc:10,} https://www.youtube.com/watch?v={v['id']} {v['snippet']['channelTitle'][:15]:<15} {v['snippet']['title']:<40}")

