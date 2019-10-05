import os
import sys
import requests
import datetime
from Crypto.Cipher import AES
from binascii import b2a_hex, a2b_hex
import re
import logging
import time

logging.basicConfig(filename='crawler.log',level=logging.INFO,format='%(asctime)s %(filename)s[line:%(lineno)d] %(message)s',datefmt='%Y-%m-%d %X')
headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.84 Safari/537.36',
        }
def download(url,name):
    download_path = os.getcwd() + "/download"
    if not os.path.exists(download_path):
        os.mkdir(download_path)
    
    filepath = os.path.join(download_path, name + ".mp4")
    if os.path.exists(filepath):
            return
    f = open(filepath, 'wb')


    all_content = requests.get(url).text  # 获取第一层M3U8文件内容
    if "#EXTM3U" not in all_content:
        raise BaseException("非M3U8的链接")
 
    if "EXT-X-STREAM-INF" in all_content:  # 第一层
        file_line = all_content.split("\n")
        for line in file_line:
            if '.m3u8' in line:
                url = url.rsplit("/", 1)[0] + "/" + line # 拼出第二层m3u8的URL
                all_content = requests.get(url).text
 
    file_line = all_content.split("\n")
 
    unknow = True
    key = ""
    n = len(file_line)
    i = 0
    for index, line in enumerate(file_line):  # 第二层
        i = i + 1
        if i % 100 == 0:
            logging.info (str(n)+":"+str(i))
        if "#EXT-X-KEY" in line:  # 找解密Key
            method_pos = line.find("METHOD")
            comma_pos = line.find(",")
            # method = line[method_pos:comma_pos].split('=')[1]
            # logging.info ("Decode Method：", method)

            uri_pos = line.find("URI")
            quotation_mark_pos = line.rfind('"')
            key_path = line[uri_pos:quotation_mark_pos].split('"')[1]
            
            key_url = url.rsplit("/", 1)[0] + "/" + key_path # 拼出key解密密钥URL
            res = requests.get(key_url)
            key = res.content
            # logging.info ("key：" , key)
            cryptor = AES.new(key, AES.MODE_CBC, key)
        if "EXTINF" in line: # 找ts地址并下载
            unknow = False
            pd_url = url.rsplit("/", 1)[0] + "/" + file_line[index + 1] # 拼出ts片段的URL
            #logging.info pd_url
            try:
                res = requests.get(pd_url)
            except:
                f.flush()
                f = open(filepath+str(index), 'wb')
                continue
           
            # c_fule_name = file_line[index + 1].rsplit("/", 1)[-1]
            
            if len(key): # AES 解密
                # cryptor = AES.new(key, AES.MODE_CBC, key)  
                # with open(os.path.join(download_path, c_fule_name + ".mp4"), 'ab') as f:
                #     f.write(cryptor.decrypt(res.content))
                # cryptor = AES.new(key, AES.MODE_CBC, key)
                f.write(cryptor.decrypt(res.content))
            else:
                pass
                # with open(os.path.join(download_path, c_fule_name), 'ab') as f:
                #     f.write(res.content)
                #     f.flush()
    if unknow:
        raise BaseException("未找到对应的下载链接")
    else:
        logging.info ("下载完成")
    # merge_file(download_path)

def detail_page(url):
    s = requests.Session()
    resp = s.get(url, headers=headers)
    title = re.findall('<title>(.*)</title>', resp.text)[0][:-32]
    videoUrl = re.findall("rel=\"preload\" href=\"(.*?)\"", resp.text)[0]
    logging.info(title)
    download(videoUrl,title)

def run():
    logging.info('开始')
    # f = open('/root/asss','w')
    # while 1:
    #     f.write('w')
    #     f.flush()
    #     time.sleep(1)
    for url in open('/root/4', 'r').readlines():
        detail_page(url.strip())
        logging.info('完成')
    # logging.info('完成1')
    
if __name__ == '__main__':
    run()