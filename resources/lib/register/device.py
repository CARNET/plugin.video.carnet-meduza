# -*- coding: utf-8 -*-
import os, sys, string, random
import urllib, urlparse, json
import requests
import xbmcaddon
import mechanize
from mechanize import Browser

# get user info from settings
aai_username = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('aai_username')
aai_password = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('aai_password')
device_type_name = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('device_type')
device_type_dict = {'Tablet':'2', 'Smartphone':'3', 'SmartTV':'4'}
# get number corresponding to device type from settings
device_type_num = device_type_dict[device_type_name]
# generate device id
device_id = ''.join(random.choice(string.ascii_letters+string.digits) for x in range(140))

api_base_url = 'https://meduza.carnet.hr/index.php/login/mobile/?device='

# set headers for initial request
REQUEST_HEADER  = {'Host': 'meduza.carnet.hr',
		'Connection': 'keep-alive',
		'Cache-Control': 'max-age=0',
		'Upgrade-Insecure-Requests': '1',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Encoding': 'gzip,deflate',
		'Accept-Language': 'en-US,en;q=0.5'}

# request target resource, discover IdP and redirect to SSO service
request_url = api_base_url + device_type_num + '&uid=' + device_id
r = requests.Session().get(request_url, params=REQUEST_HEADER)
redirect_cookies = r.cookies

# identify the user from requested SSO service (login)
form_open = r.url.encode('utf-8')

# set browser
br = mechanize.Browser()
br.set_cookiejar(redirect_cookies)
br.set_handle_equiv(True)
br.set_handle_redirect(True)
br.set_handle_referer(True)
br.set_handle_robots(False)
br.set_handle_refresh(mechanize._http.HTTPRefreshProcessor(), max_time=1)
# open login page
br.open(form_open)
br.select_form(name="f")
br["username"] = aai_username 
br["password"] = aai_password
br.method = "POST"
br.submit()

# submit using responded XHTML form, redirect to requested target resource and get response code
submit = br.open(form_open, timeout=5.0)
submit.geturl()
br.select_form(nr=0)
br.method = "POST"
response = br.submit()
response_parsed = urlparse.urlparse(response.geturl())
response_code = urlparse.parse_qs(response_parsed.query)['status'][0]

# 200 means that 'device' was successfully registered with SP and device UID can be stored in the settings
if response_code == '200':
	xbmcaddon.Addon('plugin.video.carnet-meduza').setSetting('apikey',device_id)

