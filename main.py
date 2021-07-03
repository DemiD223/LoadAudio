from dataclasses import dataclass
from typing import Dict, List
import threading
import requests
from bs4 import BeautifulSoup
from slugify import slugify


@dataclass
class Store:
    title: str
    audio: str
    words: List
    audio_file_status: bool = False


class LoadAudio:
    def __init__(self):
        self.__our_thread = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for t in self.__our_thread:
            t.join()

    def load(self, store: Store):
        t = threading.Thread(target=load_file, args=(store,))
        t.start()
        self.__our_thread.append(t)


def load_file(store: Store):
    link, path = store.audio, f'{slugify(store.title)}.mp3'
    print(f'START DOWNLOAD{store.audio} to {path}')
    req = requests.get(link)
    if req.ok:
        with open(path, 'wb') as fo:
            fo.write(req.content)
        store.audio_file_status = True
        print(f'STOP DOWNLOAD{store.audio} to {path}')
    else:
        print("REQ NOt OK")


def parse_page(link) -> Store:
    req = requests.get(link)
    if not req.ok:
        raise Exception(f"ERROR {link}")
    bs = BeautifulSoup(req.content, 'html.parser')
    title = bs.find_all('h1')[-1].text
    div_media = bs.find('div', class_='media-download')
    if not div_media:
        raise Exception(f"not found audio {link}")
    audio = div_media.find_all('a')[-1]
    if audio.attrs.get('href'):
        audio = audio.attrs['href']
    else:
        raise Exception(f'Error with audio {link}')
    words = []
    if req.text.find('Words in This Story') > 0:
        div_wsw = bs.find('div', class_='wsw')
        all_tags = div_wsw.findChildren(recursive=False)

        key = False
        for tag in all_tags:
            if tag.name == 'h2' and tag.text == 'Words in This Story':
                key = True
            if key and tag.name == 'p':
                words.append(tag.text)
    res = Store(title.strip(), audio, words)
    return res


def list_first_page():
    index = 0
    url = f'https://learningenglish.voanews.com/z/987?p={index}'
    req = requests.get(url)
    while req.status_code != 404:
        soup = BeautifulSoup(req.content, 'html.parser')
        ul = soup.find('ul', id='articleItems')
        all_li = ul.find_all('li')
        all_links = []
        for li in all_li:
            if li.find('a') and li.find('a').attrs.get('href'):
                # all_links.append('https://learningenglish.voanews.com' + li.find('a').attrs['href'])
                yield parse_page('https://learningenglish.voanews.com' + li.find('a').attrs['href'])
        index += 1
        url = f'https://learningenglish.voanews.com/z/987?p={index}'
        req = requests.get(url)


class LearnEnglish:
    def __init__(self):
        self.__url = 'https://learningenglish.voanews.com/z/987'
        self.__ses = requests.Session()

    def __iter__(self):
        self.index = -1

        return self

    def __next__(self):
        pass


all_data = []
not_done = True

def statistics():
    while not_done:
        count_of_finish = 0
        for data in all_data:
            data: Store
            if data.audio_file_status:
                count_of_finish += 1
        # if count_of_finish == len(all_data):
        #     return
        print(f"{count_of_finish}/{len(all_data)}")


if __name__ == '__main__':
    t = threading.Thread(target=statistics)
    t.start()
    with LoadAudio() as loader:
        for ind, element in enumerate(list_first_page()):
            if ind == 10:
                break
            all_data.append(element)
            loader.load(element)
    not_done = False