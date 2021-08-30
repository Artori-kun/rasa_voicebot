from bs4 import BeautifulSoup
import requests
import re
import unicodedata
from difflib import SequenceMatcher


class NewsExtractor:
    def __init__(self):
        self.user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) " \
                          "Chrome/92.0.4515.159 Safari/537.36 "
        self._base_url = "https://vietnamnet.vn"

    @property
    def base_url(self):
        return self._base_url

    @staticmethod
    def clean_the_fucking_text(text):
        characters_need_to_eliminate_regex = re.compile(r'[•\-+():\n]')
        # slashes_need_to_interpret_regex = re.compile(r'((\d+/\d+)|(\w+/\d+)|(\d+/\w+)|(\w+/\w+))')
        dots_need_to_interpret_regex = re.compile(r'(\d+.\d+)')
        time_regex = re.compile(r'((2[0-4]|[0-1][0-9]|[0-9]):([0-5][0-9]|[1-9]))')
        date_regex = re.compile(r'\b((3[0-1]|[1-2][0-9]|0[1-9])[/-](1[0-2]|0[1-9]|[1-9])[/-](\d{4}|\d{2}))|((3[0-1]|['
                                r'0-2][0-9]|[1-9])[/-](1[0-2]|0[1-9]|[1-9]))\b')

        # date_regex_without_year = re.compile(r'((3[0-1]|[0-2][0-9]|[1-9])[/-](1[0-2]|0[1-9]|[1-9]))')

        # for match in re.finditer(special_html_characters_regex, text):
        #     text.replace(match.group(0), ' ')
        text = unicodedata.normalize("NFKD", text)

        for match in re.finditer(time_regex, text):
            time_text = match.group(0)
            time_text = time_text.split(':')
            time_text = time_text[0] + ' giờ ' + time_text[1]

            text = text.replace(match.group(0), time_text)

        for match in re.finditer(date_regex, text):
            # print(match.group(0))
            date_text = match.group(0)

            if len(date_text.split('/')) == 1:
                date_text = date_text.split('-')
            else:
                date_text = date_text.split('/')

            if date_text[0].startswith('0'):
                date_text[0] = date_text[0][1:]
            if date_text[1].startswith('0'):
                date_text[1] = date_text[1][1:]

            if len(date_text) == 2:
                date_text = date_text[0] + ' tháng ' + date_text[1]
            else:
                date_text = date_text[0] + ' tháng ' + date_text[1] + ' năm ' + date_text[2]

            # print(date_text)
            text = text.replace(match.group(0), date_text)

        for match in re.finditer(dots_need_to_interpret_regex, text):
            text = text.replace(match.group(0), match.group(0).replace('.', ''))

        text = text.replace('/', ' trên ')

        # text = text.replace('\n', ' ')

        text = re.sub(characters_need_to_eliminate_regex, '', text)

        return text

    def get_headline(self, category='', subcategory=''):
        header = {"User-Agent": self.user_agent}

        response = requests.get(f"{self.base_url}/vn/{category}/{subcategory}", headers=header)
        # content = response.content
        result = {}

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        for a in soup.findAll("a", {"class": ["f-20 d-b title", "title f-n SubString50", "f-18 title"]}):
            result[a.get_text()] = a['href']

        return result

    def get_latest_headline(self):
        header = {"User-Agent": self.user_agent}

        response = requests.get(f"{self.base_url}/vn/tin-moi-nong", headers=header)

        result = {}

        if response.status_code >= 300:
            print(response.status_code)
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        for a in soup.findAll("h3", {"class": ["box-subcate-style3-title",
                                               "box-subcate-style4-title",
                                               "f-16 p-l-20 r-20"]}):
            a = a.find('a')
            result[a.get_text()] = a["href"]

        return result

    def get_article(self, slug):
        response = requests.get(self.base_url + slug, headers={"User-Agent": self.user_agent})

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        article_content = soup.find('div', {"class": "ArticleContent"})

        content_text = ''

        for p in article_content.find_all('p'):
            content_text += ' ' + p.get_text(strip=True)

        return self.clean_the_fucking_text(content_text)

    def get_general_covid_info(self):
        header = {"User-Agent": self.user_agent}

        response = requests.get("https://ncov.moh.gov.vn/web/guest/trang-chu", headers=header, verify=False)

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser').find_all('div', {"class": "row mt-5"})

        vietnam = soup[0]
        world = soup[1]

        vietnam = vietnam.find_all('span', {"class": "font24"})
        world = world.find_all('span', {"class": "font24"})

        vietnam_result = {"cases": vietnam[0].get_text(),
                          "on-treatment": vietnam[1].get_text(),
                          "cured": vietnam[2].get_text(),
                          "death": vietnam[3].get_text()}

        world_result = {"cases": world[0].get_text(),
                        "on-treatment": world[1].get_text(),
                        "cured": world[2].get_text(),
                        "death": world[3].get_text()}

        return {"Vietnam": vietnam_result,
                "World": world_result}

    def get_province_covid_info(self, province):
        header = {"User-Agent": self.user_agent}

        response = requests.get("https://ncov.moh.gov.vn/web/guest/trang-chu", headers=header, verify=False)

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser').find('table', {"id": "sailorTable"})

        for r in soup.find_all('tr', {"style": "font-weight: 600"}):
            r = r.find_all('td')

            s = SequenceMatcher(None, r[0].get_text().lowercase(), province)

            if s.ratio() > 0.85:
                result = {"cases": r[1].get_text(),
                          "latest": r[2].get_text().strip('+'),
                          "death": r[3].get_text()}

                return result

        return None

    def get_covid_timeline(self):
        header = {"User-Agent": self.user_agent}

        response = requests.get("https://ncov.moh.gov.vn/dong-thoi-gian", headers=header, verify=False)

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser').find('div', {"class": "timeline-detail"})

        timestamp = soup.find('div', {"class": "timeline-head"}).find('h3').get_text()

        timeline = soup.find('div', {"class": "timeline-content"}).find_all('p')

        timeline = ' '.join(p.get_text() for p in timeline)

        return {"timestamp": self.clean_the_fucking_text(timestamp),
                "timeline": self.clean_the_fucking_text(timeline)}

    def get_covid_headline(self):
        header = {"User-Agent": self.user_agent}

        response = requests.get(self.base_url + "/interactive/covid-19/index.html", headers=header, verify=False)

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        result = {}

        hot_headlines = soup.find_all('a', {"class": "title-content text-white title-articletype_1"})

        for a in hot_headlines:
            result[a.get_text()] = a["href"]

        other_headlines = soup.find_all('div', {"class": "row m-0 p-3 "})

        for div in other_headlines:
            result[div.find('h5').find('a').get_text()] = div.find('h5').find('a')["href"]

        return result
