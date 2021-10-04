import re
import pytz
import datetime
import string
import json
import calendar
import numpy as np

# REGEX
from dateutil.relativedelta import relativedelta

# REGEX_DATE = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|](1[0-2]|0?[1-9])[-\/:|](\d{4})"
# REGEX_DAY_MONTH = r"(3[01]|[12][0-9]|0?[1-9])[-\/:|](1[0-2]|0?[1-9])"
# REGEX_MONTH_YEAR = r"(1[0-2]|0?[1-9])[-\/:|](\d{4})"

REGEX_DATE = r"(ngày|mùng)\s(3[01]|[12][0-9]|[1-9])\s(tháng)\s(1[0-2]|[1-9])\s(năm)\s(\d{4}|\d{2})"
REGEX_DAY_MONTH = r"(ngày|mùng)\s(3[01]|[12][0-9]|[1-9])\s(tháng)\s(1[0-2]|[1-9])"
REGEX_MONTH_YEAR = r"(tháng)\s(1[0-2]|[1-9])\s(năm)\s(\d{4}|\d{2})"
REGEX_TIME = re.compile(r"(2[0-4]|1[0-9]|[0-9])\s(giờ)(\s([0-5][0-9]|[1-9])(\sphút)?)?")
REGEX_TIME_PM = re.compile(r"(([1-5])\s(giờ)(\s([1-9]|[0-5][0-9])(\sphút)?)?\s(chiều))|"
                           r"((10|[6-9])\s(giờ)(\s([1-9]|[0-5][0-9])(\sphút)?)?\s(tối))|"
                           r"((1[1-2])\s(giờ)(\s([1-9]|[0-5][0-9])(\sphút)?)?\s(đêm))")
REGEX_RECURRENCE = re.compile(r"\d+\s(ngày|tuần|tháng|năm)")
REGEX_RECURRENCE_SINGLE = re.compile(r"(hàng|mỗi)\s(ngày|tuần|tháng|năm)")


def regex_time(msg):
    # print("start")
    time_str = []
    count = 0

    """search for PM time"""
    for _ in re.finditer(REGEX_TIME_PM, msg):
        count += 1
    # print(len(tuple(matches)))

    if count != 0:
        # print("PM not none")
        for match in re.finditer(REGEX_TIME_PM, msg):
            time = match.group(0)
            # print(time)
            time = re.findall(r"\d+", time)

            time[0] = str(int(time[0]) + 12)

            if len(time) == 1:
                time.append("00")
            if len(time[1]) == 1:
                time[1] = "0" + time[1]
            t_str = ':'.join(time)
            time_str.append(t_str)
    else:
        # print(msg)
        count = 0
        for _ in re.finditer(REGEX_TIME, msg):
            count += 1
        # print(matches)
        # print(len(tuple(matches)))
        if count != 0:
            for match in re.finditer(REGEX_TIME, msg):
                time = match.group(0)
                # print(time)
                time = re.findall(r"\d+", time)
                if len(time) == 1:
                    time.append("00")
                if len(time[0]) == 1:
                    time[0] = '0' + time[0]
                if len(time[1]) == 1:
                    time[1] = "0" + time[1]
                t_str = ':'.join(time)
                time_str.append(t_str)

    return time_str


def regex_recurrence(msg):
    recurrence_type = None
    separation_count = 1
    count = 0
    for _ in re.finditer(REGEX_RECURRENCE_SINGLE, msg):
        count += 1

    if count != 0:
        # separation_count = 1
        for match in re.finditer(REGEX_RECURRENCE_SINGLE, msg):
            recurrence_type = match.group(0)
    else:
        for _ in re.finditer(REGEX_RECURRENCE, msg):
            count += 1
        if count != 0:
            for match in re.finditer(REGEX_RECURRENCE, msg):
                recurrence = match.group(0)

                separation_count = int(recurrence.split()[0])

                recurrence_type = recurrence.split()[1]

    if 'ngày' in recurrence_type:
        recurrence_type = 'daily'
    elif 'tuần' in recurrence_type:
        recurrence_type = 'weekly'
    elif 'tháng' in recurrence_type:
        recurrence_type = 'monthly'
    elif 'năm' in recurrence_type:
        recurrence_type = 'yearly'

    return recurrence_type, separation_count


