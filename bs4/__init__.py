from html.parser import HTMLParser

class Tag(dict):
    def get(self, key, default=None):
        return self[key] if key in self else default

class BeautifulSoup(HTMLParser):
    def __init__(self, html, parser="html.parser"):
        super().__init__()
        self.tags = []
        self.text_parts = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    def handle_data(self, data):
        self.text_parts.append(data)

    def find_all(self, tag, href=False):
        results = []
        for t, attrs in self.tags:
            if t == tag and (not href or "href" in attrs):
                results.append(Tag(attrs))
        return results

    def get_text(self, separator=" "):
        return separator.join(self.text_parts)
