from appJar import gui
import time
from datetime import datetime
import subprocess
import os

global all_filetypes
global baseRes
global AppInfo
AppInfo = """MagickTest
version B0.2
made by Anne Mocha
19/12/2019
This is not even close to complete.
"""
all_filetypes = [('images', '*.png'), ('images', '*.jpg'),('images','*.gif'),('images','*.bmp'),('images','*.jpeg'),('All filetypes','*')]
baseRes = 600

app = gui("Magiktest","1500x800")
app.setBg("dark gray", override=True,tint=True)
app.setFg("black", override=True)


def log(loginput, n=None, alert=False):
	loginput = str(loginput).lower()
	logtime = datetime.now().strftime('%H:%M:%S')
	if n==2:
		print(f'[{logtime}] [-!-] {loginput}')
		if alert:
			app.warningBox('Error',loginput)
	else:
		if alert:
			app.infoBox('Info',loginput)
		if n==None:
			print(f'[{logtime}] [...] {loginput}')
		elif n==0:
			print(f'[{logtime}] [-i-] {loginput}')
		elif n==1:
			print(f'[{logtime}] [-✓-] {loginput}')



def editorBtn(button):
	button = button.lower()
	log(f'editor btn: {button}',n=0)
	if button == 'fuckupBtn':
		randomizeEffects()
	if button == 'apply effects':
		app.thread(loadPreview)

def randomizeEffects():
	return None

def tbFunc(button):
	button = button.lower()
	log(f'toolbar btn: {button}',n=0)
	if button == 'open':
		og_path = selectFile()
		if og_path != '' and og_path !=():
			loadOriginal(og_path)
			app.thread(loadPreview)
		else:
			log(f'No file selected',n=0)
	if button == 'save':
		log(f'Save box open')
		try:
			export_path = app.saveBox(title='Save',fileExt='.png',fileTypes=all_filetypes)
		except BaseException as e:
			log(f'{e}',n=2)
		if export_path == '' or export_path==():
			log(f'Save cancelled',n=0)
		else:
			log(f'Save path: {export_path}')
			app.infoBox('Info','Saving, please wait a moment')
			app.thread(saveFile,export_path)
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
		app.thread(loadPreview)

def collect_args():
	log('collecting arguments')
	args = ''
	try:
		custom_args = app.getEntry("Custom arguments")
		if custom_args == '':
			log('No custom arguments',n=0)
		else:
			log(f'custom arguments: {custom_args}',n=0)
		args = f'{args} {custom_args}'
	except BaseException as e:
		log(e,n=2)
	if app.getCheckBox('box_ContentAware'):
		CA_scale = app.getScale('scale_ContentAware')
		scaleup = f'{round(100*(1+CA_scale/10),2)}%'
		scaledown = f'{round(1/(1+CA_scale/10)*100,2)}%'
		args = f'{args} -scale {scaleup}x{scaleup} -liquid-rescale {scaledown}x{scaledown}'
	if app.getCheckBox('box_Rotation'):
		args = f'{args} -background \'rgba(0,0,0,0)\' -rotate {app.getScale("scale_Rotation")}'
	if app.getCheckBox('box_flipping_hor'):
		args = f'{args} -flop'
	if app.getCheckBox('box_flipping_vert'):
		args = f'{args} -flip'
	if app.getCheckBox('box_implode'):
		implode_val = app.getEntry('entry_implode')
		if implode_val<0:
			implode_val = implode_val*-1
		args = f'{args} -implode {implode_val}'
	if app.getCheckBox('box_explode'):
		explode_val = app.getEntry('entry_explode')
		if explode_val<0:
			explode_val = explode_val*-1
		explode_val = explode_val*-1
		args = f'{args} -implode {explode_val}'
	log(f'Arguments collected',n=1)
	log(f'Arguments: {args}',n=0)
	return args

def generateOriginal(path_input):
	log("generating og image")
	try:
		try:
			os.system(f'magick convert "{path_input}" -scale {view_res}x{view_res} "temp_og.gif"')
		except BaseException as e:
			log(e,n=2)
		app.setLabel("lbl_og_path",path_input)
		return 'temp_og.gif'
	except BaseException as e:
		log(e,n=2)
		return 'image_loading_error.gif'

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
		args = collect_args()
		app.reloadImage("preview_image", 'loading.gif')
		log(f'full command: magick "temp_og.gif" {str(args)} -scale {view_res}x{view_res} "temp_pv.gif"')
		magick_output = os.system(f'magick "temp_og.gif" {str(args)} -scale {view_res}x{view_res} "temp_pv.gif"')
		if magick_output > 0:
			raise Exception
		log('preview generated')
		return 'temp_pv.gif'
	except Exception as e:
		log('Magick error: check custom arguments.',n=2,alert=True)
		return 'image_loading_error.gif'


def loadOriginal(path_input):
	app.setImageSize("original_image", view_res,view_res)
	app.reloadImage("original_image", generateOriginal(path_input))
	return None

