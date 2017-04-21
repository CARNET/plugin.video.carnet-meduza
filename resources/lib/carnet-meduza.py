# -*- coding: utf-8 -*-
import os, sys
import urllib, urlparse, json
import xbmcgui, xbmcplugin, xbmcaddon
import requests

if xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('apikey') == '':
	from register import device
	ret_code = device.response_code 

base_url = sys.argv[0]
addon_handle = int(sys.argv[1])
args = urlparse.parse_qs(sys.argv[2][1:])

xbmcplugin.setContent(addon_handle, 'videos')

api_base_url = 'https://meduza.carnet.hr/index.php/api/'
category_image_base_url = 'https://meduza.carnet.hr/uploads/images/categories/'
api_key = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('apikey')

def build_url(query):
    return base_url + '?' + urllib.urlencode(query)

def categories():
	requestCategories = requests.get(api_base_url + 'categories/?uid=' + api_key)
	categories = requestCategories.json()
	return categories

def channels():
	requestChannels = requests.get(api_base_url + 'channels/?uid=' + api_key)
	channels = requestChannels.json()
	return channels

def category_videos(name,current_page_number):
	for category in categories:
		if category['naziv'] == name:
			skip = int(current_page_number) * 25
			category_id = category['ID']
			request_category_videos = requests.get(api_base_url + 'category/?id=' + category_id + '&skip=' + str(skip) + '&uid=' + api_key)
			videos = request_category_videos.json()
        return videos 

def search_videos():
	keyboard = xbmc.Keyboard()
        keyboard.setHeading('Pretraži CARNet Meduza')
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		query = keyboard.getText()
		if query is None or len(str(query)) == 0:
			return
	else:
		return
	request_search_videos = requests.get(api_base_url + 'videos/?query=' + query + '&order=3' + '&uid=' + api_key)
	videos = request_search_videos.json()
	return videos 

def category_video_count(category_id):
	request_category_video_count = requests.get(api_base_url + 'category/count/?id=' + category_id + '&uid=' + api_key)
	category_video_count = request_category_video_count.json()
	return category_video_count

def video_url_description(video_id):
	request_video_url_description = requests.get(api_base_url + 'video/?id=' + video_id + '&uid=' + api_key).json()
	extract_keys = ['stream_url', 'opis']
	video_url_description = dict((k, request_video_url_description[k]) for k in extract_keys if k in request_video_url_description)
	return video_url_description

#TODO: add to settings option 'number of recommends' 
def recommended_videos():
	request_recommended_videos = requests.get(api_base_url + 'recommended/?number=20&uid=' + api_key)
	videos = request_recommended_videos.json()
	return videos 

def list_search_or_recommended_videos(videos):
	if videos == None:
		return
	else:	
		for video in videos:
			category_id = video['ID_kategorija']
			name = video['naslov']
			video_id = video['ID']
			genre = video['kategorija']
			duration = reduce(lambda x, y: x*60+y, [int(i) for i in (video['trajanje'].replace(':',',')).split(',')])
			video_info = video_url_description(video_id)
			try:
				url = video_info['stream_url'].encode('utf-8') + '|User-Agent=Mozilla/5.0&Referer=https://meduza.carnet.hr'
				description = video_info['opis'].encode('utf-8')
			except KeyError:
				url = ''
				description = 'Video nije moguće reproducirati. Stari prijenos uživo?'
				pass		
			image = video['slika']
			li = xbmcgui.ListItem(name, iconImage=image)
			li.setInfo( type="Video", infoLabels={ 
							"Plot": description, 
							"Genre": genre,
							"Duration": duration
								})
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
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
			duration = reduce(lambda x, y: x*60+y, [int(i) for i in (video['trajanje'].replace(':',',')).split(',')])
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
		
