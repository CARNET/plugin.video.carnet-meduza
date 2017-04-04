# -*- coding: utf-8 -*-
import os, sys
import urllib, urlparse
import xbmcgui, xbmcplugin, xbmcaddon
import requests

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])
params = urlparse.parse_qsl(sys.argv[2].replace('?',''))

xbmcplugin.setContent(addon_handle, 'movies')

apiBaseUrl = 'https://meduza.carnet.hr/index.php/api/'
categoryImageBaseUrl = 'https://meduza.carnet.hr/uploads/images/categories/'
apiKey = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('apikey')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def categories():
	requestCategories = requests.get(apiBaseUrl + 'categories/?uid=' + apiKey)
	categories = requestCategories.json()
	return categories

def categoryVideos(name,currentPageNumber):
	for category in categories:
		if category['naziv'] == name:
			skip = int(currentPageNumber) * 25
			categoryId = category['ID']
			requestCategoryVideos = requests.get(apiBaseUrl + 'category/?id=' + categoryId + '&skip=' + str(skip) + '&uid=' + apiKey)
			videos = requestCategoryVideos.json()
        return videos 

#http://stackoverflow.com/questions/6402812/how-to-convert-an-hmmss-time-string-to-seconds-in-python
def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)
		
def listCategoryVideos(videos,currentPageNumber,foldername):
	for video in videos:
		categoryId = video['ID_kategorija']
		videoNum = categoryVideoCount(categoryId)['count']
		name = video['naslov']
		videoId = video['ID']
		duration = get_sec(video['trajanje'])
		dateadded = video['datum_upload']
		playcount = video['pregledi']
		videoInfo = videoUrlDescription(videoId)
		url = videoInfo['stream_url'] + '|User-Agent=Mozilla/5.0&Referer=https://meduza.carnet.hr'
		image = video['slika']
		description = videoInfo['opis'].encode('utf-8')
		li = xbmcgui.ListItem(name, iconImage=image)
		li.setInfo( type="Video", infoLabels={ 
															"Plot": description, 
															"Duration": duration
															})
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
	pagesNum = videoNum / 25
	if int(currentPageNumber) < pagesNum:
		intCurrentPageNumber = int(currentPageNumber)
		intCurrentPageNumber += 1
		currentPageNumber = str(intCurrentPageNumber)
		url = build_url({'mode': 'folder', 'foldername': foldername + '?' + currentPageNumber})
		li = xbmcgui.ListItem('> Next Page', iconImage="DefaultFolder.png")
		xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)		
	xbmcplugin.endOfDirectory(addon_handle)

def categoryVideoCount(categoryId):
	requestCategoryVideoCount = requests.get(apiBaseUrl + 'category/count/?id=' + categoryId + '&uid=' + apiKey)
	categoryVideoCount = requestCategoryVideoCount.json()
	return categoryVideoCount

def videoUrlDescription(videoId):
    requestVideoUrlDescription = requests.get(apiBaseUrl + 'video/?id=' + videoId + '&uid=' + apiKey).json()
    extractKeys = ['stream_url', 'opis']
    videoUrlDescription = dict((k, requestVideoUrlDescription[k]) for k in extractKeys if k in requestVideoUrlDescription)
    return videoUrlDescription

mode = args.get('mode', None)

if mode is None:
    url = build_url({'mode': 'folder', 'foldername': 'Kategorije'})
    li = xbmcgui.ListItem('Kategorije', iconImage='DefaultAddonVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': 'Kanali'})
    li = xbmcgui.ListItem('Kanali', iconImage='DefaultAddonVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': 'Postavke'})
    li = xbmcgui.ListItem('Postavke', iconImage='DefaultAddonProgram.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
	
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder':
	categories = categories()
	if args['foldername'][0] == 'Kategorije':
		categoryGen = (category for category in categories if category['naziv'] != 'YouTube')
		for category in categoryGen:
			name = category['naziv'].encode('utf-8')
			url = build_url({'mode': 'folder', 'foldername': name})
			categoryImage = categoryImageBaseUrl + category['slika']
			li = xbmcgui.ListItem(name, iconImage=categoryImage)
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
		xbmcplugin.endOfDirectory(addon_handle)

	elif args['foldername'][0] == 'Kanali':
		li = xbmcgui.ListItem('Coming soon...I guess' , iconImage='DefaultVideo.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)
                xbmcplugin.endOfDirectory(addon_handle)
	
	elif args['foldername'][0] == 'Postavke':
		from resources.lib.modules import control
		control.openSettings()
	
	else:
		foldername = args['foldername'][0]
		params = args['foldername'][0].strip(foldername + '?')
		if params == '':
			currentPageNumber = '0'
		else:
			currentPageNumber = str(params)
		
		videos =  categoryVideos(foldername.decode('utf-8'),currentPageNumber)
		listCategoryVideos(videos,currentPageNumber,foldername.decode('utf-8'))
