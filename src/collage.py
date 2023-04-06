import io
from PIL import Image, ImageDraw, ImageFont
import requests
from time import time

from pylast import PERIOD_7DAYS, PERIOD_1MONTH, PERIOD_3MONTHS, \
                PERIOD_6MONTHS, PERIOD_12MONTHS, PERIOD_OVERALL

from cache import cache, update_cache, dump_cache
from const import SEVEN_DAYS_IN_SECONDS, ONE_MONTH_IN_SECONDS, \
                THREE_MONTHS_IN_SECONDS, SIX_MONTHS_IN_SECONDS, \
                TWELVE_MONTHS_IN_SECONDS, \
                TRACK, ARTIST, ALBUM, \
                NO_COVER, FONT
from spotify import get_search_result, get_name, get_artists, get_cover_url


MODE = 'RGBA'
COLLAGE_SIZE = (2500, 2500)
BG_SIZE = (1920, 1080)
X_OFFSET = 50
Y_OFFSET = 100

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BG_COLOR = WHITE


async def create_collage(items, size, type, clean=True):
    collage = Image.new(MODE, COLLAGE_SIZE, BG_COLOR)

    for index, item in enumerate(items):
        cover_obj = item['cover']
        cover_size = (COLLAGE_SIZE[0] // size[0] + 1, COLLAGE_SIZE[1] // size[1] + 1)

        x = cover_size[0] * (index % size[0])
        y = cover_size[1] * (index // size[1])

        cover = centre_image(Image.open(cover_obj).convert(MODE)).resize(cover_size)
        if not clean:
            cover = add_item_name(cover, type, items[index])

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


def add_item_name(cover, type, item_infos):
    name = item_infos['name']
    artist = item_infos['artist']  # It's None if type == ARTIST
    plays = int(item_infos['plays'])

    band = draw_band(cover)
    border_offset = band.size[1] / 10

    top_text = name
    bottom_text = f'{plays} plays'
    if type == TRACK or type == ALBUM:
        bottom_text = f'by {artist}, {bottom_text}'
    
    font = adjust_font_size(
        band=band,
        cover=cover,
        longest_line=max(top_text, bottom_text, key=len),
        border_offset=border_offset
    )

    draw = ImageDraw.Draw(cover)
    draw.text(
        xy=(border_offset, cover.size[1] - band.size[1]/2 - 6*font.size/5),
        text=top_text,
        fill=WHITE,
        font=font
    )
    draw.text(
        xy=(border_offset, cover.size[1] - band.size[1]/2 - font.size/5),
        text=bottom_text,
        fill=WHITE,
        font=font
    )
    
    return cover


def draw_band(cover):
    band = Image.new(MODE, (cover.size[0], int(cover.size[1] / 6)))
    band.paste((0, 0, 0, 220), (0, 0, band.size[0], band.size[1]))
    cover.paste(band, (0, cover.size[1] - band.size[1]), band)
    return band


def adjust_font_size(band, cover, longest_line, border_offset):
    font = None
    size = int(band.size[1] / 3)
    while not font or font.getlength(longest_line) > cover.size[0] - border_offset:
        font = ImageFont.truetype(FONT, size)
        size -= 1
    return font


async def get_top_items_infos(user, lastfm_user, size, time_range, type):
    history_top_items = user.get_history_items(time_range, type)
    lastfm_top_items = get_lastfm_top_items(lastfm_user, size, time_range, type)
    top_items = merge_items(
        history_top_items,
        lastfm_top_items,
        lastfm_user,
        time_range,
        type,
        limit=size[0]*size[1]
    )
    covers_list = get_top_items_covers_url(top_items, type)
    top_items_infos = []
    for item, cover in zip(top_items, covers_list):
        top_items_infos.append({
            'type': type,
            'name': item['name'],
            'artist': item['artist'],
            'plays': item['plays'],
            'cover': cover
        })
    return top_items_infos
    

def get_lastfm_top_items(lastfm_user, size, time_range, type):
    if type == TRACK:
        return lastfm_user.get_top_tracks(period=time_range, limit=size[0]*size[1])
    if type == ARTIST:
        return lastfm_user.get_top_artists(period=time_range, limit=size[0]*size[1])
    if type == ALBUM:
        return lastfm_user.get_top_albums(period=time_range, limit=size[0]*size[1])


def merge_items(history_top_items, lastfm_top_items, lastfm_user, time_range, type, limit):
    for item in lastfm_top_items:
        if type == ARTIST:
            key = create_key_dict_from_item(type, item.item.name)
        else:
            key = create_key_dict_from_item(type, item.item.title, artist=item.item.artist.name)

        if key in history_top_items:
            history_top_items[key]['plays'] += int(item.weight)
            history_top_items[key]['updated'] = True

        else:
            history_top_items[key] = {
                'type': type,
                'name': item.item.title if type != ARTIST else item.item.name,
                'artist': item.item.artist.name if type != ARTIST else None,
                'plays': int(item.weight),
                'updated': True
            }

    sorted_history = sorted(history_top_items.items(), key=lambda key: key[1]['plays'], reverse=True)
    history_top_items = [item[1] for item in sorted_history][:limit]

    for i in range(len(history_top_items)):
        if history_top_items[i]['updated']:
            continue

        name = history_top_items[i]['name']
        artist = history_top_items[i]['artist']

        for pl in lastfm_user.get_track_scrobbles(artist, name):
            if is_within_time_range(pl.timestamp, time_range):
                history_top_items[i]['plays'] += 1

        history_top_items[i]['updated'] = True

    sorted_items = sorted(history_top_items, key=lambda key: key['plays'], reverse=True)
    return sorted_items


def create_key_dict_from_item(type, name, artist=None):
    if type == ARTIST:
        return name
    return f'{name} {artist}'


def is_within_time_range(unixtime, time_range):
    if time_range == PERIOD_7DAYS and time() - unixtime < SEVEN_DAYS_IN_SECONDS:
        return True
    elif time_range == PERIOD_1MONTH and time() - unixtime < ONE_MONTH_IN_SECONDS:
        return True
    elif time_range == PERIOD_3MONTHS and time() - unixtime < THREE_MONTHS_IN_SECONDS:
        return True
    elif time_range == PERIOD_6MONTHS and time() - unixtime < SIX_MONTHS_IN_SECONDS:
        return True
    elif time_range == PERIOD_12MONTHS and time() - unixtime < TWELVE_MONTHS_IN_SECONDS:
        return True
    elif time_range == PERIOD_OVERALL:
        return True
    return False



def get_top_items_covers_url(top_items, type):
    covers_list = []

    for item_dict in top_items:
        key = create_key_dict_from_item(type, artist=item_dict['artist'], name=item_dict['name'])
        if key in cache:
            covers_list.append(requests.get(cache[key]['image_url'], stream=True).raw)
            continue

        item = item_dict['name']
        item_infos = find_spotify_item(key, item, type)
        image_url = get_cover_url(item_infos, type)

        if not image_url:
            covers_list.append(NO_COVER)
            continue

        covers_list.append(requests.get(image_url, stream=True).raw)
        name = get_name(item_infos)
        artists = get_artists(item_infos['artists'])
        update_cache(key, {
            'name': name,
            'artists': artists,
            'image_url': image_url
        })
        dump_cache()

    return covers_list


def find_spotify_item(query, item, type):
    counter = 0
    first_result = None
    while True:
        counter += 1
        item_infos = get_search_result(query, type, limit=counter)
        if not first_result:
            first_result = item_infos
        if item_infos['name'] == item:
            return item_infos
        if counter > 5:
            return first_result


def get_descriptive_collage(lastfm_user):
    collage = Image.new(MODE, BG_SIZE, BG_COLOR)
