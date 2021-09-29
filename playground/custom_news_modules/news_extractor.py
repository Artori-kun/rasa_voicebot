from bs4 import BeautifulSoup
import requests
import re
import unicodedata
from difflib import SequenceMatcher
import json
from requests_html import HTMLSession


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
        characters_need_to_eliminate_regex = re.compile(r'[•\-+():]')
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

    def get_headline(self, category):
        with open('custom_news_modules/category.json', 'r', encoding='utf-8') as fr:
            categories_dict = json.load(fr)

        slug = categories_dict[category]
        header = {"User-Agent": self.user_agent}

        response = requests.get(self.base_url + slug, headers=header)
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
        if self.base_url in slug:
            response = requests.get(slug, headers={"User-Agent": self.user_agent})
        else:
            response = requests.get(self.base_url + slug, headers={"User-Agent": self.user_agent})

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        article_content = soup.find('div', {"class": "ArticleContent"})

        content_text = ''

        for p in article_content.find_all('p'):
            content_text += ' ' + p.get_text(strip=True)

        return self.clean_the_fucking_text(content_text)

    def get_general_covid_info_vn(self):
        header = {"User-Agent": self.user_agent}

        response = requests.get("https://vietnamnet.vn/interactive/covid-19/viet-nam.html", headers=header,
                                verify=False)

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        general_stat = soup.find('div', {"class": "row data"}).find_all('span')

        vietnam_result = {"cases": general_stat[0].get_text(),
                          "death": general_stat[2].get_text(),
                          "cured": general_stat[3].get_text()}

        new_stat = soup.find('div', {"class": "col col-md-2"}).find('span')
        vietnam_result["new-cases"] = new_stat.get_text().strip('+')

        return vietnam_result

    def get_general_covid_info_world(self):
        header = {"User-Agent": self.user_agent}

        response = requests.get("https://vietnamnet.vn/interactive/covid-19/the-gioi.html", headers=header,
                                verify=False)

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser')

        general_stat = soup.find('div', {"row data"}).find_all('span')

        world_result = {"cases": general_stat[0].get_text(),
                        "death": general_stat[2].get_text(),
                        "cured": general_stat[3].get_text()}

        return world_result

    def get_province_covid_info(self, province):
        header = {"User-Agent": self.user_agent}

        response = requests.get("https://vietnamnet.vn/interactive/covid-19/viet-nam.html", headers=header,
                                verify=False)

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser') \
            .find('tbody', {"id": "tbody-sparkline"})

        for r in soup.find_all('tr'):
            province_tag = r.find_all('th')

            s = SequenceMatcher(None, province_tag.get_text().lower(), province)
            print(s.ratio())

            if s.ratio() > 0.8:
                stat = r.find_all('td')
                result = {"new-cases": stat[0].get_text().strip('+'),
                          "cases": stat[1].get_text()}

                return result

        return None

    def get_covid_timeline(self):
        header = {"User-Agent": self.user_agent}

        response = requests.get("https://covid19.gov.vn/", headers=header, verify=False)

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser') \
            .find('div', {"class": "home__focus-position"}) \
            .find('div', {"class": "item active"})

        timestamp = soup.find('p', {"class": "time"}).get_text()

        timeline_title = soup.find('span', {"class": "box-focus-link-title"}).get_text()

        timeline = soup.find('div', {"class": "box-focus-sapo"}).find_all('p')

        timeline = timeline_title + '\n' + ' '.join(p.get_text() for p in timeline)

        return {"timestamp": self.clean_the_fucking_text(timestamp),
                "timeline": self.clean_the_fucking_text(timeline)}

    def get_covid_headline(self):
        session = HTMLSession()
        response = session.get(self.base_url + "/interactive/covid-19/index.html")
        response.html.render()

        # header = {"User-Agent": self.user_agent}
        #
        # response = requests.get(self.base_url + "/interactive/covid-19/index.html", headers=header, verify=False)
        #
        # if response.status_code >= 300:
        #     return None

        soup = BeautifulSoup(response, 'html.parser')

        result = {}

        hot_headlines = soup.find_all('a', {"class": "title-content text-white title-articletype_1"})

        for a in hot_headlines:
            result[a.get_text()] = a["href"]

        other_headlines = soup.find_all('div', {"class": "row m-0 p-3 "})

        for div in other_headlines:
            result[div.find('h5').find('a').get_text()] = div.find('h5').find('a')["href"]

        return result
