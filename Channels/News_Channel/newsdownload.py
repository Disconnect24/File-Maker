#!/usr/bin/python3
# -*- coding: utf-8 -*-

# ===========================================================================
# NEWS CHANNEL GENERATION SCRIPT
# AUTHORS: LARSEN VALLECILLO
# ****************************************************************************
# Copyright (c) 2015-2018 RiiConnect24, and it's (Lead) Developers
# ===========================================================================

import binascii
import collections
import json
import textwrap
import time
from io import BytesIO
from datetime import datetime

import googlemaps
import newspaper
import requests
from PIL import Image
from bs4 import BeautifulSoup
from unidecode import unidecode
from simplejson.errors import JSONDecodeError
from utils import setup_log, log, u8, u16, u32, u32_littleendian, enc

with open("./Channels/News_Channel/config.json", "rb") as f:
    config = json.load(f)

if config["production"]: setup_log(config["sentry_url"], True)


"""Resize the image and strip metadata (to make the image size smaller)."""

def shrink_image(data, resize, source):
    if data == "" or data is None: return None

    picture = requests.get(data).content
    try:
        image = Image.open(BytesIO(picture))
    except IOError:
        return None

    maxsize = (200, 200)

    """If for some reason the image has an alpha channel (probably a PNG), fill the background with white."""

    image = image.convert("RGB")

    if resize: image.thumbnail(maxsize, Image.ANTIALIAS)

    data = list(image.getdata())
    image_without_exif = Image.new(image.mode, image.size)
    image_without_exif.putdata(data)

    buffer = BytesIO()
    image_without_exif.save(buffer, format='jpeg')

    return buffer.getvalue()


"""Get the location data."""

cities = collections.OrderedDict()

