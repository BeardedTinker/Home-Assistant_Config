"""Support for media browsing."""
import logging
from homeassistant.components.media_player import BrowseError, BrowseMedia
from ytmusicapi import ytmusic
from .const import *


PLAYABLE_MEDIA_TYPES = [
    MediaType.ALBUM,
    USER_ALBUM,
    USER_ARTIST,
    MediaType.TRACK,
    MediaType.PLAYLIST,
    LIB_TRACKS,
    HISTORY,
    USER_TRACKS,
    ALBUM_OF_TRACK
]

CONTAINER_TYPES_SPECIFIC_MEDIA_CLASS = {
    MediaType.ALBUM: MediaClass.ALBUM,
    LIB_ALBUM: MediaClass.ALBUM,
    MediaType.ARTIST: MediaClass.ARTIST,
    MediaType.PLAYLIST: MediaClass.PLAYLIST,
    LIB_PLAYLIST: MediaClass.PLAYLIST,
    HISTORY: MediaClass.PLAYLIST,
    USER_TRACKS: MediaClass.PLAYLIST,
    MediaType.SEASON: MediaClass.SEASON,
    MediaType.TVSHOW: MediaClass.TV_SHOW,
}

CHILD_TYPE_MEDIA_CLASS = {
    MediaType.SEASON: MediaClass.SEASON,
    MediaType.ALBUM: MediaClass.ALBUM,
    MediaType.ARTIST: MediaClass.ARTIST,
    MediaType.MOVIE: MediaClass.MOVIE,
    MediaType.PLAYLIST: MediaClass.PLAYLIST,
    MediaType.TRACK: MediaClass.TRACK,
    MediaType.TVSHOW: MediaClass.TV_SHOW,
    MediaType.CHANNEL: MediaClass.CHANNEL,
    MediaType.EPISODE: MediaClass.EPISODE,
}

_LOGGER = logging.getLogger(__name__)


class UnknownMediaType(BrowseError):
    """Unknown media type."""