def regex_date(msg, timezone="Asia/Ho_Chi_Minh"):
    """ use regex to capture date string format """

    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz)

    date_str = []
    regex = REGEX_DATE
    regex_day_month = REGEX_DAY_MONTH
    regex_month_year = REGEX_MONTH_YEAR
    pattern = re.compile("(%s|%s|%s)" % (
        regex, regex_month_year, regex_day_month), re.UNICODE)

    matches = pattern.finditer(msg)
    for match in matches:
        _dt = match.group(0)
        numbers = re.findall(r"\d+", _dt)
        _dt = '-'.join(numbers)
        # _dt = _dt.replace("/", "-").replace("|", "-").replace(":", "-")
        for i in range(len(_dt.split("-"))):
            if len(_dt.split("-")[i]) == 1:
                _dt = _dt.replace(_dt.split("-")[i], "0" + _dt.split("-")[i])
        if len(_dt.split("-")) == 2:
            pos1 = _dt.split("-")[0]
            pos2 = _dt.split("-")[1]
            if 0 < int(pos1) < 32 and 0 < int(pos2) < 13:
                _dt = pos1 + "-" + pos2 + "-" + str(now.year)
        date_str.append(_dt)
    return date_str


def preprocess_msg(msg):
    """ return a list of character of messenger without punctuation"""

    msg = msg.lower()
    special_punc = string.punctuation
    for punc in "-+/:|":
        special_punc = special_punc.replace(punc, '')
    msg = ''.join(c for c in msg if c not in special_punc)

    """ convert string to numbers """
    with open("custom_date_extractor/number_str.json", "r", encoding="utf8") as fr:
        number_str = json.load(fr)

    n_grams = (8, 7, 6, 5, 4, 3, 2, 1)
    i = 0
    words = msg.split()

    while i < len(words):
        for n_gram in n_grams:
            token = ' '.join(words[i:i + n_gram])
            if token in number_str.keys():
                msg = msg.replace(token, str(number_str[token]))
                words = msg.split()
                i = 0
        i += 1

    """ remove white space between 2 numbers after the word "năm" """
    pos = msg.find("năm")
    if pos != -1:
        str_contain_year = msg[pos:]
        pattern = re.compile(r"(\d+\s\d+)")
        y = re.search(pattern, str_contain_year)

        while y is not None:
            y = y.group()
            msg = msg.replace(y, y.replace(' ', ''))
            str_contain_year = str_contain_year.replace(y, y.replace(' ', ''))
            y = re.search(pattern, str_contain_year)

    return msg


def tokenize(msg):
    """ extract date in messenger by matching in synonyms.json """

    def remove_token(words, token):
        tok = token.split(" ")
        for t in tok:
            words.remove(t)
        return words

    with open("custom_date_extractor/synonyms.json", "r", encoding="utf8") as fr:
        data = json.load(fr)

    with open("custom_date_extractor/number_str.json", "r", encoding="utf8") as fr:
        number_str = json.load(fr)

    words = msg.split()

    tokens = []
    n_grams = (8, 7, 6, 5, 4, 3, 2, 1)
    i = 0
    w, W = None, None

    while i < len(words):
        has_gram = False
        token = None
        for n_gram in n_grams:
            token = ' '.join(words[i:i + n_gram])
            if token in data.keys():
                w = words[i - 1] if i > 0 else ''
                W = words[i + n_gram] if i < len(words) - n_gram else ''
                # i += n_gram
                has_gram = True
                break
        if has_gram is False:
            token = words[i]
            i += 1
        if token in data.keys():
            if data[token] in ["daysago", "nextday", "lastweek", "nextweek", "lastmonth", "nextmonth", "lastyear",
                               "nextyear"]:
                if w in number_str.keys():
                    tokens.append({data[token]: number_str[w] + " " + token})
                    words.remove(w)
                    words = remove_token(words=words, token=token)
                elif w.isnumeric():
                    tokens.append({data[token]: w + " " + token})
                    words.remove(w)
                    words = remove_token(words=words, token=token)
                else:
                    tokens.append({data[token]: token})
                    words = remove_token(words=words, token=token)
                continue
            if data[token] in ["week", "year", "day", "month"]:
                if W in number_str.keys():
                    tokens.append({data[token]: token + " " + number_str[W]})
                    words = remove_token(words=words, token=token)
                    words.remove(W)
                elif W.isnumeric():
                    tokens.append({data[token]: token + " " + W})
                    words = remove_token(words=words, token=token)
                    words.remove(W)
                else:
                    tokens.append({data[token]: token})
                    words = remove_token(words=words, token=token)
                continue

            tokens.append({data[token]: token})
            words = remove_token(words=words, token=token)
    return tokens


