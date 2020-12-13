# coding: utf-8
from __future__ import unicode_literals

from .common import InfoExtractor
from ..utils import int_or_none


class Zee5BaseIE(InfoExtractor):
    def _call_api(self, path, video_id):
        # Get x-access-token
        access_token = self._download_json(
            "https://useraction.zee5.com/token/platform_tokens.php?platform_name=web_app",
            video_id=video_id,
            note='Downloading token',
            errnote='Unable to download token')['token']

        # Download metadata
        return self._download_json(
            'https://gwapi.zee5.com/content/details/' + path,
            video_id=video_id,
            headers={
                "User-Agent":
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
                "X-Access-Token": access_token
            })

    def _get_m3u8_url(self, meta, video_id):
        video_token = self._download_json(
            "https://useraction.zee5.com/tokennd",
            video_id,
            note='Downloading video token',
            errnote='Unable to download video token')['video_token']
        return 'https://zee5vodnd.akamaized.net/' + meta['hls'][0].replace(
            'drm', 'hls') + video_token


class Zee5IE(Zee5BaseIE):
    _VALID_URL = r"""(?x)
        https?://(?:www\.)?zee5\.com/
            (?:movies/details|(?:tvshows/details|kids/kids-shows)/[\w-]+/[\d-]+)
        /[\w-]+/(?P<id>[\w-]+)"""

    def _real_extract(self, url):
        video_id = self._match_id(url)
        meta = self._call_api(video_id + '?translation=en', video_id)
        m3u8_url = self._get_m3u8_url(meta, video_id)
        formats = self._extract_m3u8_formats(m3u8_url, video_id, 'mp4')
        self._sort_formats(formats)

        return {
            'id': video_id,
            'title': meta['title'],
            'description': meta.get('description'),
            'thumbnail': meta.get('image_url'),
            'url': 'https://www.zee5.com/' + meta.get('web_url'),
            'rating': int_or_none(meta.get('rating')),
            'duration': int_or_none(meta.get('duration')),
            'formats': formats,
            'ext': 'mp4',
        }


class Zee5PlaylistIE(Zee5BaseIE):
    _VALID_URL = r"https?://(?:www\.)?zee5\.com/(?:tvshows/details|kids/kids-shows)/[\w-]+/(?P<id>[\d-]+)/?$"

    def _format_episode(self, episode):
        return self.url_result('https://www.zee5.com/' + episode['web_url'],
                               video_id=episode.get('id'),
                               video_title=episode.get('title'))

    def _real_extract(self, url):
        base_url = 'https://gwapi.zee5.com/content/tvshow/'
        playlist_id = self._match_id(url)

        access_token = self._download_json(
            "https://useraction.zee5.com/token/platform_tokens.php?platform_name=web_app",
            video_id=playlist_id,
            note='Downloading token',
            errnote='Unable to download token')['token']

        headers = {
            "User-Agent":
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.66 Safari/537.36",
            "X-Access-Token": access_token
        }

        meta = self._download_json(
            base_url + playlist_id + '?translation=en&limit=1',
            playlist_id,
            headers=headers)

        page_number = 1
        entries = []
        season = meta['seasons'][0]
        season_id = season['id']
        total_episodes = season['total_episodes']

        while len(entries) < total_episodes:
            url = base_url + '?season_id=%s&type=episode&translation=en&on_air=false&page=%d&limit=100' % (
                season_id, page_number)
            data = self._download_json(
                url,
                playlist_id,
                note='Downloading playlist page: %d' % page_number,
                errnote='Failed to download playlist page: %d' % page_number,
                headers=headers)

            entries.extend(
                [self._format_episode(episode) for episode in data['episode']])
            page_number += 1

        return self.playlist_result(
            entries,
            playlist_id,
            playlist_title=meta.get('title'),
            playlist_description=meta.get('description'))
