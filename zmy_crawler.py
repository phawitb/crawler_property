from webdriver_manager.chrome import ChromeDriverManager   #-------
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
import time
from datetime import datetime
import json
from dateutil.relativedelta import *
import os

DIFF_MONTH = 0  #craw if lastupdate < 1 month

def scrolling_down(t):
    for i in range(t):
        driver.execute_script("window.scrollBy(0,2000)","")
        time.sleep(0.5)
        
def get_text(x):
    return driver.find_element(By.XPATH,x).text

def get_herf(x):
    return driver.find_element(By.XPATH,x).get_attribute("href")

def click(x):
    driver.find_element(By.XPATH,x).click()

def get_links(page):
    driver.get(f'https://th.zmyhome.com/buy?page={page}&sortFilter=ads&per-page=40')
    # time.sleep(3)
    LINK = []
    c = 1
    for i in range(50):
        try:
            driver.implicitly_wait(3)
            p = f'/html/body/div[1]/section[2]/div/div/div/div[4]/div[{i}]/article/figure/a'
            link = driver.find_element(By.XPATH,p).get_attribute("href")
            LINK.append(link)
            c += 1
        except:
            pass
    return LINK

def get_Details(url):
#     driver.get('https://th.zmyhome.com/property/H362887')
    driver.get(url)
    driver.implicitly_wait(3)
    # time.sleep(3)

    def get_detailbox():
        t = get_text('/html/body/div[1]/section[1]/div/div/div/div[3]/div[2]').split('\n')[1:]
        d = {}
        for i in range(len(t)):
            if i%2==0:
                d[t[i]] = t[i+1]
        return d

    def get_near():
        try:
            t = get_text('/html/body/div[1]/section[1]/div/div/div/div[3]/div[5]').split('\n')
            location = t[2]
            t = [x for x in t if x not in ['ทำเลที่ตั้ง','คลิกดูแผนที่','น้อยลง']]
            idx = None
            near = []
            for i in t:
                if '(' not in i:
                    idx = i
                else:
                    near.append(f'{idx}-{i}')
            return near,location
        except:
            return None,None
    
    def create_date(d):
        dd = d.split()
        if 'วันนี้' in d:
            date = datetime.now()
        elif 'เดือน' in d:
            date = datetime.now() + relativedelta(months=-1*int(dd[1]))
        elif 'วัน' in d:
            date = datetime.now() + relativedelta(days=-1*int(dd[1]))
        elif 'ปี' in d:
            date = datetime.now() + relativedelta(years=-1*int(dd[1]))
        else:
            date = d
        return date.strftime("%Y%m%d")

    d = get_detailbox()
    try:
        click('/html/body/div[1]/section[1]/div/div/div/div[3]/div[5]/a')  #attend ทำเลที่ตั้ง
    except:
        pass
    d['header'] = get_text('/html/body/div[1]/section[1]/div/div/div/div[1]/h2')
    try:
        d['sub_header'] = get_text('/html/body/div[1]/section[1]/div/div/div/div[1]/div')
    except:
        pass

    gps = ['/html/body/div[1]/section[1]/div/div/div/div[3]/div[6]/div/a',
           '/html/body/div[1]/section[1]/div/div/div/div[3]/div[5]/div/a',
           '/html/body/div[1]/section[1]/div/div/div/div[3]/div[5]/div/a']
           
    for g in gps:
        try:
            d['gps'] = get_herf(g)
            break
        except:
            # print('no GPS........'*10)
            pass

    if 'gps' not in d.keys():
        print('no GPS........'*10)
        
    d['price_per_area'] = get_text('/html/body/div[1]/section[1]/div/div/div/div[3]/div[1]/ul/li/small')
    d['seen'] = get_text('/html/body/div[1]/section[1]/div/div/div/div[2]/div[2]/div/ul[2]/li[1]/a/span[2]')
    d['love'] = get_text('/html/body/div[1]/section[1]/div/div/div/div[2]/div[2]/div/ul[2]/li[2]/a/span[2]')
    d['last_update'] = create_date(get_text('/html/body/div[1]/section[1]/div/div/div/div[2]/div[2]/div/ul[2]/li[4]/a/span[2]'))
    
    near,location = get_near()
    if near:
        d['near'] = near
    if location:
        d['location'] = location
    d['timestamp'] = time.time()
    return d

def diff_month(d2,d1):
#     d2 = datetime.now().strftime("%Y%m%d")
    y = int(d2[:4])-int(d1[:4])
    m = int(d2[4:6])-int(d1[4:6])
    return 12*y+m


# driver = webdriver.Chrome()
driver = webdriver.Chrome(ChromeDriverManager(version='108.0.5359.71').install())   #-----------------

page = 1
driver.get(f'https://th.zmyhome.com/buy?page={page}&sortFilter=ads&per-page=40')
driver.find_element(By.XPATH,'/html/body/div[2]/button').click()
max_page = driver.find_element(By.XPATH,'/html/body/div[1]/section[2]/div/div/div/div[5]/ul/li[8]/a').text
max_page = int(max_page)
print('max_page:',max_page)

# max_page = 2
page = 1

if not os.path.exists('data'):
  os.makedirs('data')

for page in range(1,max_page+1):
    LINK = get_links(page)
    
    try:
        with open('data/zmy_data.json', 'r') as openfile:
            D = json.load(openfile)
    except:
        D = {}

    for i,url in enumerate(LINK):
        
        if not url in D.keys():
            print('key not exist')
            craw = True
        else:
            d2 = datetime.now().strftime("%Y%m%d")
            d1 = D[url]['last_update']
            print('key exist diff month',diff_month(d2,d1))
            if diff_month(d2,d1) < DIFF_MONTH:
                craw = True
            else:
                if 'gps' in D[url].keys():
                    craw = True
                else:
                    craw = False

        print(f'{i}/{page},{url}')

        if craw:
            d = get_Details(url)
            print(d)
            D[url] = d

    with open("data/zmy_data.json", "w") as outfile:
        outfile.write(json.dumps(D, indent=4))