cities["AMSTERDAM"] = ["253d0379", "Amsterdam"]
cities["ATLANTA"] = ["17ffc3fe", "Atlanta"]
cities["BAGHDAD"] = ["17b71f95", "Baghdad"]
cities["BALTIMORE"] = ["1bf0c986", "Baltimore"]
cities["BANGKOK"] = ["09c7477a", "Bangkok"]
cities["BEIJING"] = ["1c6252cc", "Beijing"]
cities["BEIRUT"] = ["1818193e", "Beirut"]
cities["BERLIN"] = ["25590988", "Berlin"]
cities["BOSTON"] = ["1e1fcd78", "Boston"]
cities["BRUSSELS"] = ["2427031b", "Brussels"]
cities["CAIRO"] = ["155e1638", "Cairo"]
cities["CHICAGO"] = ["1dc2c1ac", "Chicago"]
cities["CINCINNATI"] = ["1bd9c3f2", "Cincinnati"]
cities["CLEVELAND"] = ["1d82c5e8", "Cleveland"]
cities["DALLAS"] = ["1750bb2b", "Dallas"]
cities["DENVER"] = ["1c42b559", "Denver"]
cities["DETROIT"] = ["1e1ac4f2", "Detroit"]
cities["DJIBOUTI"] = ["083f1eaf", "Djibouti"]
cities["DUBLIN"] = ["25e2fb8d", "Dublin"]
cities["GENEVA"] = ["20d0045c", "Geneva"]
cities["GIBRALTAR"] = ["19b3fc32", "Gibraltar"]
cities["GUATEMALA CITY"] = ["0a61bfb5", "Guatemala City"]
cities["HAVANA"] = ["1076c571", "Havana"]
cities["HELSINKI"] = ["2ac911bb", "Helsinki"]
cities["HONG KONG"] = ["0ff95147", "Hong Kong"]
cities["HONOLULU"] = ["0f268fbf", "Honolulu"]
cities["HOUSTON"] = ["152abc30", "Houston"]
cities["INDIANAPOLIS"] = ["1c47c2bc", "Indianapolis"]
cities["ISLAMABAD"] = ["17f63407", "Islamabad"]
cities["ISTANBUL"] = ["1d32149f", "Istanbul"]
cities["JERUSALEM"] = ["1696190a", "Jerusalem"]
cities["JOHANNESBURG"] = ["ed6913f2", "Johannesburg"]
cities["KUWAIT CITY"] = ["14e2221e", "Kuwait City"]
cities["LAS VEGAS"] = ["19b9ae21", "Las Vegas"]
cities["LONDON"] = ["24a0ffeb", "London"]
cities["LOS ANGELES"] = ["1837abeb", "Los Angeles"]
cities["LUXEMBOURG"] = ["2347045b", "Luxembourg"]
cities["MACAU"] = ["0fcc50c8", "Macau"]
cities["MADRID"] = ["1cb3fd62", "Madrid"]
cities["MEXICO CITY"] = ["0dd1b981", "Mexico City"]
cities["MIAMI"] = ["1253c6fa", "Miami"]
cities["MILAN"] = ["20550688", "Milan"]
cities["MILWAUKEE"] = ["1e9ac17e", "Milwaukee"]
cities["MINNEAPOLIS"] = ["1ffcbdae", "Minneapolis"]
cities["MONACO"] = ["1f160549", "Monaco"]
cities["MONTREAL"] = ["2051cbbf", "Montréal"]
cities["MOSCOW"] = ["27a81abf", "Moscow"]
cities["MUNICH"] = ["223a0837", "Munich"]
cities["NEW DELHI"] = ["145636e5", "New Delhi"]
cities["NEW ORLEANS"] = ["154dbff3", "New Orleans"]
cities["NEW YORK"] = ["1cf3cb60", "New York"]
cities["OKLAHOMA CITY"] = ["1938baa8", "Oklahoma City"]
cities["PANAMA CITY"] = ["0664c787", "Panama City"]
cities["PARIS"] = ["22bd01ab", "Paris"]
cities["PHILADELPHIA"] = ["1c69ca8d", "Philadelphia"]
cities["PHOENIX"] = ["17c9b04e", "Phoenix"]
cities["PITTSBURGH"] = ["1cc1c71e", "Pittsburgh"]
cities["PRAGUE"] = ["239b0a43", "Prague"]
cities["QUEBEC CITY"] = ["214ccd6b", "Quebec City"]
cities["RIO DE JANEIRO"] = ["efb8e142", "Rio de Janeiro"]
cities["ROME"] = ["1dca08e1", "Rome"]
cities["SALT LAKE CITY"] = ["1cfcb06f", "Salt Lake City"]
cities["SAN ANTONIO"] = ["14ecb9f6", "San Antonio"]
cities["SAN DIEGO"] = ["1743acb1", "San Diego"]
cities["SAN FRANCISCO"] = ["1adca8f3", "San Francisco"]
cities["SAN MARINO"] = ["1f3d08d7", "San Marino"]
cities["SAO PAULO"] = ["ef44deda", "São Paulo"]
cities["SEATTLE"] = ["21daa903", "Seattle"]
cities["SHANGHAI"] = ["16385661", "Shanghai"]
cities["SINGAPORE"] = ["00eb49da", "Singapore"]
cities["ST. LOUIS"] = ["1b77bfdc", "St. Louis"]
cities["STOCKHOLM"] = ["2a200cd5", "Stockholm"]
cities["SYDNEY"] = ["e7e76b8c", "Sydney"]
cities["TOKYO"] = ["19606363", "Tokyo"]
cities["TORONTO"] = ["1f13c787", "Toronto"]
cities["UNITED NATIONS"] = ["1cf0cb78", "United Nations"]
cities["VATICAN CITY"] = ["1dcc08db", "Vatican City"]
cities["VIENNA"] = ["223d0ba0", "Vienna"]
cities["WASHINGTON"] = ["1ba8c938", "Washington"]
cities["ZURICH"] = ["21a40610", "Zürich"]


