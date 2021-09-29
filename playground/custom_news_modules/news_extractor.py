from bs4 import BeautifulSoup
import requests
import re
import unicodedata
from difflib import SequenceMatcher
import json
import time


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
        text.strip()
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
        header = {"User-Agent": self.user_agent,
                  "Referer": "https://covid19.gov.vn"}

        response = requests.get("https://static.pipezero.com/covid/data.json", headers=header)

        if response.status_code >= 300:
            return None

        data = response.json()

        vietnam_result = {"cases": data["total"]["internal"]["cases"],
                          "death": data["total"]["internal"]["death"],
                          "recovered": data["total"]["internal"]["recovered"],
                          "treating": data["total"]["internal"]["treating"],
                          "new-cases": data["today"]["internal"]["cases"]}

        return vietnam_result

    def get_general_covid_info_world(self):
        header = {"User-Agent": self.user_agent,
                  "Referer": "https://covid19.gov.vn"}

        response = requests.get("https://static.pipezero.com/covid/data.json", headers=header)

        if response.status_code >= 300:
            return None

        data = response.json()

        world_result = {"cases": data["total"]["world"]["cases"],
                        "death": data["total"]["world"]["death"],
                        "new-cases": data["today"]["world"]["cases"]}

        return world_result

    def get_province_covid_info(self, province):
        header = {"User-Agent": self.user_agent,
                  "Referer": "https://covid19.gov.vn"}

        response = requests.get("https://static.pipezero.com/covid/data.json", headers=header)

        if response.status_code >= 300:
            return None

        data = response.json()

        for r in data["locations"]:

            s = SequenceMatcher(None, r["name"].lower(), province)
            # print(s.ratio())

            if s.ratio() > 0.8:
                result = {"new-cases": r["casesToday"],
                          "cases": r["cases"],
                          "death": r["death"]}

                return result

        return None

    def get_covid_timeline(self):

        header = {"User-Agent": self.user_agent,
                  "Referer": "https://covid19.gov.vn"}

        response = requests.get("https://covid19.gov.vn/ajax/dien-bien-dich.htm", headers=header)

        if response.status_code >= 300:
            return None

        soup = BeautifulSoup(response.content, 'html.parser') \
            .find('div', {"class": "swiper-slide", "data-index": "0"})

        timestamp = soup.find('p', {"class": "time"}).get_text()

        timeline_title = soup.find('span', {"class": "box-focus-link-title"}).get_text()

        timeline = soup.find('div', {"class": "box-focus-sapo"}).find_all('p')

        timeline = timeline_title + '\n' + ' '.join(p.get_text() for p in timeline)

        return {"timestamp": self.clean_the_fucking_text(timestamp),
                "timeline": self.clean_the_fucking_text(timeline)}

    def get_covid_headline(self):
        def convert_to_proper_json(text):
            text = text.replace("=", ":")
            text = text.replace("retvar", "\"retvar\"")
            text = "{" + text + "}"

            fw = open("custom_news_modules/stupid_response.json", "w", encoding="utf-8")
            fw.write(text)
            fw.close()

            fr = open("custom_news_modules/stupid_response.json", "r", encoding="utf-8")
            data = json.load(fr)

            return data

        header = {"User-Agent": self.user_agent,
                  "Referer": "https://vietnamnet.vn/interactive/covid-19/index.html"}

        response_main = requests.get("https://vietnamnet.vn/jsx/loadmore/?domain=desktop&c=covid-19&p=1&s=5&a=0",
                                     headers=header)

        response_sub = requests.get(" https://vietnamnet.vn/jsx/loadmore/?domain=desktop&c=covid-19&p=1&s=20&a=5",
                                    headers=header)

        if response_main.status_code >= 300 or response_sub.status_code >= 300:
            return None

        result = {}

        data_main = convert_to_proper_json(response_main.text)
        data_sub = convert_to_proper_json(response_sub.text)

        for r in data_main["retvar"]:
            result[r["title"]] = r["link"].replace("http://vietnamnet.vn", "")

        for r in data_sub["retvar"]:
            result[r["title"]] = r["link"].replace("http://vietnamnet.vn", "")

        return result