def loadPreview():
	app.setImageSize("preview_image", view_res,view_res)
	app.reloadImage("preview_image", generatePreview())
	return None

def selectFile():
	log('file select window')
	file = app.openBox(title='Select File', fileTypes=all_filetypes)
	if file != '':
		log(f'path to file: {file}',n=0)
	else:
		log(f'No new file selected',n=0)
	return file

def saveFile(new_path):
	log(f'Saving as {new_path}')
	if '.' not in new_path:
		log(f'No file extenstion, defaulting to png',n=1)
		new_path = f'{new_path}.png'
	args = collect_args()
	og_path = app.getLabel('lbl_og_path')
	magick_output = os.system(f'magick "{og_path}" {args} "{new_path}"')
	if magick_output >0:
		log(f'Magick error, check custom arguments.',n=2,alert=True)
	else:
		log(f'Sucessfully exported to {new_path}',n=1,alert=True)


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
app.setSticky('')
#left big frame (og image)
app.addImage("original_image", 'no_image_loaded.gif')
app.stopLabelFrame()

app.startLabelFrame("bigRIGHT",label='preview image',row=0,column=2)
#rgiht big frame (preview image)
app.setSticky('n')
app.setSticky('')
app.addImage("preview_image", 'no_image_loaded.gif')
app.stopLabelFrame()

app.setStretch('column')
app.setSticky('sew')
app.startFrame('bottomFrame', 2, 0, 3)
app.startFrame('bottomleft', 0,0)
app.setSticky('wne')
app.addLabelEntry("Custom arguments")
app.stopFrame()

#app.startFrame('bottomcenter',0,1)
#app.setSticky('en')
#app.addLabel('bottom', 'The little part')
#app.stopFrame()

#app.startFrame('bottomright',0,2)
#app.setSticky('en')
#app.stopFrame()
app.stopFrame()

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
#bottom button
app.setSticky('sew')
app.startFrame('preferences_bottom')
app.addButton("Apply",refresh_images)
app.stopFrame()
app.stopSubWindow()


##effects window
app.startSubWindow('effectsWindow', title="Effects",transient=True)
app.setBg("dark gray", override=True,tint=True)
app.setFg("black", override=True)
app.setSize(300, 400)
app.setSticky('nesw')
app.setStretch('both')
app.setTransparency(90)
app.startScrollPane('effects_scroll')
#content aware
app.startLabelFrame('frame_ContentAware',label='Content Aware')
app.addNamedCheckBox('Enable','box_ContentAware', 0,0)
app.addScale('scale_ContentAware',0,1)
app.setScaleRange('scale_ContentAware', 0,10,curr=5)
app.showScaleValue('scale_ContentAware')
app.setScaleLength('scale_ContentAware',10)
app.setScaleWidth('scale_ContentAware',10)
app.showScaleIntervals('scale_ContentAware', 10)
app.stopLabelFrame()
#rotation
app.startLabelFrame('frame_rotation', label='Rotation')
app.addNamedCheckBox('Enable','box_Rotation', 0,0)
app.addScale('scale_Rotation',0,1)
app.setScaleRange('scale_Rotation', 0,360,curr=0)
app.showScaleValue('scale_Rotation')
app.setScaleLength('scale_Rotation',10)
app.setScaleWidth('scale_Rotation',10)
app.showScaleIntervals('scale_Rotation', 180)
app.setScaleIncrement('scale_Rotation',45)
app.stopLabelFrame()
#flipping
app.startLabelFrame('frame_flipping', label='Flipping')
app.addNamedCheckBox('Horizontal','box_flipping_hor')
app.addNamedCheckBox('Vertical','box_flipping_vert')
app.stopLabelFrame()
#implode
app.startLabelFrame('frame_implode',label='Implode')
app.addNamedCheckBox('Enable','box_implode',0,0)
app.addNumericEntry('entry_implode',1,0)
app.setEntry('entry_implode',0.5)
app.setEntryMaxLength('entry_implode',5)
app.stopLabelFrame()
#explode
app.startLabelFrame('frame_explode',label='Explode')
app.addNamedCheckBox('Enable','box_explode',0,0)
app.addNumericEntry('entry_explode',1,0)
app.setEntry('entry_explode',0.5)
app.setEntryMaxLength('entry_explode',5)
app.stopLabelFrame()

app.stopScrollPane()
app.setSticky('esw')
app.setStretch('column')
app.startFrame('effects_bottom')
app.addNamedButton("Randomize",'fuckupBtn', editorBtn,0,0)
app.addButton("Apply effects",editorBtn,0,2)
app.stopFrame()
app.stopSubWindow()

app.startSubWindow('secret_sub')
app.addLabel('lbl_og_path',"No image loaded")
app.stopSubWindow()

app.showSubWindow('effectsWindow')
view_res = 600*(app.getScale("Preview Scale")/100)
log(f'Resolution: {view_res}',n=0)

app.go()
