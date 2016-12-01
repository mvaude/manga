import asyncio
import os
import pprint
import re
import sys
import time
from urllib.request import urlopen
import shutil

from bs4 import BeautifulSoup
import requests

class Manga(object):

    base_url = "http://www.mangaeden.com/en/en-manga/"

    def __init__(self, manga):
        self.name = manga
        self.get_chapters()
        self.scans = {}

    async def get_scan(self, url):
        #`print("URL: {}".format(url))
        # html = urlopen(url)
        html = requests.get(url, allow_redirects=False)
        html.close()
        # print(html.status_code)
        if html.status_code == 200:
            bsObj = BeautifulSoup(html.text, "html.parser")
            res = bsObj.find_all("img", id="mainImg")
            scan = res[0].attrs["src"]
            return "http:{}".format(scan)
        else:
            return ""

    def get_ext(self, scan):
        return "jpg" if "jpg" in scan else "png"
    
    def write_scan(self, scan, chapter, page):
        if not os.path.exists(self.name):
            os.makedirs(self.name)
        path = "{}/{}".format(self.name, chapter)
        if not os.path.exists(path):
            os.makedirs(path)
        with open("./{}/{:03d}.{}".format(path, page, self.get_ext(scan)), "wb") as f:
            # print("SCAN: ", scan)
            r = requests.get(scan)
            # print(r.status_code)
            f.write(r.content)

    def get_chapters(self):
        self.chapters = []
        r = requests.get("{}{}/".format(self.base_url, self.name))
        r.close()
        if r.status_code == 200:
            bsObj = BeautifulSoup(r.text, "html.parser")
            for scan in bsObj.find_all("a", "chapterLink"):
                chapter = re.findall(r'/(\d+\.*\d*)/1/', scan.attrs["href"])
                #print(chapter)
                if len(chapter[0]) > 0:
                    try:
                        num = int(chapter[0])
                    except ValueError:
                        num = float(chapter[0])
                    self.chapters.append(num)
        self.chapters = sorted(self.chapters) 
        # print(self.chapters)

    async def get_scans(self, scan, chapter, page):
        self.write_scan(scan, chapter, page)
        return (chapter, page)

    async def zip_chapter(self, chapter):
        if type(chapter) == float:
            pathname = '{}/{}-chapter-{:08.3f}'.format(self.name, self.name, chapter)
        else:
            pathname = '{}/{}-chapter-{:04d}.000'.format(self.name, self.name, chapter)
        shutil.make_archive(pathname, 'zip', '{}/{}'.format(self.name, chapter))
        os.rename('{}.zip'.format(pathname), '{}.cbz'.format(pathname))
        return "chapter {} compressed".format(chapter)

    async def zip_chapters(self):
        tasks = []
        for chapter in self.chapters:
            tasks.append(self.zip_chapter(chapter))
        return tasks

async def get_routines(manga):
    res = []
    for chapter in manga.chapters:
        for page in range(1, 1000):
            url = "{}{}/{}/{}/".format(manga.base_url, manga.name, chapter, page)
            scan = await manga.get_scan(url)
            if scan == "":
                break
            res.append(manga.get_scans(scan, chapter, page))
    return res

async def main(manga):
    mng = Manga(manga)
    start_time = time.time()
    print("start list of routines")
    routines = await get_routines(mng)
    print("finish list of routines {}s".format(time.time() - start_time))
    tmp_time = time.time()
    print("start async.wait")
    completed, pending = await asyncio.wait(routines)
    print("finish async.wait {}s".format(time.time() - tmp_time))
    res = []
    for item in completed:
        (chapter, page) = item.result()
        res.append((chapter, page))
    routines = await mng.zip_chapters()
    completed, pending = await asyncio.wait(routines)
    for item in completed:
        print(item.result())
    print("Total time: {}s".format(time.time() - start_time))

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("No enough arguments")
    else:
        print(sys.argv[1])
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(sys.argv[1]))
        loop.close()
