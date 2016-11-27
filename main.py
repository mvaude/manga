from urllib.request import urlopen
import os
import pprint
import re
import sys

from bs4 import BeautifulSoup
import requests

class Manga(object):

    base_url = "http://www.mangaeden.com/en/en-manga/"

    def __init__(self, manga):
        self.name = manga
        self.get_chapters()

    def get_scan(self, url):
        print("URL: {}".format(url))
        # html = urlopen(url)
        html = requests.get(url, allow_redirects=False)
        print(html.status_code)
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
            print("SCAN: ", scan)
            r = requests.get(scan)
            print(r.status_code)
            f.write(r.content)

    def get_chapters(self):
        self.chapters = []
        r = requests.get("{}/{}/".format(self.base_url, self.name))
        if r.status_code == 200:
            bsObj = BeautifulSoup(r.text, "html.parser")
            for scan in bsObj.find_all("a", "chapterLink"):
                chapter = re.findall(r'/(\d+\.*\d*)/1/', scan.attrs["href"])
                print(chapter)
                if len(chapter[0]) > 0:
                    try:
                        num = int(chapter[0])
                    except ValueError:
                        num = float(chapter[0])
                    self.chapters.append(num)
        self.chapters = sorted(self.chapters) 
        print(self.chapters)
    
def main(manga):
    mng = Manga(manga)
    count = 0
    for chapter in mng.chapters:
        for page in range(1, 1000):
            url = "{}{}/{}/{}/".format(mng.base_url, mng.name, chapter, page)
            scan = mng.get_scan(url)
            if scan == "":
                count += 1
                break
            mng.write_scan(scan, chapter, page)
            count = 0
        if count == 3:
            break

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("No enough arguments")
    else:
        print(sys.argv[1])
        main(sys.argv[1])