def cluster_tokens(tokens):
    date_tokens, weekday_tokens, day_month_year_tokens = [], [], []
    for tok in tokens:
        if list(tok.keys())[0] in ["today", "beforeyesterday", "aftertomorrow", "daysago", "nextday"]:
            date_tokens.append(tok)
        elif "weekday" in list(tok.keys())[0] or list(tok.keys())[0] in ["week", "lastweek", "nextweek"]:
            weekday_tokens.append(tok)
        else:
            day_month_year_tokens.append(tok)

    return date_tokens, weekday_tokens, day_month_year_tokens


def get_date(tokens, timezone='Asia/Ho_Chi_Minh'):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz).date()
    dates = []

    for token in tokens:
        tok_key = list(token.keys())[0]
        tok_value = list(token.values())[0]
        date = now
        if tok_key == "today":
            date = now
        if tok_key == "beforeyesterday":
            date = now + datetime.timedelta(days=-2)
        if tok_key == "aftertomorrow":
            date = now + datetime.timedelta(days=2)
        if tok_key == "daysago":
            if tok_value.split()[0].isnumeric():
                num_days = -int(tok_value.split()[0])
                date = now + datetime.timedelta(days=num_days)
            else:
                date = now + datetime.timedelta(days=(-1))
        if tok_key == "nextday":
            if tok_value.split()[0].isnumeric():
                num_days = int(tok_value.split()[0])
                date = now + datetime.timedelta(days=num_days)
            else:
                date = now + datetime.timedelta(days=1)
        dates.append(date.strftime("%d-%m-%Y"))
    return dates


def get_day_month_year(tokens, timezone='Asia/Ho_Chi_Minh'):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz).date()
    day_month_years = []

    for i in range(0, len(tokens)):
        day_tok_key = list(tokens[i].keys())[0]
        day_tok_value = list(tokens[i].values())[0]
        if "day" in day_tok_key or day_tok_key == "endmonth":
            day = int(day_tok_key.split("day")[1])
            if day_tok_key == "endmonth":
                day = calendar.monthrange(now.year, now.month)[1]
            month = now.month
            year = now.year
            for j in range(i + 1, len(tokens)):
                month_tok_key = list(tokens[j].keys())[0]
                month_tok_value = list(tokens[j].values())[0]
                if "month" in month_tok_key and month_tok_key != "endmonth":
                    if month_tok_key.startswith("month"):
                        month = int(month_tok_key.split("month")[1])
                        for k in range(j + 1, len(tokens)):
                            year_tok_key = list(tokens[k].keys())[0]
                            year_tok_value = list(tokens[k].values())[0]
                            if "year" in year_tok_key:
                                if year_tok_key == "year":
                                    year = int(year_tok_value.split()[-1])
                                    break
                                if year_tok_key == "nextyear":
                                    if year_tok_value.split()[0].isnumeric():
                                        num_year = int(
                                            year_tok_value.split()[0])
                                        year = (
                                                now + relativedelta(years=num_year)).year
                                    else:
                                        year = now.year + 1
                                    break
                                if year_tok_key == "lastyear":
                                    if year_tok_value.split()[0].isnumeric():
                                        num_year = - \
                                            int(year_tok_value.split()[0])
                                        year = (
                                                now + relativedelta(years=num_year)).year
                                    else:
                                        year = now.year - 1
                                    break
                        break
                    if month_tok_key == "nextmonth":
                        if month_tok_value.split()[0].isnumeric():
                            num_month = int(month_tok_value.split()[0])
                            month = (
                                    now + relativedelta(months=num_month)).month
                            year = (now + relativedelta(months=num_month)).year
                        else:
                            month = now.month + 1
                        break
                    if month_tok_key == "lastmonth":
                        if month_tok_value.split()[0].isnumeric():
                            num_month = -int(month_tok_value.split()[0])
                            month = (now + relativedelta(months=num_month)).month
                            year = (now + relativedelta(months=num_month)).year
                        else:
                            month = now.month - 1
                        break
            date = datetime.date(int(year), int(month), int(day))
            day_month_years.append(date.strftime("%d-%m-%Y"))
    return day_month_years


