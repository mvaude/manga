from urllib.request import urlopen
from bs4 import BeautifulSoup
import requests
import os
import sys

class Manga(object):
    
    def __init__(self, manga):
        self.manga = manga

    def get_scan(self, url):
        print("URL: {}".format(url))
        # html = urlopen(url)
        html = requests.get(url, allow_redirects=False)
        print(html.status_code)
        if html.status_code == 200:
            bsObj = BeautifulSoup(html.text, "html.parser")
            res = bsObj.find_all("img", id="mainImg")
            print(res)
            scan = res[0].attrs["src"]
            print(scan)
            return "http:{}".format(scan)
        else:
            return ""
    
    def get_ext(self, scan):
        return "jpg" if "jpg" in scan else "png"
    
    def write_scan(self, manga, scan, chapter, page):
        if not os.path.exists(manga):
            os.makedirs(manga)
        path = "{}/{}".format(manga, chapter)
        if not os.path.exists(path):
            os.makedirs(path)
        path = "{}/{}/{:03d}".format(manga, chapter, page)
        if not os.path.exists(path):
            os.makedirs(path)
        with open("./{}/{:03d}.{}".format(path, page, self.get_ext(scan)), "wb") as f:
            print(scan)
            r = requests.get(scan)
            print(r.status_code)
            f.write(r.content)
    
def main(manga):
    mng = Manga(manga)
    count = 0
    for chapter in range(10000):
        for page in range(1, 1000):
            url = "http://www.mangaeden.com/en/en-manga/{}/{}/{}/".format(manga, chapter, page)
            scan = mng.get_scan(url)
            if scan == "":
                count += 1
                break
            mng.write_scan(manga, scan, chapter, page)
            count = 0
        if count == 3:
            break

if __name__ == "__main__":
    if (len(sys.argv) != 2):
        print("No enough arguments")
    else:
        print(sys.argv[1])
        main(sys.argv[1])
