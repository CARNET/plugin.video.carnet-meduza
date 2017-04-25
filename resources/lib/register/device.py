# -*- coding: utf-8 -*-
import os, sys, string, random, platform
import urllib, urlparse, json
import requests
import xbmc, xbmcaddon
import mechanize
from mechanize import Browser
from modules import control #tnx/credit:https://github.com/shannah/exodus/blob/master/resources/lib/modules/control.py
from classes.memstorage import Storage
from classes.memstorage import MemStorage #tnx/credit: http://romanvm.github.io/script.module.simpleplugin/storage.html

#MemStorage does not allow to modify mutable objects in-place. You need to assign them to variables first, modify and then store them back to a MemStorage instance.
tmp_store = MemStorage('ts')

# get username/apikey from settings
aai_username = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('aai_username')
#api_key = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('apikey')

def gen_key():
	# ex: Linux
	os_name = platform.system()
	# ex: Kodi (some name)
	kodi_name = xbmc.getInfoLabel('System.FriendlyName')
	# generate 140 char device id (a.k.a. api key)
	rnd_str = ''.join(random.choice(string.ascii_letters+string.digits) for x in range(140))
	combo_str = kodi_name + os_name + rnd_str
	# remove non alpha-numeric chars and truncate to 140 
	uniq_key = ''.join(char for char in combo_str if char.isalnum())[:140]
	return uniq_key

def store_key():
	#gen/set/get uniq key == device_id == api_key
	#get addon full path
	plugin_path = xbmcaddon.Addon().getAddonInfo('path').decode('utf-8')
	# Create a storage object
	with Storage(plugin_path) as key_store: 
		if not key_store:
			uniq_key = gen_key() # gen key only if key_store empty (once)
			key_store['uniq_key'] = uniq_key # store object
			key_store['reg_dev_status'] = 'not_reg'
		key = key_store['uniq_key']
		reg_dev_status = key_store['reg_dev_status']
	return (key, reg_dev_status)

# register device
def dev_reg(device_id):
	# get user info from settings
	aai_password = get_pwd()
	api_base_url = 'https://meduza.carnet.hr/index.php/login/mobile/?device='
	device_type_name = xbmcaddon.Addon('plugin.video.carnet-meduza').getSetting('device_type')
	device_type_dict = {'Tablet':'2', 'Smartphone':'3', 'SmartTV':'4'}
	# get number corresponding to device type from settings
	device_type_num = device_type_dict[device_type_name]
	# request target resource, discover IdP and redirect to SSO service
	request_url = api_base_url + device_type_num + '&uid=' + device_id
	r = requests.get(request_url)
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
	br.select_form(name='f')
	br['username'] = aai_username 
	br['password'] = aai_password
	br.method = 'POST'
	br.submit()

	# submit using responded XHTML form, redirect to requested target resource and get response code
	submit = br.open(form_open, timeout=5.0)
	submit.geturl()
	br.select_form(nr=0)
	br.method = 'POST'
	response = br.submit()
	response_url = response.geturl()
	return response_url

# check device registration status
def check_reg(response, device_id):
	response_parsed = urlparse.urlparse(response)
	response_code = urlparse.parse_qs(response_parsed.query)['status'][0]
	# 200 means that 'device' was successfully registered with SP and device UID can be stored in the settings
	if response_code == '200':
		xbmcaddon.Addon('plugin.video.carnet-meduza').setSetting('apikey',device_id)
		user_info(device_id)
		control.infoDialog('Uređaj uspješno registiran')
		#get addon full path
		plugin_path = xbmcaddon.Addon().getAddonInfo('path').decode('utf-8')
		# Create a storage object
		with Storage(plugin_path) as key_store: 
			key_store['reg_dev_status'] = 'is_reg'
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

def pre_run():
	# request target resource, discover IdP and redirect to SSO service
	request_url = 'https://meduza.carnet.hr/index.php/api/registered/?uid=' + api_key
	r = requests.get(request_url)
	registered_status = r.json()['code']
	if registered_status == 200:
		control.infoDialog(r.json()['message'] + ' - looks good!')
	else:
		control.infoDialog('Pogreška. Provjerite postavke ili pokušajte ponovo!')

# get user info and populate the settings.xml
def user_info(api_key):
	# request target resource, discover IdP and redirect to SSO service
	request_url = 'https://meduza.carnet.hr/index.php/api/user/?uid=' + api_key
	r = requests.get(request_url)
	user_details = r.json()
	first_name = user_details['ime'].encode('utf-8')
	last_name = user_details['prezime'].encode('utf-8')
	reg_date = user_details['datum_registracija'].encode('utf-8')
	xbmcaddon.Addon('plugin.video.carnet-meduza').setSetting('first_name',first_name)
	xbmcaddon.Addon('plugin.video.carnet-meduza').setSetting('last_name',last_name)
	xbmcaddon.Addon('plugin.video.carnet-meduza').setSetting('reg_date',reg_date)

api_key, dev_reg_status = store_key()
xbmcaddon.Addon('plugin.video.carnet-meduza').setSetting('apikey',api_key)

# if aai_username missing open settings, otherwise  start device registration
if not aai_username and dev_reg_status == 'not_reg':
	control.infoDialog('Podesite vaš AAI@EduHr Username!')	
	control.openSettings()
elif dev_reg_status == 'not_reg':
	reg_response = dev_reg(api_key)
	check_reg(reg_response, api_key)
#check if device is registered (pre_run) only once
elif not tmp_store:
	pre_run()
	tmp_store['run_once'] = 1
else:
	pass