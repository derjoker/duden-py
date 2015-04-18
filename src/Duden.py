# coding: UTF-8

import urllib
import urllib2
import os.path
from bs4 import BeautifulSoup

import config
from anki import CardImg
from anki import CardIdiom
from anki import CardExample

# sound download path
_path_duden_mp3 = config._path_duden_mp3
# picture download path
_path_duden_img = config._path_duden_img
# rechtschreibung html path
_path_rechtschreibung = config._path_rechtschreibung

'''
Constant
'''

CODEC = 'UTF-8'

'''
Function
'''

# #Improve#

def read(url):
#     TIMEOUT = 0.010
    TIMEOUT = 10
    TRY = 3
    count = 0
    r = ''
    while (count < TRY and r == ''):
        try:
            r = urllib2.urlopen(url, timeout=TIMEOUT).read()
        except Exception,e:
            print e
            r = ''
        count += 1
    return r

'''
Class
'''

class Duden:
    
    def __init__(self):
        print 'Duden'

class Rechtschreibung:
    
    URLRECHTSCHREIBUNG = 'http://www.duden.de/rechtschreibung/'
    
    # access key
    k_img = 'img'
    k_text = 'text'
    k_def = 'definition'
    k_examples = 'examples'
    
    def __init__(self, d_rechtschreibung):
        self.rechtschreibung = d_rechtschreibung
        self.url = Rechtschreibung.URLRECHTSCHREIBUNG + d_rechtschreibung
        
        localRS = os.path.join(_path_rechtschreibung, self.rechtschreibung + '.html')
        if os.path.exists(localRS):
            self.html = open(localRS).read()
        else:
            self.html = read(self.url).replace('\n', '')    # no newline, prepare for Anki card
            if self.html != '':
                with open(localRS,'w') as f:
                    f.write(self.html)
        
        self.soup = BeautifulSoup(self.html)
        
        try:
            # get_text() return Unicode
            self.wort = self.soup.find('span', class_='lemma_zeile').get_text().strip()
        except Exception,e:
            print d_rechtschreibung, e
            self.wort = ''
        
        # even if there's actually no mp3 for this word (in case we can find one someday ^_^)
        self.aussprache = self.rechtschreibung + '.mp3'
        
        self.bild = []
        
        self.beispiele = []
    
    def isValid(self):
        return self.rechtschreibung != '' and self.wort != ''
    
    def downloadMP3(self):
        try:
            # it could happen that, there's no mp3 (e.g. sicher_machen)
            url_mp3 = self.soup.find('a', text="Als mp3 abspielen")['href']
            local_mp3 = os.path.join(_path_duden_mp3, self.aussprache)
            print 'start downloading pronunciation ...', self.wort
            urllib.urlretrieve(url_mp3, local_mp3)
            print url_mp3, 'downloaded.'
        except Exception,e:
            print e
    
    def downloadImg(self):
        imgs = self.soup.find_all('img', class_='hidden')
        
        for index in range(len(imgs)):
            text = str(imgs[index].find_next_sibling('span', class_='bu')).decode(CODEC)
            
            url_img = imgs[index]['src']
            img_name = self.rechtschreibung + '-' + str(index) + '.' + url_img.split('.')[-1]
            local_img = os.path.join(_path_duden_img, img_name)
            print 'start downloading ...', img_name
            urllib.urlretrieve(url_img, local_img)
            print 'image downloaded.'
            
            content = BeautifulSoup(str(imgs[index].find_parent('span', class_='content')))
            for div in content.find_all(['div', 'span'],recursive=False):
                div.decompose()
            definition = str(content).decode(CODEC)
                        
            self.bild.append({Rechtschreibung.k_img:img_name, Rechtschreibung.k_text:text, Rechtschreibung.k_def:definition})
    
    def getBeispiele(self):
        b = []
        
        beispiele = self.soup.find_all('div', class_='Beispiele')
        
        for beispiel in beispiele:
            bedeutung = BeautifulSoup(str(beispiel.parent))
            for div in bedeutung.find_all('div'):
                div.decompose()
            examples = []
            for bs in beispiel.find_all('span', class_='beispiel'):
                examples.append(str(bs).decode(CODEC))
            b.append({Rechtschreibung.k_def:str(bedeutung).decode(CODEC),Rechtschreibung.k_examples:examples})
        
        return b
    
    def makeCardExample(self):
        cards = []
        
        for item in self.getBeispiele():
            for example in item[Rechtschreibung.k_examples]:
                ce = CardExample(example,self.wort,item[Rechtschreibung.k_def],self.aussprache)
                if ce.isValid():
                    cards.append(ce.printCardExample())
                else: print 'Card Example invalid:', ce.printArgs()
        
        return cards
    
    def getWendungen(self):
        print 'Wendungen'
    
    def getBilder(self):
        bilder = []
        
        imgs = self.soup.find_all('img', class_='hidden')
        
        for img in imgs:
            text = str(img.find_next_sibling('span', class_='bu')).decode(CODEC)
            
            # http://www.duden.de/_media_/full/S/Stellung-201100280769.jpg -> Stellung-201100280769.jpg
            img_name = img['src'].split('/')
            
            content = BeautifulSoup(str(img.find_parent('span', class_='content')))
            for div in content.find_all(['div', 'span'],recursive=False):
                div.decompose()
            definition = str(content).decode(CODEC)
            
            bilder.append({Rechtschreibung.k_img:img_name, Rechtschreibung.k_text:text, Rechtschreibung.k_def:definition})
        
        return bilder
    
    # return Recthschreibung on page without Blaettern part
    def getRechtschreibungOnPage(self):
        if self.html != '':
            soup = BeautifulSoup(self.html)
            # remove Blaettern part (Im Alphabet davor, Im Alphabet danach)
            soup.find('div', class_='field-name-field-browse').extract()
            # /rechtschreibung/fallen#b2-Bedeutung-1d -> fallen
            return [link['href'].split('/')[-1].split('#')[0] for link in soup.select('a[href^="/rechtschreibung/"]')]
        else: return []

class Analyser:
    
    def __init__(self, html):
        self.html = html
    
    def getLinkMP3(self):
        soup = BeautifulSoup(self.html)
        link = soup.find_all('a', text="Als mp3 abspielen")
        print len(link)
        if len(link) > 0:
            # it could happen that, there's no mp3 (e.g. sicher_machen)
            return soup.find('a', text="Als mp3 abspielen")['href']
        return None
    
    # return Recthschreibung on page without Blaettern part
    def getRechtschreibungOnPage(self):
        if self.html != '':
            soup = BeautifulSoup(self.html)
            # remove Blaettern part (Im Alphabet davor, Im Alphabet danach)
            soup.find('div', class_='field-name-field-browse').extract()
            # /rechtschreibung/fallen#b2-Bedeutung-1d -> fallen
            return [link['href'].split('/')[-1].split('#')[0] for link in soup.select('a[href^="/rechtschreibung/"]')]
        else: return []

'''
UnitTest
'''

if __name__ == '__main__':
    lt = [u'Taetigkeit', u'Blickwinkel', u'scheiden', u'Ehe', u'beobachten', u'modern_neu_modisch', u'schmuck', u'drauf', u'Anleitung']
    for item in lt:
        print item
        rs = Rechtschreibung(item)
        
        analyser = Analyser(rs.html)
        print analyser.getLinkMP3()
        print analyser.getRechtschreibungOnPage()