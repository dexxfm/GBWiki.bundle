import json
from HTMLParser import HTMLParser

def Start():
    pass


class GBWikiAgent(Agent.Movies):
    name = 'Giantbomb Games Wiki'
    languages = [Locale.Language.NoLanguage]
    primary_provider = True
    accepts_from = None
    contributes_to = None

    class Webparser(HTMLParser):
        def __init__(self):
            HTMLParser.__init__(self)
            self.data = []
            self.start_tags = []
            self.end_tags = []
            self.comments = []

        def handle_starttag(self, tag, attrs):
            self.start_tags.append(tag)

        def handle_endtag(self, tag):
            self.end_tags.append(tag)

        def handle_comment(self, data):
            self.comments.append(data)

        def handle_data(self, data):
            self.data.append(data)

    ####################################################################################################################
    # Plex Search and Update methods
    ####################################################################################################################

    def search(self, results, media, lang, manual):

        primary_metadata = None
        Log('Filepath: {}'.format(media.filename))
        file_path = media.filename.replace('%20', ' ')
        file_path = media.filename.replace('%2F', '/')
        file_path = file_path.replace('%2E', '.')
        file_location = file_path.split('/')
        game_name = file_location[(len(file_location)-2)]
        Log('File Location: {}'.format(file_location))
        Log('Game Name from File: {}'.format(game_name))

        # Giantbomb Wiki Lookup
        gb_base = 'https://www.giantbomb.com/api/search/?api_key={api}&format=json'.format(api=Prefs['api_key'])
        gb_search = '&query=' + game_name + '&resources=game&limit=1'
        gb_data = JSON.ObjectFromURL(gb_base + gb_search)

        # Compute the GUID based on the media hash.
        part = media.items[0].parts[0]
        Log('Game Name: {}'.format(gb_data['results'][0]['name']))
        Log('Game Year: {}'.format(gb_data['results'][0]['original_release_date'][:4]))
        game_year = gb_data['results'][0]['original_release_date'][:4]

        results.Append(MetadataSearchResult(
            id=part.hash,
            name=game_name.replace('%20', ' '),
            year=game_year,
            lang=lang,
            score=100,
            ))

    def update(self, metadata, media, lang):

        # Giantbomb Wiki Lookup
        gb_base = 'https://www.giantbomb.com/api/search/?api_key={api}&format=json'.format(api=Prefs['api_key'])
        gb_search = '&query=' + media.title.replace(' ', '%20') + '&resources=game&limit=1'
        gb_data = JSON.ObjectFromURL(gb_base + gb_search)
        game_posters = gb_data['results'][0]['image']['original_url']

        # Fill in metadata details
        # metadata.title = gb_data['results'][0]['name']
        metadata.year = Datetime.ParseDate(gb_data['results'][0]['original_release_date']).date().year
        tagline_html = self.Webparser()
        tagline_html.feed(gb_data['results'][0]['deck'])
        Log('\nTagline Parsed: {}\n\n'.format(''.join(tagline_html.data)))
        metadata.tagline = ''.join(tagline_html.data)

        if gb_data['results'][0]['description']:
            sum_html = self.Webparser()
            sum_html.feed(gb_data['results'][0]['description'])
            Log('\nSummary List Length: {}\n\n'.format(len(sum_html.data)))
            Log('\nSummary Parsed: {}\n\n'.format(''.join(sum_html.data)))
            try:
                sum_html.data.remove('Overview')
            except:
                pass
            metadata.summary = ''.join(sum_html.data)

        metadata.originally_available_at = Datetime.ParseDate(gb_data['results'][0]['original_release_date']).date()
        Log('\nDate: {}\n\n'.format(metadata.originally_available_at))

        # Pull data from image tags
        gb_images = gb_data['results'][0]['image_tags'][0]['api_detail_url'] + \
                    '&format=json&api_key={}'.format(Prefs['api_key'])
        gb_images_data = JSON.ObjectFromURL(gb_images)
        for art in gb_images_data['results']:
            art_url = art['original_url']

            try:
                metadata.art[art_url] = (Proxy.Preview(HTTP.Request(art_url).content))
            except:
                pass

        metadata.collections.clear()
        metadata.collections.add(media.title)
        # metadata.posters[game_posters] = Proxy.Preview(HTTP.Request(game_posters).content)
