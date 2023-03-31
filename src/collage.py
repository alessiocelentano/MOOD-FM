import requests
from PIL import Image
import io

from cache import cache, update_cache, dump_cache
from spotify import get_search_result, get_track_name, get_artists, get_cover_url
from const import TRACK, ARTIST, ALBUM
from const import NO_COVER

MODE = 'RGB'
COLLAGE_SIZE = (1920, 1920)

X_OFFSET = 50
Y_OFFSET = 100
BG_SIZE = (1920, 1080)
BG_COLOR = '#000000'


async def create_collage(covers_list, size):
    collage = Image.new(MODE, COLLAGE_SIZE, BG_COLOR)
    for index, item in enumerate(covers_list):
        cover_size = (COLLAGE_SIZE[0] // size[0] + 1, COLLAGE_SIZE[1] // size[1] + 1)
        x = cover_size[0] * (index % size[0])
        y = cover_size[1] * (index // size[1])
        cover = centre_image(Image.open(item)).resize(cover_size)
        collage.paste(cover, (x, y))
    image_bytes = io.BytesIO()
    collage.save(image_bytes, format='png')
    return image_bytes


def centre_image(image):
    width, height = image.size
    new_dim = min(width, height)
    left = (width - new_dim) / 2
    top = (height - new_dim) / 2
    right = (width + new_dim) / 2
    bottom = (height + new_dim) / 2
    return image.crop((left, top, right, bottom))


async def get_top_items_covers_url(lastfm_user, size, time_range, type):
    items = get_top_items(lastfm_user, size, time_range, type)
    covers_list = []

    for i in items:
        query = get_query(i, type)
        if query in cache:
            covers_list.append(requests.get(cache[query]['image_url'], stream=True).raw)
            continue

        item_name = i.item.name if type == ARTIST else i.item.title
        item_infos = find_spotify_item(query, item_name, type)
        image_url = get_cover_url(item_infos, type)

        if not image_url:
            covers_list.append(NO_COVER)
            continue

        covers_list.append(requests.get(image_url, stream=True).raw)
        if type == TRACK:
            track_name = get_track_name(item_infos)
            track_artists = get_artists(item_infos['artists'])
            update_cache(query, {
                'track_name': track_name,
                'track_artists': track_artists,
                'image_url': image_url
            })
        else:
            update_cache(query, {'image_url': image_url})
        dump_cache()

    return covers_list


def get_top_items(lastfm_user, size, time_range, type):
    if type == TRACK:
        return lastfm_user.get_top_tracks(period=time_range, limit=size[0]*size[1])
    if type == ARTIST:
        return lastfm_user.get_top_artists(period=time_range, limit=size[0]*size[1])
    if type == ALBUM:
        return lastfm_user.get_top_albums(period=time_range, limit=size[0]*size[1])


def find_spotify_item(query, item_name, type):
    counter = 0
    first_result = None
    while True:
        counter += 1
        item_infos = get_search_result(query, type, limit=counter)
        if not first_result:
            first_result = item_infos
        if item_infos['name'] == item_name:
            return item_infos
        if counter > 5:
            return first_result


def get_query(item, type):
    if type == TRACK:
        return ' '.join([item.item.title, item.item.artist.name])
    if type == ARTIST:
        return ' '.join([item.item.name])
    if type == ALBUM:
        return ' '.join([item.item.title, item.item.artist.name])


def get_descriptive_collage(lastfm_user):
    collage = Image.new(MODE, BG_SIZE, BG_COLOR)
