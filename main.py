from appJar import gui
import time
from datetime import datetime
import subprocess
import os

global AppInfo
AppInfo = """MagickTest
version B0.2
made by Anne Mocha
19/12/2019
This is not even close to complete.
"""


app = gui("Magiktest","1500x800")
app.setBg("dark gray", override=True,tint=True)
app.setFg("black", override=True)


def log(loginput, n=None, alert=False):
	loginput = str(loginput).lower()
	logtime = datetime.now().strftime('%H:%M:%S')
	if n==None:
		print(f'[{logtime}] [...] {loginput}')
	elif n==0:
		print(f'[{logtime}] [-i-] {loginput}')
	elif n==1:
		print(f'[{logtime}] [-✓-]')
	elif n==2:
		print(f'[{logtime}] [-!-] {loginput}')
		if alert:
			app.warningBox('Error',loginput)



def editorBtn(button):
	button = button.lower()
	log(f'editor btn: {button}')
	if button == 'fuckupBtn':
		fuckupEffects()
	if button == 'apply effects':
		app.thread(loadPreview)

def fuckupEffects():
	return None

def tbFunc(button):
	button = button.lower()
	log(f'toolbar btn: {button}',n=0)
	if button == 'open':
		og_path = selectfile()
		if og_path != '':
			loadOriginal(og_path)
			loadPreview()
	if button == 'settings':
		app.showSubWindow("preferences")
	if button == 'refresh':
		refresh_images()
	if button == 'about':
		openAbout()
	if button == 'wizard':
		app.showSubWindow('effectsWindow')

def refresh_images():
	log('refreshing images')
	log('removing temp files')
	try:
		os.remove('temp_pv.gif')
		os.remove('temp_og.gif')
		log('temp files removed',n=0)
	except BaseException as e:
		log(e,n=2)

	og_path = app.getLabel("lbl_og_path")
	if og_path != "No image loaded":
		loadOriginal(og_path)
	pv_path = app.getLabel("lbl_pv_path")
	if pv_path != "No image generated":
		app.thread(loadPreview)

def generateOriginal(path_input):
	log("generating og image")
	try:
		res_quality = app.getScale("Preview Scale")
		try:
			os.system(f'magick convert "{path_input}" -scale {res_quality}%x{res_quality}% "temp_og.gif"')
		except BaseException as e:
			log(e,n=2)
		app.setLabel("lbl_og_path",path_input)
		return 'temp_og.gif'
	except BaseException as e:
		log(e,n=2)
		return 'image_loading_error.gif'

def collect_args():
	log('collecting arguments')
	try:
		custom_args = app.getEntry("Custom arguments")
		log(f'custom arguments: {custom_args}',n=0)
		return custom_args
	except BaseException as e:
		log(e,n=2)
		return ''

def generatePreview():
	log('generating preview')
	try:
		try:
			log('removing old temp_pv.gif')
			os.remove('temp_pv.gif')
		except BaseException as e:
			log(e,n=2)
		og_image = app.getLabel("lbl_og_path")
		if og_image == "No image loaded":
			log('No original image loaded', n=2)
			return 'no_image_loaded.gif'
		res_quality = app.getScale("Preview Scale")
		args = collect_args()
		app.reloadImage("preview_image", 'loading.gif')
		magick_output = os.system(f'magick "{og_image}" {str(args)} -scale {res_quality}%x{res_quality}% "temp_pv.gif"')
		if magick_output > 0:
			log('Magick error: likely bad args',n=2)
			raise Exception
		log('preview generated')
		return 'temp_pv.gif'
	except Exception as e:
		return 'image_loading_error.gif'


def loadOriginal(path_input):
	res_quality = app.getScale("Preview Scale")
	app.setImageSize("original_image", 900*res_quality/100,900*res_quality/100)
	app.reloadImage("original_image", generateOriginal(path_input))
	return None

def loadPreview():
	res_quality = app.getScale("Preview Scale")
	app.setImageSize("preview_image", 900*res_quality/100,900*res_quality/100)
	app.reloadImage("preview_image", generatePreview())
	return None

def selectfile():
	log('file select window')
	file = app.openBox(title='Select File', fileTypes=[('images', '*.png'), ('images', '*.jpg')])
	if file != '':
		log(f'path to file: {file}',n=0)
	else:
		log(f'No new file selected',n=0)
	return file


def openAbout():
	app.infoBox('About',AppInfo)

tools = ["OPEN", "SAVE", "REFRESH", "WIZARD",
        "SETTINGS", "PRINT", "ABOUT"]

app.addToolbar(tools, tbFunc, findIcon=True)

app.setStretch('both')
app.setSticky('news')
#'The big part'
app.startLabelFrame("bigLEFT",label='original image',row=0,column=0)
app.setSticky('n')
app.addLabel('lbl_og_path',"No image loaded")
app.setSticky('')
#left big frame (og image)
app.addImage("original_image", 'no_image_loaded.gif')
app.addLabel("left big area")
app.stopLabelFrame()

app.startLabelFrame("bigRIGHT",label='preview image',row=0,column=2)
#rgiht big frame (preview image)
app.setSticky('n')
app.addLabel('lbl_pv_path',"No image loaded")
app.setSticky('')
app.addImage("preview_image", 'no_image_loaded.gif')
app.addLabel("rigth big area")
app.stopLabelFrame()

app.setStretch('column')
app.setSticky('sew')
app.startFrame('bottomFrame', 2, 0, 3)
app.startFrame('bottomleft', 0,0)
app.setSticky('wne')
app.addLabelEntry("Custom arguments")
app.addNamedButton("Just fuck my shit up",'fuckupBtn', editorBtn)
app.stopFrame()

app.startFrame('bottomcenter',0,1)
app.setSticky('en')
app.addLabel('bottom', 'The little part')
app.stopFrame()

app.startFrame('bottomright',0,2)
app.setSticky('en')
app.addButton("Apply effects",editorBtn)
app.stopFrame()
app.stopFrame()

##effects window
app.startSubWindow('effectsWindow', title="Effects <NONFUNCTIONAL>",transient=True)
app.setBg("dark gray", override=True,tint=True)
app.setFg("black", override=True)
app.setSize(300, 400)
app.setSticky('new')
app.setStretch('column')
app.setTransparency(90)
app.startScrollPane('effects_scroll')
app.startLabelFrame('frame_ContentAware',label='Content Aware')
app.setSticky('new')
app.setStretch('column')
app.addNamedCheckBox('Enable','eff_ContentAware', 0,0)
app.addScale('scale_ContentAware',0,1)
app.setScaleRange('scale_ContentAware', 1,10,curr=1)
app.showScaleValue('scale_ContentAware')
app.setScaleLength('scale_ContentAware',10)
app.setScaleWidth('scale_ContentAware',10)
app.stopLabelFrame()
app.stopScrollPane()
app.stopSubWindow()

###prefrences window
app.startSubWindow('preferences', transient=True)
app.setTransparency(90)
app.setBg("dark gray", override=True,tint=True)
app.setFg("black", override=True)
app.setSize(300, 400)
app.setSticky('new')
app.addLabelScale("Preview Scale")
app.setScaleRange("Preview Scale", 5, 150, curr=100)
app.showScaleValue("Preview Scale")

app.setSticky('sew')
app.startFrame('preferences_bottom')
app.addButton("Apply",refresh_images)
app.stopFrame()
app.stopSubWindow()

app.showSubWindow('effectsWindow')

app.go()