def get_weekday_week(tokens, week_now, timezone='Asia/Ho_Chi_Minh'):
    tz = pytz.timezone(timezone)
    now = datetime.datetime.now(tz=tz).date()
    weekday_now = now.weekday() + 2
    weekday_weeks = []
    week_day = 0
    for i in range(0, len(tokens)):
        tok_key = list(tokens[i].keys())[0]
        tok_value = list(tokens[i].values())[0]
        num_week = 0
        if "weekday" in tok_key:
            week_day = int(tok_key.split("weekday")[1])
            for j in range(i + 1, len(tokens)):
                week_tok_key = list(tokens[j].keys())[0]
                week_tok_value = list(tokens[j].values())[0]
                if week_tok_key == "week":
                    week = int(week_tok_value.split()[-1])
                    num_week = week - week_now
                    break
                if week_tok_key == "nextweek":
                    if week_tok_value.split()[0].isnumeric():
                        num_week = int(week_tok_value.split()[0])
                    else:
                        num_week = 1
                    break
                if week_tok_key == "lastweek":
                    if week_tok_value.split()[0].isnumeric():
                        num_week = -int(week_tok_value.split()[0])
                    else:
                        num_week = -1
                    break
            date = now + datetime.timedelta(weeks=num_week) + datetime.timedelta(days=week_day - weekday_now)
            weekday_weeks.append(date.strftime("%d-%m-%Y"))

        else:
            if tok_key == "week":
                week = int(tok_value.split()[-1])
                num_week = week - week_now
            if tok_key == "nextweek":
                if tok_value.split()[0].isnumeric():
                    num_week = int(tok_value.split()[0])
                else:
                    num_week = 1
            if tok_key == "lastweek":
                if tok_value.split()[0].isnumeric():
                    num_week = -int(tok_value.split()[0])
                else:
                    num_week = -1
            if week_day == 0:
                week = [(now + datetime.timedelta(weeks=num_week) + datetime.timedelta(days=2 - weekday_now)).strftime(
                    "%d-%m-%Y"),
                    (now + datetime.timedelta(weeks=num_week) + datetime.timedelta(days=8 - weekday_now)).strftime(
                        "%d-%m-%Y")]
                weekday_weeks.append(week)
            else:
                date = now + \
                       datetime.timedelta(weeks=num_week) + \
                       datetime.timedelta(days=week_day - weekday_now)
                weekday_weeks.append(date.strftime("%d-%m-%Y"))

    return weekday_weeks


def summary_date(message):
    message = preprocess_msg(message)
    dates = regex_date(message)
    tokens = tokenize(message)
    date_tokens, weekday_week_tokens, day_month_year_tokens = cluster_tokens(
        tokens=tokens)
    dates.extend(get_date(tokens=date_tokens))
    dates.extend(get_day_month_year(tokens=day_month_year_tokens))
    dates.extend(get_weekday_week(tokens=weekday_week_tokens, week_now=36))

    dates = np.array(dates)

    return list(np.unique(dates))


def summary_time(message):
    message = preprocess_msg(message)

    times = regex_time(message)
    times = np.array(times)

    return list(np.unique(times))


def summary_recurrence(message):
    message = preprocess_msg(message)
    recurrence_type, separation_count = regex_recurrence(message)

    return recurrence_type, separation_count
