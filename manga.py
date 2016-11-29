import asyncio
from operator import itemgetter
import os
import pprint
import re
import shutil
import sys
import time

import aiohttp
import aiofiles
from bs4 import BeautifulSoup

class Manga:

    base_url = "http://www.mangaeden.com"
    manga_url = "/en/en-manga/"

    def __init__(self, manga, from_chapter=0):
        self.name = manga
        self.from_chapter = from_chapter

    async def get_scan(self, url, client):
        async with client.get(url, allow_redirects=False) as html:
            if html.status == 200:
                bsObj = BeautifulSoup(await html.text(encoding='utf-8'), "html.parser")
                res = bsObj.find_all("img", id="mainImg")
                scan = res[0].attrs["src"]
                return "http:{}".format(scan)
            else:
                return ""

    async def get_pages(self, chapter, client):
        pages = {}
        pages[chapter] = []
        async with client.get("{}{}".format(self.base_url, self.chapters[chapter])) as r:
            if r.status == 200:
                bsObj = BeautifulSoup(await r.text(encoding='utf-8'), "html.parser")
                for scans in bsObj.find_all("select", id="pageSelect"):
                    for scan in scans.find_all("option"):
                        url = self.get_scan("{}{}".format(self.base_url, scan.attrs["value"]), client)
                        pages[chapter].append((int(scan.attrs["data-page"]), url))
        return pages

    def get_string(self, num):
        if type(num) is int:
            return "{:04d}.000".format(num)
        elif type(num) is float:
            return "{:08.3f}".format(num)

    async def get_chapters(self, client):
        self.chapters = {}
        self.chapter_pages = {}
        async with client.get("{}{}{}/".format(self.base_url, self.manga_url, self.name)) as r:
            if r.status == 200:
                bsObj = BeautifulSoup(await r.text(encoding='utf-8'), "html.parser")
                for scan in bsObj.find_all("a", "chapterLink"):
                    chapter_link = scan.attrs["href"]
                    chapter = re.findall(r'/(\d+\.*\d*)/1/', chapter_link)
                    if len(chapter[0]) > 0:
                        if chapter[0] < str(self.from_chapter):
                            break
                        try:
                            num = int(chapter[0])
                        except ValueError:
                            num = float(chapter[0])
                        self.chapters[num] = chapter_link
                        self.chapter_pages[num] = []
        return self.chapters

    async def _get_urls(self, client):
        routines = [self.get_pages(chapter, client) for chapter in sorted(self.chapters.keys())]
        completed, prending = await asyncio.wait(routines)
        urls = []
        for item in completed:
            data = item.result()
            key = list(data.keys())[0]
            self.chapter_pages[key] = data[key]
        return self.chapter_pages

    async def get_urls(self, client):
        start_time = time.time()
        print("start url")
        await self.get_chapters(client)
        urls = await self._get_urls(client)
        print("url end: {}s".format(time.time() - start_time))
        return urls

    async def zip_chapter(self, chapter):
        pathname = '{}/{}-chapter-{}'.format(self.name, self.name, chapter)
        shutil.make_archive(pathname, 'zip', '{}/{}'.format(self.name, chapter))
        os.rename('{}.zip'.format(pathname), '{}.cbz'.format(pathname))
        return "{}.cbz".format(pathname)

    def get_ext(self, scan):
        return "jpg" if "jpg" in scan else "png"

    async def write_file(self, f, r):
        while True:
            chunk = await r.content.read(1024)
            if not chunk:
                break
            await f.write(chunk)

    async def get_picture(self, client, scan, f):
        try:
            async with client.get(scan) as r:
                await self.write_file(f, r)
        except (aiohttp.errors.ServerDisconnectedError, aiohttp.errors.ClientResponseError):
            async with aiohttp.ClientSession() as client:
                await self.get_picture(client, scan, f)

    async def download(self, chapter, page, scan, client):
        if not os.path.exists(self.name):
            os.makedirs(self.name)
        path = "{}/{}".format(self.name, self.get_string(chapter))
        if not os.path.exists(path):
            os.makedirs(path)
        async with aiofiles.open("./{}/{:03d}.{}".format(path, page, self.get_ext(scan)), "wb") as f:
            await self.get_picture(client, scan, f)
        return "0"

    async def download_chapters(self):
        routines = []
        res = []
        async with aiohttp.ClientSession() as client:
            urls = await self.get_urls(client)
            for chapter in urls.keys():
                for (page, url) in urls[chapter]:
                    routines.append(self.download(chapter, page, await url, client))
            completed, pending = await asyncio.wait(routines)
            for item in completed:
                res.append(item.result())
            routines = [self.zip_chapter(self.get_string(chapter)) for chapter in self.chapters.keys()]
            completed, pending = await asyncio.wait(routines)
            res = []
            for item in completed:
                res.append(item.result())
            res = sorted(res)
        return res

    def download_manga(self):
        tmp_time = time.time()
        print('start download loop')
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.download_chapters())
        loop.close()
        

if __name__ == "__main__":
    start_time = time.time()
    m = Manga(sys.argv[1])
    m.download_manga()
    print("finish in {0:.2f}s".format(time.time() - start_time))