def locations_download(language_code, data):
    locations = collections.OrderedDict()
    locations_return = collections.OrderedDict()
    gmaps = googlemaps.Client(key=config["google_maps_api_key"])

    """This dictionary is used to determine languages."""

    languages = {
        0: "ja",
        1: "en",
        2: "de",
        3: "fr",
        4: "es",
        5: "it",
        6: "nl",
    }

    for keys, values in list(data.items()):
        location = values[7]

        if location is not None:
            if location not in locations: locations[location] = []

            locations[location].append(keys)

    for name in list(locations.keys()):
        read = None

        if name == "":
            continue

        #print(unidecode(name))

        if name not in cities:
            try:
                read = gmaps.geocode(unidecode(name), language=languages[language_code])
            except:
                log("There was a error downloading the location data.", "INFO")

        if read is None and name in cities:
            coordinates = binascii.unhexlify(cities[name][0] + "0000000006000000")
            new_name = enc(cities[name][1])

            for filenames in locations[name]:
                if new_name not in locations_return: locations_return[new_name] = [coordinates, []]

                locations_return[new_name][1].append(filenames)

        elif read is not None:
            try:
                new_name = enc(read[0]["address_components"][0]["long_name"])

                """Not doing anything with these at this time."""

                country = u8(0)
                region = u8(0)
                location = u16(0)
                zoom_factor = u32_littleendian(6)

                coordinates = u16(int(read[0]["geometry"]["location"]["lat"] / 0.0054931640625) & 0xFFFF) + u16(int(
                    read[0]["geometry"]["location"][
                        "lng"] / 0.0054931640625) & 0xFFFF) + country + region + location + zoom_factor

                for filenames in locations[name]:
                    if new_name not in locations_return: locations_return[new_name] = [coordinates, []]

                    locations_return[new_name][1].append(filenames)
            except:
                log("There was a error downloading the location data.", "INFO")

    return locations_return


"""Get location from Geoparser."""


def geoparser_get(article):
    i = 0
    for key in config["geoparser_keys"]:
        url = 'https://geoparser.io/api/geoparser'
        headers = {'Authorization': "apiKey %s" % key}
        data = {'inputText': article}
        response = requests.post(url, headers=headers, data=data)
        status_code = response.status_code
        if response.status_code == 402:
            continue
        else:
            try:
                property = response.json()["features"][0]["properties"]
                i += 1
                return property["name"] + ", " + property["country"]
            except:
                return None
    log("Out of Geoparser requests.", "WARNING")
    return None

"""Download the news."""

class News:
    def __init__(self, source):
        self.source = source["type"]  # TODO Remove code that depends on this value. It's not clean.
        self.sourceinfo = source
        self.language = self.sourceinfo["lang"]
        self.newsdata = collections.OrderedDict()

        self.parse_feed()

    def __dict__(self):
        return self.newsdata

    def parse_feed(self):
        print("Downloading News from " + self.sourceinfo["name"] + "...")

        for key, value in list(self.sourceinfo["cat"].items()):
            try:
                feed = self.sourceinfo["feed"](key)
            except IOError:
                print("Failed to read article")
                continue

            i = 0

            entries = self.sourceinfo["entries"](feed)

            for entry in entries:
                if self.source == "AP":
                    try:
                        entry = entry["contents"][0]
                    except:
                        continue

                current_time = int((time.mktime(datetime.utcnow().timetuple()) - 946684800) / 60)
                try:
                    updated_time = int((time.mktime(time.strptime(entry["updated"], "%Y-%m-%d %H:%M:%S") if self.source == "AP" else entry["updated_parsed"]) - 946684800) / 60)
                except:
                    print("Failed to parse RSS feed.")
                    continue

                if current_time - updated_time < 60:
                    i += 1

                    if self.source == "AFP_French" and key not in entry["link"]:
                        continue
                    elif self.source == "AFP" and "dpa" in entry["description"]:
                        self.source = "dpa"  # TODO Thing at line 472
                        self.sourceinfo["copyright"] = "Alle Rechte für die Wiedergabe, Verwertung und Darstellung reserviert. © %s dpa"
                    elif self.source == "NU.nl" and entry["author"] == "ANP":
                        self.sourceinfo["copyright"] = "All reproduction and representation rights reserved. © %d B.V. Algemeen Nederlands Persbureau ANP";
                    elif self.source == "Reuters_Japanese":
                        entry["link"] = requests.get(
                            "http://bit.ly/" + entry["description"].split("http://bit.ly/", 1)[1][:7]).url
                        entry["title"] = entry["title"].split("  http://bit.ly/", 1)[0]

                    title = entry["headline"] if self.source == "AP" else entry["title"]

                    #print(title)

                    downloaded_news = Parse(entry["gcsUrl"] if self.source == "AP" else entry["link"], self.source, updated_time,
                                            title, self.language).get_news()

                    if downloaded_news:
                        self.newsdata[value + str(i)] = downloaded_news


