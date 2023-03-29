import requests
from PIL import Image
import io

from cache import cache, update_cache, dump_cache
from spotify import get_search_result, get_cover_url
from const import TRACK, ARTIST, ALBUM
from const import NO_COVER

MODE = 'RGB'
COLLAGE_SIZE = (900, 900)

X_OFFSET = 50
Y_OFFSET = 100
BG_SIZE = (1920, 1080)
BG_COLOR = '#5D4037'


def create_collage(covers_list, size):
    collage = Image.new(MODE, COLLAGE_SIZE, BG_COLOR)
    for index, item in enumerate(covers_list):
        cover_size = (COLLAGE_SIZE[0] // size[0], COLLAGE_SIZE[1] // size[1])
        x = cover_size[0] * (index % size[0])
        y = cover_size[1] * (index // size[1])
        cover = Image.open(item).resize(cover_size)
        collage.paste(cover, (x, y))
    image_bytes = io.BytesIO()
    collage.save(image_bytes, format='png')
    return image_bytes


def get_top_items_covers_url(lastfm_user, size, period, type):
    items = get_top_items(lastfm_user, size, period, type)
    covers_list = []
    for i in items:
        query = get_query(i, type)
        if query in cache:
            covers_list.append(requests.get(cache[query], stream=True).raw)
        else:
            item_infos = get_search_result(query, type)
            image_url = get_cover_url(item_infos, type)
            if image_url:
                covers_list.append(requests.get(image_url, stream=True).raw)
                update_cache(query, image_url)
                dump_cache()
            else:
                covers_list.append(NO_COVER)
    return covers_list


def get_top_items(lastfm_user, size, period, type):
    if type == TRACK:
        return lastfm_user.get_top_tracks(period=period, limit=size[0]*size[1])
    if type == ARTIST:
        return lastfm_user.get_top_artists(period=period, limit=size[0]*size[1])
    if type == ALBUM:
        return lastfm_user.get_top_albums(period=period, limit=size[0]*size[1])


def get_query(item, type):
    if type == TRACK:
        return ' '.join([item.item.title, item.item.artist.name])
    if type == ARTIST:
        return item.item.name
    if type == ALBUM:
        return ' '.join([item.item.title, item.item.artist.name])


def get_descriptive_collage(lastfm_user):
    collage = Image.new(MODE, BG_SIZE, BG_COLOR)
