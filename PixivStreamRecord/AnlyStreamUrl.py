import urllib3
from bs4 import BeautifulSoup
import json
import sys,os,signal
import time

def getStreamUrl(id):
    http = urllib3.PoolManager()
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    # user1 tkh_c
    # user2 sakusyo-art
    # user3 katze_horenso
    url = 'https://sketch.pixiv.net/@%s/lives/' %id
    r = http.request('GET', url)
    soup = BeautifulSoup(r.data.decode('utf-8'), "lxml")
    x = soup.find(id='state').string
    x = x[x.find('=') + 1:]
    y = json.loads(x)
    # find liveId
    params = y['context']['dispatcher']['stores']['RouteStore']['currentNavigate']['route']['params']
    if 'live_id' in params.keys():
        live_id = params['live_id']
        m3u8Url = y['context']['dispatcher']['stores']['LiveStore']['lives'][live_id]['owner']['hls_movie']
        return m3u8Url,live_id
    else:
        return False,False

def getHighResUrl(id):
    baseUrl,live_id = getStreamUrl(id)
    if baseUrl:
        highResUrl = baseUrl.replace('index.m3u8','4000000_1920x1080/index.m3u8')
        http = urllib3.PoolManager()
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        resCode = http.request('GET',highResUrl)
        if resCode.status == 200:
            return highResUrl,live_id
        else:
            return False,False
    else:
        return False,False

if __name__ == "__main__":
    userid = sys.argv[1]
    dateTime = time.strftime('%y%m%d%H%M',time.localtime(time.time()))
    highResUrl, live_id = getHighResUrl(userid)
    if not live_id:
        print('Live is not start')
        sys.exit(1)
    print('URL = %s , live_id = %s'%(highResUrl,live_id))
    fileName = 'PixivStream-%s-%s-%s' %(userid,dateTime,live_id)
    print('logFileName = %s.log , steramFileName = %s.mkv'%(fileName,fileName))
    processInfo = os.popen('ps -ef |grep %s |grep -v grep'%live_id).readlines()
    processNum = len(processInfo)
    print('processNum = %s'%processNum)
    if processNum==0:
        os.system('nohup /usr/bin/ffmpeg -i %s -c copy /Raspi/%s.mkv >/Raspi/%s.log 2>&1 &'%(highResUrl,fileName,fileName))
        print('Stream start Recording')
        while(1):
            time.sleep(300)
            http = urllib3.PoolManager()
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
            resCode = http.request('GET', highResUrl)
            if resCode.status == 200:
                print('resCode = %s , Stream is still alive'%resCode.status)
                continue
            else:
                processPids = os.popen("ps -ef |grep %s |grep -v grep|awk '{print $2}'" %live_id).readlines()
                for pid in processPids:
                    print('pid = %s , Stream record is dead' %pid)
                    os.kill(int(pid),signal.SIGKILL)
                # mkv to mp4 to fix time scroll
                os.system('/usr/bin/ffmpeg -i /Raspi/%s.mkv -c copy /Raspi/%s.mp4'%(fileName,fileName))
                sys.exit(0)
    else:
        print('Stream is Recording')