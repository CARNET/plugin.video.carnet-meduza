# -*- coding: utf-8 -*-
import os, sys, string, random
import urllib, urlparse, json
import requests
import xbmc, xbmcaddon
import mechanize
from mechanize import Browser
from modules import control #tnx/credit:https://github.com/shannah/exodus/blob/master/resources/lib/modules/control.py

# generate device id and get username/apikey from settings
device_id = ''.join(random.choice(string.ascii_letters+string.digits) for x in range(140))
aai_username = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('aai_username')
api_key = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('apikey')

# register device
def dev_reg():
	# get user info from settings
	aai_password = get_pwd()
	api_base_url = 'https://meduza.carnet.hr/index.php/login/mobile/?device='
	REQUEST_HEADER  = {'Host': 'meduza.carnet.hr',
		'Connection': 'keep-alive',
		'Cache-Control': 'max-age=0',
		'Upgrade-Insecure-Requests': '1',
		'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/57.0.2987.133 Safari/537.36',
		'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
		'Accept-Encoding': 'gzip,deflate',
		'Accept-Language': 'en-US,en;q=0.5'}

	device_type_name = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('device_type')
	device_type_dict = {'Tablet':'2', 'Smartphone':'3', 'SmartTV':'4'}
	# get number corresponding to device type from settings
	device_type_num = device_type_dict[device_type_name]

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
	response_url = response.geturl()
	return response_url

# check device registration status
def check_reg(response):
	response_parsed = urlparse.urlparse(response)
	response_code = urlparse.parse_qs(response_parsed.query)['status'][0]
	# 200 means that 'device' was successfully registered with SP and device UID can be stored in the settings
	if response_code == '200':
		xbmcaddon.Addon('plugin.video.carnet-meduza').setSetting('apikey',device_id)
		control.infoDialog("Uređaj uspješno registiran")
	else: 
		ret_codes = {'100':'Nedostaje UID parametar', '300':'Korisnički račun je istekao', '400':'Neuspješna registracija', '401':'Uređaj  je već registriran'}
		ret_message = ret_codes[response_code]
		control.infoDialog(ret_message)
	
def get_pwd():
	keyboard = xbmc.Keyboard()
	keyboard.setHeading('AAI@EduHr lozinka')
	keyboard.setHiddenInput(True) 
	keyboard.doModal()
	if (keyboard.isConfirmed()):
		enter_pwd = keyboard.getText()
		if enter_pwd is None or len(str(enter_pwd)) == 0:
			control.infoDialog('Pogrešan unos. Pokušajte ponovo!')
	del keyboard
	return enter_pwd

if api_key  == '':
	if aai_username == '':
		control.openSettings()
	else:
		reg_response = dev_reg()
		check_reg(reg_response)