async def build_item_response(ytmusicplayer, payload):
    """Create response payload for the provided media query."""
    search_id = payload[SEARCH_ID]
    search_type = payload[SEARCH_TYPE]
    media_library = ytmusicplayer._api
    hass = ytmusicplayer.hass

    children = []
    thumbnail = None
    title = None
    media = None
    sort_list = ytmusicplayer._sortBrowser
    p1 = datetime.datetime.now()
    _LOGGER.debug("- build_item_response for: " + search_type)

    if search_type == LIB_PLAYLIST:  # playlist OVERVIEW -> lists playlists
        media = await hass.async_add_executor_job(media_library.get_library_playlists, BROWSER_LIMIT)
        title = LIB_PLAYLIST_TITLE  # single playlist

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",                  # noqa: E251
                media_class = MediaClass.PLAYLIST,          # noqa: E251
                media_content_type = MediaType.PLAYLIST,    # noqa: E251
                media_content_id = f"{item['playlistId']}",  # noqa: E251
                can_play = True,                             # noqa: E251
                can_expand = True,                           # noqa: E251
                thumbnail = find_thumbnail(item)             # noqa: E251
            ))


    elif search_type == MediaType.PLAYLIST:  # single playlist -> lists tracks
        media = await hass.async_add_executor_job(media_library.get_playlist, search_id, BROWSER_LIMIT)
        title = media['title']

        for item in media['tracks']:
            item_title = f"{item['title']}"
            if("artists" in item):
                artist = ""
                if(isinstance(item["artists"], str)):
                    artist = item["artists"]
                elif(isinstance(item["artists"], list)):
                    artist = item["artists"][0]["name"]
                if(artist):
                    item_title = artist + " - " + item_title

            children.append(BrowseMedia(
                title = item_title,                       # noqa: E251
                media_class = MediaClass.TRACK,          # noqa: E251
                media_content_type = MediaType.TRACK,    # noqa: E251
                media_content_id = f"{item['videoId']}",  # noqa: E251
                can_play = True,                          # noqa: E251
                can_expand = False,                       # noqa: E251
                thumbnail = find_thumbnail(item)          # noqa: E251
            ))

    elif search_type == LIB_ALBUM:  # LIB! album OVERVIEW, not uploaded -> lists albums
        media = await hass.async_add_executor_job(media_library.get_library_albums, BROWSER_LIMIT)
        title = LIB_ALBUM_TITLE


        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",                 # noqa: E251
                media_class = MediaClass.ALBUM,            # noqa: E251
                media_content_type = MediaType.ALBUM,      # noqa: E251
                media_content_id = f"{item['browseId']}",   # noqa: E251
                can_play = True,                            # noqa: E251
                can_expand = True,                          # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))

    elif search_type == MediaType.ALBUM:  # single album (NOT uploaded) -> lists tracks
        res = await hass.async_add_executor_job(media_library.get_album, search_id)
        media = res['tracks']
        title = res['title']

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",               # noqa: E251
                media_class = MediaClass.TRACK,          # noqa: E251
                media_content_type = MediaType.TRACK,    # noqa: E251
                media_content_id = f"{item['videoId']}",  # noqa: E251
                can_play = True,                          # noqa: E251
                can_expand = False,                       # noqa: E251
                thumbnail = find_thumbnail(res)           # noqa: E251
            ))

    elif search_type == LIB_TRACKS:  # liked songs (direct list, NOT uploaded) -> lists tracks
        media = await hass.async_add_executor_job(lambda: media_library.get_library_songs(limit=BROWSER_LIMIT))
        title = LIB_TRACKS_TITLE

        for item in media:
            item_title = f"{item['title']}"
            if("artists" in item):
                artist = ""
                if(isinstance(item["artists"], str)):
                    artist = item["artists"]
                elif(isinstance(item["artists"], list)):
                    artist = item["artists"][0]["name"]
                if(artist):
                    item_title = artist + " - " + item_title

            children.append(BrowseMedia(
                title = item_title,                         # noqa: E251
                media_class = MediaClass.TRACK,            # noqa: E251
                media_content_type = MediaType.TRACK,      # noqa: E251
                media_content_id = f"{item['videoId']}",    # noqa: E251
                can_play = True,                            # noqa: E251
                can_expand = False,                         # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))

    elif search_type == HISTORY:  # history songs (direct list) -> lists tracks
        media = await hass.async_add_executor_job(media_library.get_history)
        search_id = HISTORY
        title = HISTORY_TITLE

        for item in media:
            item_title = f"{item['title']}"
            if("artists" in item):
                artist = ""
                if(isinstance(item["artists"], str)):
                    artist = item["artists"]
                elif(isinstance(item["artists"], list)):
                    artist = item["artists"][0]["name"]
                if(artist):
                    item_title = artist + " - " + item_title

            children.append(BrowseMedia(
                title = item_title,                         # noqa: E251
                media_class = MediaClass.TRACK,            # noqa: E251
                media_content_type = MediaType.TRACK,      # noqa: E251
                media_content_id = f"{item['videoId']}",    # noqa: E251
                can_play = True,                            # noqa: E251
                can_expand = False,                         # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))

    elif search_type == USER_TRACKS:  # list all uploaded songs -> lists tracks
        media = await hass.async_add_executor_job(media_library.get_library_upload_songs, BROWSER_LIMIT)
        search_id = USER_TRACKS
        title = USER_TRACKS_TITLE

        for item in media:
            item_title = f"{item['title']}"
            if("artist" in item):
                artist = ""
                if(isinstance(item["artist"], str)):
                    artist = item["artist"]
                elif(isinstance(item["artist"], list)):
                    artist = item["artist"][0]["name"]
                if(artist):
                    item_title = artist + " - " + item_title

            children.append(BrowseMedia(
                title = item_title,                         # noqa: E251
                media_class = MediaClass.TRACK,            # noqa: E251
                media_content_type = MediaType.TRACK,      # noqa: E251
                media_content_id = f"{item['videoId']}",    # noqa: E251
                can_play = True,                            # noqa: E251
                can_expand = False,                         # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))

    elif search_type == USER_ALBUMS:  # uploaded album overview!! -> lists user albums
        media = await hass.async_add_executor_job(media_library.get_library_upload_albums, BROWSER_LIMIT)
        title = USER_ALBUMS_TITLE

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",                 # noqa: E251
                media_class = MediaClass.ALBUM,            # noqa: E251
                media_content_type = USER_ALBUM,            # noqa: E251
                media_content_id = f"{item['browseId']}",   # noqa: E251
                can_play = True,                            # noqa: E251
                can_expand = True,                          # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))

    elif search_type == USER_ALBUM:  # single uploaded album -> lists tracks
        res = await hass.async_add_executor_job(media_library.get_library_upload_album, search_id)
        media = res['tracks']
        title = res['title']

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",               # noqa: E251
                media_class = MediaClass.TRACK,          # noqa: E251
                media_content_type = MediaType.TRACK,    # noqa: E251
                media_content_id = f"{item['videoId']}",  # noqa: E251
                can_play = True,                          # noqa: E251
                can_expand = False,                       # noqa: E251
                thumbnail = find_thumbnail(item)          # noqa: E251
            ))

    elif search_type == USER_ARTISTS:  # with S
        media = await hass.async_add_executor_job(media_library.get_library_upload_artists, BROWSER_LIMIT)
        title = USER_ARTISTS_TITLE

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['artist']}",                # noqa: E251
                media_class = MediaClass.ARTIST,           # noqa: E251
                media_content_type = USER_ARTIST,           # noqa: E251
                media_content_id = f"{item['browseId']}",   # noqa: E251
                can_play = False,                           # noqa: E251
                can_expand = True,                          # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))

    elif search_type == USER_ARTISTS_2:  # list all artists now, but follow up will be the albums of that artist
        media = await hass.async_add_executor_job(media_library.get_library_upload_artists, BROWSER_LIMIT)
        title = USER_ARTISTS_2_TITLE

        for item in media:
            children.append(BrowseMedia(
                title = f"{item['artist']}",                # noqa: E251
                media_class = MediaClass.ARTIST,           # noqa: E251
                media_content_type = USER_ARTIST_2,         # noqa: E251
                media_content_id = f"{item['browseId']}",   # noqa: E251
                can_play = False,                           # noqa: E251
                can_expand = True,                          # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))

    elif search_type == USER_ARTIST:  # without S
        media = await hass.async_add_executor_job(media_library.get_library_upload_artist, search_id, BROWSER_LIMIT)
        title = USER_ARTIST_TITLE
        if(isinstance(media, list)):
            if('artist' in media[0]):
                if(isinstance(media[0]['artist'], list)):
                    if('name' in media[0]['artist'][0]):
                        title = media[0]['artist'][0]['name']

        for item in media:
            if("artists" in item):
                artist = ""
                if(isinstance(item["artists"], str)):
                    artist = item["artists"]
                elif(isinstance(item["artists"], list)):
                    artist = item["artists"][0]["name"]
                if(artist):
                    title = artist + " - " + title

            children.append(BrowseMedia(
                title = f"{item['title']}",                 # noqa: E251
                media_class = MediaClass.TRACK,            # noqa: E251
                media_content_type = MediaType.TRACK,      # noqa: E251
                media_content_id = f"{item['videoId']}",    # noqa: E251
                can_play = True,                            # noqa: E251
                can_expand = False,                         # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))

    elif search_type == USER_ARTIST_2:  # list each album of an uploaded artists only once .. next will be uploaded album view 'USER_ALBUM'
        media_all = await hass.async_add_executor_job(media_library.get_library_upload_artist, search_id, BROWSER_LIMIT)
        title = USER_ARTIST_2_TITLE
        media = list()
        for item in media_all:
            if('album' in item):
                if('name' in item['album']):
                    if(all(item['album']['name'] != a['title'] for a in media)):
                        media.append({
                            'type': 'user_album',
                            'browseId': item['album']['id'],
                            'title': item['album']['name'],
                            'thumbnails': item['thumbnails']
                        })
        if('artist' in media_all[0]):
                if(isinstance(media_all[0]['artist'], list)):
                    if('name' in media_all[0]['artist'][0]):
                        title = "Uploaded albums of " + media_all[0]['artist'][0]['name']


        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",                 # noqa: E251
                media_class = MediaClass.ALBUM,            # noqa: E251
                media_content_type = USER_ALBUM,            # noqa: E251
                media_content_id = f"{item['browseId']}",   # noqa: E251
                can_play = True,                            # noqa: E251
                can_expand = True,                          # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))


    elif search_type == SEARCH:
        title = SEARCH_TITLE
        if ytmusicplayer._search is not None:
            media_all = await hass.async_add_executor_job(lambda: media_library.search(query=ytmusicplayer._search.get('query', ""), filter=ytmusicplayer._search.get('filter', None), limit=int(ytmusicplayer._search.get('limit', 20))))

            if(ytmusicplayer._search.get('filter', None) is not None):
                helper = {}
            else:
                helper = {'song': "Track: ", 'playlist': "Playlist: ", 'album': "Album: ", 'artist': "Artist: "}

            for a in media_all:
                if(a['category'] in ["Top result", "Podcast"]):
                    continue

                if(a['resultType'] == 'song'):
                    
                    artists = ""
                    if("artist" in a):
                        artists = a["artist"]
                    if("artists" in a):
                        artists = ', '.join(artist["name"] for artist in a["artists"] if "name" in artist)
                        
                    children.append(BrowseMedia(
                        title = helper.get(a['resultType'], "") + artists + " - " + a['title'],  # noqa: E251
                        media_class = MediaClass.TRACK,                       # noqa: E251
                        media_content_type = MediaType.TRACK,                 # noqa: E251
                        media_content_id = a['videoId'],                       # noqa: E251
                        can_play = True,                                       # noqa: E251
                        can_expand = False,                                    # noqa: E251
                        thumbnail = find_thumbnail(a)                          # noqa: E251
                    ))
                elif(a['resultType'] == 'playlist'):
                    children.append(BrowseMedia(
                        title = helper.get(a['resultType'], "") + a['title'],  # noqa: E251
                        media_class = MediaClass.PLAYLIST,                    # noqa: E251
                        media_content_type = MediaType.PLAYLIST,              # noqa: E251
                        media_content_id = f"{a['browseId']}",                 # noqa: E251
                        can_play = True,                                       # noqa: E251
                        can_expand = True,                                     # noqa: E251
                        thumbnail = find_thumbnail(a)                          # noqa: E251
                    ))
                elif(a['resultType'] == 'album'):
                    children.append(BrowseMedia(
                        title = helper.get(a['resultType'], "") + a['title'],  # noqa: E251
                        media_class = MediaClass.ALBUM,                       # noqa: E251
                        media_content_type = MediaType.ALBUM,                 # noqa: E251
                        media_content_id = f"{a['browseId']}",                 # noqa: E251
                        can_play = True,                                       # noqa: E251
                        can_expand = True,                                     # noqa: E251
                        thumbnail = find_thumbnail(a)                          # noqa: E251
                    ))
                elif(a['resultType'] == 'artist'):
                    _LOGGER.debug("a: %s", a)
                    children.append(BrowseMedia(
                        title = helper.get(a['resultType'], "") + a['artist'], # noqa: E251
                        media_class = MediaClass.ARTIST,                      # noqa: E251
                        media_content_type = MediaType.ARTIST,                # noqa: E251
                        media_content_id = f"{a['browseId']}",                 # noqa: E251
                        can_play = False,                                      # noqa: E251
                        can_expand = True,                                     # noqa: E251
                        thumbnail = find_thumbnail(a)                          # noqa: E251
                    ))
                else:  # video / artists / uploads are currently ignored
                    continue

        # _LOGGER.debug("search entry end")
    elif search_type == MediaType.ARTIST:
         media_all = await hass.async_add_executor_job(media_library.get_artist, search_id)
         helper = {'song': "Track: ", 'playlist': "Playlist: ", 'album': "Album: ", 'artist': "Artist"}

         if('singles' in media_all):
            for a in media_all['singles']['results']:
              children.append(BrowseMedia(
                  title = helper.get('song', "") + a['title'],           # noqa: E251
                  media_class = MediaClass.ALBUM,                       # noqa: E251
                  media_content_type = MediaType.ALBUM,                 # noqa: E251
                  media_content_id = a['browseId'],                      # noqa: E251
                  can_play = True,                                       # noqa: E251
                  can_expand = False,                                    # noqa: E251
                  thumbnail = find_thumbnail(a)                          # noqa: E251
              ))
         if('albums' in media_all):
            for a in media_all['albums']['results']:
              children.append(BrowseMedia(
                  title = helper.get('album', "") + a['title'],          # noqa: E251
                  media_class = MediaClass.ALBUM,                       # noqa: E251
                  media_content_type = MediaType.ALBUM,                 # noqa: E251
                  media_content_id = f"{a['browseId']}",                 # noqa: E251
                  can_play = True,                                       # noqa: E251
                  can_expand = True,                                     # noqa: E251
                  thumbnail = find_thumbnail(a)                          # noqa: E251
              ))

    elif search_type == MOOD_OVERVIEW:
        media_all = await hass.async_add_executor_job(lambda: media_library.get_mood_categories())
        title = MOOD_TITLE
        for cap in media_all:
            for e in media_all[cap]:
                children.append(BrowseMedia(
                    title = f"{cap} - {e['title']}",      # noqa: E251
                    media_class = MediaClass.PLAYLIST,   # noqa: E251
                    media_content_type = MOOD_PLAYLISTS,  # noqa: E251
                    media_content_id = e['params'],       # noqa: E251
                    can_play = False,                     # noqa: E251
                    can_expand = True,                    # noqa: E251
                    thumbnail = "",                       # noqa: E251
                ))
    elif search_type == MOOD_PLAYLISTS:
        media = await hass.async_add_executor_job(lambda: media_library.get_mood_playlists(search_id))
        title = MOOD_TITLE
        for item in media:
            children.append(BrowseMedia(
                title = f"{item['title']}",                  # noqa: E251
                media_class = MediaClass.PLAYLIST,          # noqa: E251
                media_content_type = MediaType.PLAYLIST,    # noqa: E251
                media_content_id = f"{item['playlistId']}",  # noqa: E251
                can_play = True,                             # noqa: E251
                can_expand = True,                           # noqa: E251
                thumbnail = find_thumbnail(item)             # noqa: E251
            ))
    elif search_type == CONF_RECEIVERS:
        title = PLAYER_TITLE
        for e, f in ytmusicplayer._friendly_speakersList.items():
            children.append(BrowseMedia(
                title = f,                            # noqa: E251
                media_class = MediaClass.TV_SHOW,    # noqa: E251
                media_content_type = CONF_RECEIVERS,  # noqa: E251
                media_content_id = e,                 # noqa: E251
                can_play = True,                      # noqa: E251
                can_expand = False,                   # noqa: E251
                thumbnail = "",                       # noqa: E251
            ))
    elif search_type == CUR_PLAYLIST:
        title = CUR_PLAYLIST_TITLE
        sort_list = False
        i = 1
        for item in ytmusicplayer._tracks:
            item_title = item["title"]
            if("artists" in item):
                artist = ""
                if(isinstance(item["artists"], str)):
                    artist = item["artists"]
                elif(isinstance(item["artists"], list)):
                    artist = item["artists"][0]["name"]
                if(artist):
                    item_title = artist + " - " + item_title

            children.append(BrowseMedia(
                title = item_title,                         # noqa: E251
                media_class = MediaClass.TRACK,            # noqa: E251
                media_content_type = CUR_PLAYLIST_COMMAND,  # noqa: E251
                media_content_id = i,                       # noqa: E251
                can_play = True,                            # noqa: E251
                can_expand = False,                         # noqa: E251
                thumbnail = find_thumbnail(item)            # noqa: E251
            ))
            i += 1

    elif search_type == ALBUM_OF_TRACK:
        try:
            res = await hass.async_add_executor_job(lambda: media_library.get_album(ytmusicplayer._track_album_id))
            sort_list = False
            media = res['tracks']
            title = res['title']

            for item in media:
                children.append(BrowseMedia(
                    title = f"{item['title']}",  # noqa: E251
                    media_class = MediaClass.TRACK,  # noqa: E251
                    media_content_type = MediaType.TRACK,  # noqa: E251
                    media_content_id = f"{item['videoId']}",  # noqa: E251
                    can_play = True,  # noqa: E251
                    can_expand = False,  # noqa: E251
                    thumbnail = find_thumbnail(item)             # noqa: E251
                ))
        except:
            pass


    # ########################################### END ###############
    if sort_list:
        children.sort(key=lambda x: x.title, reverse=False)
    response = BrowseMedia(
        media_class=CONTAINER_TYPES_SPECIFIC_MEDIA_CLASS.get(
            search_type, MediaClass.DIRECTORY
        ),
        media_content_id=search_id,
        media_content_type=search_type,
        title=title,
        can_play=search_type in PLAYABLE_MEDIA_TYPES and search_id,
        can_expand=True,
        children=children,
        thumbnail=thumbnail,
    )

    if search_type == "library_music":
        response.children_media_class = MediaClass.MUSIC
    elif len(children) > 0:
        response.calculate_children_class()
    t = (datetime.datetime.now() - p1).total_seconds()
    _LOGGER.debug("- Calc / grab time: " + str(t) + " sec")
    return response



def library_payload(ytmusicplayer):
    # Create response payload to describe contents of a specific library.
    # Used by async_browse_media.
    library_info = BrowseMedia(media_class=MediaClass.DIRECTORY, media_content_id="library", media_content_type="library", title="Media Library", can_play=False, can_expand=True, children=[])

    library_info.children.append(BrowseMedia(title=LIB_PLAYLIST_TITLE,   media_class=MediaClass.PLAYLIST, media_content_type=LIB_PLAYLIST,   media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=LIB_ALBUM_TITLE,      media_class=MediaClass.ALBUM,    media_content_type=LIB_ALBUM,      media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=LIB_TRACKS_TITLE,     media_class=MediaClass.TRACK,    media_content_type=LIB_TRACKS,     media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=HISTORY_TITLE,        media_class=MediaClass.TRACK,    media_content_type=HISTORY,        media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=USER_TRACKS_TITLE,    media_class=MediaClass.TRACK,    media_content_type=USER_TRACKS,    media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=USER_ALBUMS_TITLE,    media_class=MediaClass.ALBUM,    media_content_type=USER_ALBUMS,    media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=USER_ARTISTS_TITLE,   media_class=MediaClass.ARTIST,   media_content_type=USER_ARTISTS,   media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=USER_ARTISTS_2_TITLE, media_class=MediaClass.ARTIST,   media_content_type=USER_ARTISTS_2, media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=MOOD_TITLE,           media_class=MediaClass.PLAYLIST, media_content_type=MOOD_OVERVIEW,  media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=PLAYER_TITLE,         media_class=MediaClass.TV_SHOW,  media_content_type=CONF_RECEIVERS, media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241
    library_info.children.append(BrowseMedia(title=CUR_PLAYLIST_TITLE,   media_class=MediaClass.PLAYLIST, media_content_type=CUR_PLAYLIST,   media_content_id="", can_play=False, can_expand=True, thumbnail=""))  # noqa: E241

    # add search button if possible
    if(ytmusicplayer._search.get("query", "") != ""):
        library_info.children.append(
            BrowseMedia(title="Results for \"" + str(ytmusicplayer._search.get("query", "No search")) + "\"", media_class=MediaClass.DIRECTORY, media_content_type=SEARCH, media_content_id="", can_play=False, can_expand=True, thumbnail="")
        )

    # add "go to album of track" if possible
    if(ytmusicplayer._track_album_id not in ["", None] and ytmusicplayer._track_name not in ["", None]):
        library_info.children.append(
            BrowseMedia(title="Album of \"" + str(ytmusicplayer._track_name) + "\"", media_class=MediaClass.ALBUM, media_content_type=ALBUM_OF_TRACK, media_content_id="1", can_play=True, can_expand=True, thumbnail=ytmusicplayer._track_album_cover)
        )

    # add "radio of track" if possible
    if(ytmusicplayer._attributes['videoId'] != ""):
        library_info.children.append(
            BrowseMedia(title="Radio of \"" + str(ytmusicplayer._track_name) + "\"", media_class=MediaClass.PLAYLIST, media_content_type=CHANNEL_VID, media_content_id=ytmusicplayer._attributes['videoId'], can_play=True, can_expand=False, thumbnail="")
        )

    return library_info