def start_channel(channel_id,channel_video_count):
	playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
	player = xbmc.Player()
	playlist.clear()
	requestChannel = requests.get(api_base_url + 'channel/?id=' + channel_id + '&uid=' + api_key)
	channel = requestChannel.json()
	channel_index = channel['index']
	schedule = channel['raspored']
	channel_offset = channel['offset']
	schedule_gen = ((i, j) for i, j in enumerate(schedule))
	for i, j in schedule_gen:
	        li = xbmcgui.ListItem(j['naslov'], 'label1', thumbnailImage = j['slika'])
		itemArgs = {
                'title': j['naslov'].encode('utf-8'),
                'plot': j['opis'].encode('utf-8'),
                'tracknumber': i 
            	}
		li.setInfo('video', itemArgs)
		playlist.add(url=j['stream_url'],listitem=li)
        player.play(item=playlist,startpos=channel_index)
	player.seekTime(channel_offset)

mode = args.get('mode', None)

if mode is None:
    url = build_url({'mode': 'folder', 'foldername': 'Preporuke'})
    li = xbmcgui.ListItem('Preporuke', iconImage='DefaultVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': 'Kategorije'})
    li = xbmcgui.ListItem('Kategorije', iconImage='DefaultAddonVideo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'folder', 'foldername': 'Kanali'})
    li = xbmcgui.ListItem('Kanali', iconImage='DefaultAddonTvInfo.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)

    url = build_url({'mode': 'search', 'foldername': 'Pretraga'})
    li = xbmcgui.ListItem('Pretraga', iconImage='DefaultAddonsSearch.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
	
    url = build_url({'mode': 'settings', 'foldername': 'Postavke'})
    li = xbmcgui.ListItem('Postavke', iconImage='DefaultAddonProgram.png')
    xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
	
    xbmcplugin.endOfDirectory(addon_handle)

elif mode[0] == 'folder':
	if args['foldername'][0] == 'Preporuke':
		videos =  recommended_videos()
		list_search_or_recommended_videos(videos)

	elif args['foldername'][0] == 'Kategorije':
		categories = categories()
		categoryGen = (category for category in categories if category['naziv'] != 'YouTube')
		for category in categoryGen:
			name = category['naziv'].encode('utf-8')
			url = build_url({'mode': 'folder', 'foldername': name})
			categoryImage = category_image_base_url + category['slika']
			li = xbmcgui.ListItem(name, iconImage=categoryImage)
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li, isFolder=True)
		xbmcplugin.endOfDirectory(addon_handle)

	elif args['foldername'][0] == 'Kanali':
		channels = channels()
		channelGen = (channel for channel in channels if channel['naziv'] != 'UNWANTED')
		for channel in channelGen:
			name = channel['naziv'].encode('utf-8')
			url = build_url({'mode': 'folder', 'foldername': name})
			try:
				channelImage = channel['slika']
			except KeyError:
				channelImage = ''
				pass		
			li = xbmcgui.ListItem(name, iconImage=channelImage)
			xbmcplugin.addDirectoryItem(handle=addon_handle, url=url, listitem=li)
		xbmcplugin.endOfDirectory(addon_handle)

	else:
		categories = categories()
		channels = channels()
		foldername = args['foldername'][0]
		#api response is 'list of dictionaries' so using lambda is nice way of checking for values
		if filter(lambda name: name['naziv'] == foldername.decode('utf-8'), categories):
			if not 'pagenumber' in args:
				current_page_number = '0'
			else:
				current_page_number = args['pagenumber'][0] 
			videos =  category_videos(foldername.decode('utf-8'),current_page_number)
			list_category_videos(videos,current_page_number,foldername.decode('utf-8'))
		else:
			channel = filter(lambda name: name['naziv'] == foldername.decode('utf-8'), channels)
			channel_id = channel[0]['ID'].encode('utf-8')
			channel_video_count = channel[0]['emisije'].encode('utf-8')
			start_channel(channel_id,channel_video_count)

elif mode[0] == 'search':
	videos = search_videos()
	list_search_or_recommended_videos(videos)

elif mode[0] == 'settings':		
	#https://github.com/shannah/exodus/blob/master/resources/lib/modules/control.py
	from modules import control
	control.openSettings()