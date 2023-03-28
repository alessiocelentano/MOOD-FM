import requests
from PIL import Image
import io

from const import TRACKS, ARTISTS, ALBUMS
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


def get_top_items_covers_url(lastfm_user, network, size, period, type):
    items = get_top_items(lastfm_user, size, period, type)
    covers_list = []
    for i in items:
        image_url = get_image(network, i, type)
        if image_url:
            covers_list.append(requests.get(image_url, stream=True).raw)
        else:
            covers_list.append(NO_COVER)
    return covers_list


def get_top_items(lastfm_user, size, period, type):
    if type == TRACKS:
        return lastfm_user.get_top_tracks(period=period, limit=size[0]*size[1])
    if type == ARTISTS:
        return lastfm_user.get_top_artists(period=period, limit=size[0]*size[1])
    if type == ALBUMS:
        return lastfm_user.get_top_albums(period=period, limit=size[0]*size[1])


def get_image(network, item, type):
    if type == TRACKS:
        # FIX: NO IMAGE FOUND
        return network.search_for_track(item.item.artist.name, item.item.title).get_next_page()[0].info['image'][-1]
    if type == ARTISTS:
        # FIX: NO IMAGE FOUND
        return network.search_for_artist(item.item.name).get_next_page()[0].info['image'][-1]
    if type == ALBUMS:
        return item.item.info['image'][-1]


def get_descriptive_collage(lastfm_user):
    collage = Image.new(MODE, BG_SIZE, BG_COLOR)

