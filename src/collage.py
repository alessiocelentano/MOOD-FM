import requests
from PIL import Image, ImageDraw, ImageFont
import io

from cache import cache, update_cache, dump_cache
from spotify import get_search_result, get_track_name, get_artists, get_cover_url
from const import TRACK, ARTIST, ALBUM
from const import NO_COVER
from const import FONT

MODE = 'RGBA'
COLLAGE_SIZE = (2500, 2500)

X_OFFSET = 50
Y_OFFSET = 100
BG_SIZE = (1920, 1080)
BG_COLOR = '#000000'


async def create_collage(user, top_items_infos, size, time_range, type, clean=True):
    collage = Image.new(MODE, COLLAGE_SIZE, BG_COLOR)
    for index, item in enumerate(top_items_infos):
        cover_obj = item['cover']
        cover_size = (COLLAGE_SIZE[0] // size[0] + 1, COLLAGE_SIZE[1] // size[1] + 1)
        x = cover_size[0] * (index % size[0])
        y = cover_size[1] * (index // size[1])
        cover = centre_image(Image.open(cover_obj).convert(MODE)).resize(cover_size)
        if not clean:
            cover = add_item_name(user, cover, top_items_infos[index], time_range, type)
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


def add_item_name(user, cover, item_infos, time_range, type):
    track_name = item_infos['track']
    album_name = item_infos['album']
    artist = item_infos['artist']
    plays = int(item_infos['scrobbles'])

    band = draw_band(cover)
    # additional_plays = get_additional_plays(user, time_range, artist, track_name, album_name)
    additional_plays = 0
    border_offset = band.size[1] / 10

    top_text = track_name or album_name or artist
    bottom_text = str(plays + additional_plays) + ' plays'
    if type == TRACK or type == ALBUM:
        bottom_text = f'by {artist}, {bottom_text}'
    
    font = adjust_font_size(band, cover, max(top_text, bottom_text, key=len), border_offset)

    draw = ImageDraw.Draw(cover)
    draw.text((border_offset, cover.size[1] - band.size[1]/2 - 6*font.size/5), top_text, (255,255,255), font=font)
    draw.text((border_offset, cover.size[1] - band.size[1]/2 - font.size/5), bottom_text, (255,255,255), font=font)
    
    return cover


def get_additional_plays(user, time_range, artist, track_name, album_name):
    # Fix: not scrobble time in User. Impossible to add them consistently
    #      alternative: use only for overall
    additional_plays = 0
    for index in user.find_tracks_index(artist, track_name, album_name):
        additional_plays += user.scrobbles_before_lastfm[index]['scrobbles']
    return additional_plays


def draw_band(cover):
    band = Image.new(MODE, (cover.size[0], int(cover.size[1] / 6)))
    band.paste((0, 0, 0, 220), (0, 0, band.size[0], band.size[1]))
    cover.paste(band, (0, cover.size[1] - band.size[1]), band)
    return band


def adjust_font_size(band, cover, text, offset):
    font = None
    size = int(band.size[1] / 3)
    while not font or font.getlength(text) > cover.size[0] - offset:
        font = ImageFont.truetype(FONT, size)
        size -= 1
    return font


async def get_top_items_infos(lastfm_user, size, time_range, type):
    top_items = get_top_items(lastfm_user, size, time_range, type)
    covers_list = get_top_items_covers_url(top_items, type)
    top_items_infos = []
    for item, cover in zip(top_items, covers_list):
        top_items_infos.append({
            'track': item.item.title if type == TRACK else None,
            'album': item.item.title if type == ALBUM else None,
            'artist': item.item.name if type == ARTIST else item.item.artist.name,
            'scrobbles': item.weight,
            'cover': cover
        })
    return top_items_infos
    

def get_top_items(lastfm_user, size, time_range, type):
    if type == TRACK:
        return lastfm_user.get_top_tracks(period=time_range, limit=size[0]*size[1])
    if type == ARTIST:
        return lastfm_user.get_top_artists(period=time_range, limit=size[0]*size[1])
    if type == ALBUM:
        return lastfm_user.get_top_albums(period=time_range, limit=size[0]*size[1])


def get_top_items_covers_url(top_items, type):
    covers_list = []

    for i in top_items:
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
