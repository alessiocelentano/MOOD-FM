from pylast import LastFMNetwork

from const import FM_API_KEY, FM_API_SECRET


network = LastFMNetwork(
    api_key=FM_API_KEY,
    api_secret=FM_API_SECRET
)
