# -*- coding: utf-8 -*-
import os, sys
import urllib, urlparse
import xbmcgui, xbmcplugin, xbmcaddon
import requests

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'movies')

api_base_url = 'https://meduza.carnet.hr/index.php/api/'
category_image_base_url = 'https://meduza.carnet.hr/uploads/images/categories/'
api_key = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('apikey')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

#http://stackoverflow.com/questions/6402812/how-to-convert-an-hmmss-time-string-to-seconds-in-python
def get_sec(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + int(s)

def categories():
	requestCategories = requests.get(api_base_url + 'categories/?uid=' + api_key)
	categories = requestCategories.json()
	return categories

def category_videos(name,current_page_number):
	for category in categories:
		if category['naziv'] == name:
			skip = int(current_page_number) * 25
			category_id = category['ID']
			request_category_videos = requests.get(api_base_url + 'category/?id=' + category_id + '&skip=' + str(skip) + '&uid=' + api_key)
			videos = request_category_videos.json()
        return videos 

#TODO: add to settings option 'number of recommends' 
def recommended_videos():
	request_recommended_videos = requests.get(api_base_url + 'recommended/?number=20&uid=' + api_key)
	videos = request_recommended_videos.json()
	return videos 

def list_recommended_videos(videos):
	for video in videos:
		category_id = video['ID_kategorija']
		name = video['naslov']
		video_id = video['ID']
		duration = get_sec(video['trajanje'])
		video_info = video_url_description(video_id)
		#xbmc.log("AAAAAAAAAAAAAAAAAAAAAA: %r" % video_info, xbmc.LOGNOTICE)
		#url = video_info['stream_url'].encode('utf-8') + '|User-Agent=Mozilla/5.0&Referer=https://meduza.carnet.hr'
		#description = video_info['opis'].encode('utf-8')
		#url = ''
		#description = ''
		image = video['slika']
		#li = xbmcgui.ListItem(name, iconImage=image)
		#li.setInfo( type="Video", infoLabels={ 
		#					"Plot": description, 
		#					"Duration": duration
		#						})
		#xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
		li = xbmcgui.ListItem(name, iconImage=image)
		xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)
	xbmcplugin.endOfDirectory(addon_handle)

def list_category_videos(videos,current_page_number,foldername):
	if not videos:
		li = xbmcgui.ListItem('Trenutno nema video u ovoj kategoriji...' , iconImage='DefaultVideo.png')
		xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)
		xbmcplugin.endOfDirectory(addon_handle)
	else:
		for video in videos:
			category_id = video['ID_kategorija']
			video_num = category_video_count(category_id)['count']
			name = video['naslov']
			video_id = video['ID']
			duration = get_sec(video['trajanje'])
			dateadded = video['datum_upload']
			playcount = video['pregledi']
			video_info = video_url_description(video_id)
			url = video_info['stream_url'] + '|User-Agent=Mozilla/5.0&Referer=https://meduza.carnet.hr'
			image = video['slika']
			description = video_info['opis'].encode('utf-8')
			li = xbmcgui.ListItem(name, iconImage=image)
			li.setInfo( type="Video", infoLabels={ 
								"Plot": description, 
								"Duration": duration
								})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
	
		pages_num = video_num / 25
		if int(current_page_number) < pages_num:
			int_current_page_number = int(current_page_number)
			int_current_page_number += 1
			current_page_number = str(int_current_page_number)
			url = build_url({'mode': 'folder', 'foldername': foldername, 'pagenumber': current_page_number})
			li = xbmcgui.ListItem('> Next Page (' + str(int_current_page_number + 1) + ')', iconImage="DefaultFolder.png")
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)		
		xbmcplugin.endOfDirectory(addon_handle)

def category_video_count(category_id):
	request_category_video_count = requests.get(api_base_url + 'category/count/?id=' + category_id + '&uid=' + api_key)
	category_video_count = request_category_video_count.json()
	return category_video_count

def video_url_description(video_id):
	request_video_url_description = requests.get(api_base_url + 'video/?id=' + video_id + '&uid=' + api_key).json()
	extract_keys = ['stream_url', 'opis']
	video_url_description = dict((k, request_video_url_description[k]) for k in extract_keys if k in request_video_url_description)
	return video_url_description

mode = args.get('mode', None)

if mode is None:
    url = build_url({'mode': 'folder', 'foldername': 'Preporuka'})
    li = xbmcgui.ListItem('Preporuka', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': 'Kategorije'})
    li = xbmcgui.ListItem('Kategorije', iconImage='DefaultAddonVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': 'Kanali'})
    li = xbmcgui.ListItem('Kanali', iconImage='DefaultAddonTvInfo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': 'Pretraga'})
    li = xbmcgui.ListItem('Pretraga', iconImage='DefaultAddonsSearch.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
	
    url = build_url({'mode': 'folder', 'foldername': 'Postavke'})
    li = xbmcgui.ListItem('Postavke', iconImage='DefaultAddonProgram.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
	
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder':
	categories = categories()
	if args['foldername'][0] == 'Preporuka':
		videos =  recommended_videos()
		list_recommended_videos(videos)
		#li = xbmcgui.ListItem('Coming soon...I guess' , iconImage='DefaultVideo.png')
		#xbmcplugin.addDirectoryItem(handle=addon_handle, url='', listitem=li)
		#xbmcplugin.endOfDirectory(addon_handle)
	
	elif args['foldername'][0] == 'Kategorije':
		categoryGen = (category for category in categories if category['naziv'] != 'YouTube')
		for category in categoryGen:
			name = category['naziv'].encode('utf-8')
			url = build_url({'mode': 'folder', 'foldername': name})
			categoryImage = category_image_base_url + category['slika']
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
		if not 'pagenumber' in args:
			current_page_number = '0'
		else:
			current_page_number = args['pagenumber'][0] 
		videos =  category_videos(foldername.decode('utf-8'),current_page_number)
		list_category_videos(videos,current_page_number,foldername.decode('utf-8'))

