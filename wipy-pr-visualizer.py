import time
import urequests
import machine
import json
from machine import WDT
from network import WLAN

from ws2812 import WS2812

wlan = WLAN()

# Runtime vars
numPRs = 0

# led stuff
CHAIN_LEN = 16
chain = WS2812(CHAIN_LEN)

# actual colors defined in config.json which is loaded in main()
colorsForNumPRs = {
    0: (80, 80, 80),   # white
    1: (0, 80, 80),
    2: (70, 0, 90),
    3: (85, 85, 0),
    4: (100, 70, 0),
    5: (100, 0, 0),    # red
}

# rgbData = [
#     (255, 102, 0), (127, 21, 0), (63, 10, 0), (31, 5, 0),
#     (15, 2, 0), (7, 1, 0), (0, 0, 70), (0, 0, 110),
#     (0, 0, 140), (0, 0, 180), (0, 0, 220), (0, 0, 255)
# ]
# rgbData = [colorsForNumPRs[0]] * CHAIN_LEN
rgbData = [(0, 0, 0)] * CHAIN_LEN
chain.show(rgbData)

def loadSettings(select):
    f = open('config.json', 'r')
    settings = json.loads(f.readall())
    f.close()
    
    if select is not None:
        settings = settings[select]
    
    return settings

def getGQLPRs():
    settings = loadSettings(select = "github")
    
    requestUrl = 'https://api.github.com/graphql'
    qlQuery = 'query{repository(owner:"' + settings['user'] + '",name:"' + settings['repo'] + '"){pullRequests(states:OPEN){totalCount}}}'
    
    data = {
        'query': qlQuery
    }
    
    headers = {
        'User-Agent': 'WiPy PR monitor',
        'Authorization': 'bearer ' + settings['access_token']
    }
    
    r = urequests.post(
        requestUrl,
        headers = headers,
        # data = qlQuery
        json = data
    )
    
    jsonData = r.json()
    r.close()
    
    return jsonData['data']['repository']['pullRequests']['totalCount']

def getPRs():
    # use graphQl instead of regular API because here I can count directly
    return getGQLPRs()
    
    headers = {
        'User-Agent': 'WiPy PR monitor'
    }
    r = urequests.get(
        'https://api.github.com/repos/' + user + '/' + repo + '/pulls?access_token=' + access_token,
        headers = headers
    )
    # numPRs = len(r.json())
    numPRs = countFirstLevelObjectsInJsonResponse(r)
    r.close()
    return numPRs

def countFirstLevelObjectsInJsonResponse(response):
    count = 0
    level = 0
    inString = False
    mask = False
    
    doneReading = False
    
    while not doneReading:
        chunk = response.raw.read(1024)
        if len(chunk) == 0:
            doneReading = True
            continue
        
        strChunk = str(chunk, "utf-8")

        for c in strChunk:
            if c == "\\" and not mask:
                mask = True
                continue

            if c == "\"" and not mask:
                inString = not inString
                continue

            mask = False

            if c == "{" and not inString:
                level += 1
                continue

            if c == "}" and not inString:
                level -= 1
                if level == 0:
                    count += 1

    print("Counted " + str(count))
    return count

def getAndPrintPRs():
    global numPRs
    try:
        numPRs = getPRs()
    except Exception as e:
        print("exception")
        print(str(e))
        numPRs = -1
    
    print("Found PRs: " + str(numPRs))

ticks = 0
highlightPixel = 1

def drawForTicks(ticks, numPRs):
    global rgbData
    global highlightPixel
    
    if numPRs < 0:
        blynk(ticks, [0, 255, 255])
        return
    
    clrIndex = min(numPRs, len(colorsForNumPRs) - 1)
    color = colorsForNumPRs[clrIndex]
    
    if ticks % 10 == 0:
        highlightPixel = (machine.rng() >> 16) % CHAIN_LEN
    
    factor = 10 + (10 - ((ticks - 1) % 10))
    rgbData[highlightPixel] = [
        (color[0] * factor) // 10,
        (color[1] * factor) // 10,
        (color[2] * factor) // 10
    ]
    
    chain.show(rgbData)

def blynk(ticks, color):
    global rgbData
    
    if ticks%20 == 0:
        for i in range(CHAIN_LEN):
            rgbData[i] = color
    
    if ticks%20 == 10:
        for i in range(CHAIN_LEN):
            rgbData[i] = [0, 0, 0]
    
    chain.show(rgbData)

def drawErrorForTicks(ticks):
    blynk(ticks, [255, 0, 0])

def main():
    global numPRs
    global ticks
    global colorsForNumPRs
    
    wdt = WDT(timeout=15000)
    
    while True:
        wdt.feed()
        # print(ticks)
        
        if wlan.mode() == WLAN.AP:
            drawErrorForTicks(ticks)
            
            ticks += 1
            time.sleep_ms(13)
            continue
        
        # about every 10 s:
        if ticks % (800 // 2) == 0:
            print('load colors')
            colorsForNumPRs = loadSettings(select = "colors")
            print('getting...')
            getAndPrintPRs()
        
        drawForTicks(ticks, numPRs)
        ticks += 1
        time.sleep_ms(13)

main()

# from ws2812 import WS2812
# chain = WS2812(4)
# data = [
#     (100, 0, 0),    # red
#     (0, 100, 0),    # green
#     (0, 0, 100),    # blue
#     (0, 100, 100),   # white
# ]
#
# for i in range(100):
#     chain.show(data)
#     time.sleep_ms(50)