class Parse(News):
    def __init__(self, url, source, updated_time, headline, language, article=None, picture=None, credits=None, caption=None,
                 location=None, resize=None, html=None, soup=None):
        self.url = url
        self.source = source
        self.updated_time = updated_time
        self.headline = headline
        self.language = language
        self.article = article
        self.picture = picture
        self.credits = credits
        self.caption = caption
        self.location = location
        self.resize = resize
        self.html = html
        self.soup = soup

        if self.source != "AP":
            self.newspaper_init()

        {
            "AP": self.parse_ap,
            "Reuters": self.parse_reuters,
            "AFP_French": self.parse_afp,
            "AFP": self.parse_donaukurier,
            "SID": self.parse_sid,
            "ANSA": self.parse_ansa,
            "NU.nl": self.parse_nu,
            "Reuters_Japanese": self.parse_reuters_japanese
        }[self.source]()

        self.get_news()

    def get_news(self):
        return [] if not self.headline or not self.article else [u32(self.updated_time), u32(self.updated_time), enc(self.article), enc(self.headline),
                    shrink_image(self.picture, self.resize, self.source), enc(self.credits), enc(self.caption),
                    self.location, self.source]

    def newspaper_init(self):
        self.newsdata = newspaper.Article(self.url, language=self.language)
        self.newsdata.download()
        self.newsdata.parse()

        self.article = self.newsdata.text
        self.picture = self.newsdata.top_image
        self.html = self.newsdata.html
        self.soup = BeautifulSoup(self.html, "lxml")

    def parse_ap(self):
        try:
            self.newsdata = requests.get(self.url).json()
        except JSONDecodeError:
            return []

        if self.newsdata["localMemberName"] is not None:
            return []

        if self.newsdata["localLinkUrl"]:
            if "apnews" not in self.newsdata["localLinkUrl"]:
                return []
        else:
            return []

        self.article = BeautifulSoup(self.newsdata["storyHTML"], "lxml").text.replace("\n", "\n\n")

        if self.article[-2:] == "\n\n":
            self.article = self.article[:-2]

        if self.newsdata["bylines"] != "":
            self.article += "\n\n" + self.newsdata["bylines"]

        if self.article is None:
            return []

        if self.newsdata["mediaCount"] > 0 and self.newsdata["media"] != []:
            if self.newsdata["media"][0]["imageMimeType"] == "image/jpeg":
                self.resize = True

                self.picture = self.newsdata["media"][0]["gcsBaseUrl"] + "400" + self.newsdata["media"][0]["imageFileExtension"]

                self.caption = self.newsdata["media"][0]["flattenedCaption"]

                try:
                    self.credits = self.caption.rsplit("(")[-1][:-1]
                except:
                    self.credits = None
            else:
                self.picture = None
        else:
            self.picture = None

        if self.newsdata["dateline"] != None:
            self.location = self.newsdata["dateline"]

    def parse_reuters(self):
        try:
            self.soup.find("div", {"class": "trustBadgeContainer_1gqgJ"}).decompose()
        except:
            pass

        try:
            self.caption = self.soup.find("span", {"class": "caption_KoNH1"}).text.replace("  REUTERS/",
                                                                                           " REUTERS/")
        except:
            pass

        try:
            self.soup.findall("div", {"class": "caption_KoNH1"}).decompose()
        except:
            pass

        self.article = BeautifulSoup(
            str(self.soup.find("div", {"class": "body_1gnLA"})).replace("</p>", "\n\n</p>"),
            "lxml").text

        if self.picture is not None:
            if "rcom-default.png" in self.picture:
                self.picture = None
            else:
                self.resize = False
                try:
                    self.picture += "&w=200"
                except:
                    pass

        if "(Reuters)" in self.article and self.article[:9] != "(Reuters)":
            self.location = self.article.split(" (Reuters)")[0]

    def parse_afp(self):
        try:
            self.resize = True
            self.caption = self.soup.find("figcaption", {"class": "art-caption"}).text
        except:
            pass

        try:
            """The location is at the end of the article, I couldn't find anything better to parse it."""

            if "(AFP)" in self.article:
                buf = BytesIO(self.article)
                line = buf.readlines()[-1]
                buf = BytesIO(self.article)
                self.location = line.strip()[22:-19]
                self.article = line.strip()[22:-10] + buf.readlines()[1:].replace("\n\n" + line, "")
        except:
            pass

    def parse_donaukurier(self):
        try:
            self.resize = True
            self.caption = self.soup.find("figcaption").text
        except:
            pass

        if self.caption is not None:
            buf = BytesIO(self.article)
            self.article = "".join(buf.readlines()[1:])

        try:
            if self.source == "AFP":
                self.location = self.soup.find("em").text.split(" (AFP)")[0]
            elif self.source == "dpa":
                self.location = self.article.split(" (dpa)")[0]
        except:
            pass

    def parse_sid(self):
        try:
            self.resize = True
            self.caption = self.soup.find("small").text
        except:
            pass

        try:
            self.location = geoparser_get(self.article)
        except:
            pass

    def parse_ansa(self):
        try:
            self.resize = True
            self.credits = self.soup.find("div", {"class": "news-caption hidden-phone"}).find("em").text
        except:
            pass

        try:
            self.location = self.soup.find("span", {"itemprop": "dateline"}, {"class": "location"}).text
        except:
            pass

    def parse_nu(self):
        if "Video" in self.headline or "Liveblog" in self.headline:
            return None

        try:
            self.resize = True
            self.credits = self.soup.find("span", {"class": "photographer"}).text
        except:
            pass

        try:
            self.location = geoparser_get(self.article)
        except:
            pass

    def parse_reuters_japanese(self):
        try:
            self.headline = self.soup.find("h1", {"class": "headline_2zdFM"}).text
        except:
            return None

        try:
            self.caption = self.soup.find("span", {"class": "caption_KoNH1"}).text.replace("  REUTERS/",
                                                                                           " REUTERS/")
        except:
            pass

        try:
            self.soup.findall("div", {"class": "caption_KoNH1"}).decompose()
        except:
            pass

        article_text = BeautifulSoup(
            str(self.soup.find("div", {"class": "body_1gnLA"})).replace("</p>", "\n\n</p>"),
            "lxml").text

        self.article = "\n".join(textwrap.wrap(article_text, 25))

        if self.picture is not None:
            if "rcom-default.png" in self.picture:
                self.picture = None
            else:
                self.resize = False
                try:
                    self.picture += "&w=200"
                except:
                    pass

        try:
            self.location = self.article.split("[")[1].split("　")[0]
        except:
            pass
