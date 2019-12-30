from appJar import gui
import time
from datetime import datetime
import subprocess
import os
from operator import itemgetter
global all_filetypes
global baseRes
global AppInfo
AppInfo = """MagickEditor
version B0.3
made by Anne Mocha (@mocchapi)
github.com/mocchapi/MagickEditor
30/12/2019
"""
all_filetypes = [('images', '*.png'), ('images', '*.jpg'),('images','*.gif'),('images','*.bmp'),('images','*.jpeg'),('All filetypes','*')]
baseRes = 600

app = gui("Magiktest","500x400")
app.setSize('1500x800')
app.setBg("dark gray", override=True,tint=True)
app.setFg("black", override=True)
app.setLocation("CENTER")

app.startSubWindow('secret_sub')
app.addLabel('lbl_og_path',"No image loaded")
app.addLabel('lbl_prevtime','0')
app.stopSubWindow()

def log(loginput, n=None, alert=False):
	loginput = str(loginput).lower().title()
	logtime = datetime.now().strftime('%H:%M:%S')
	if timePassed(180):
		print(('─'*15))
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

def timePassed(amount):
	prevtime = float(app.getLabel('lbl_prevtime'))
	currtime = round(time.time(),3)
	app.setLabel('lbl_prevtime',str(currtime))
	difftime = currtime-prevtime
	if prevtime == 0:
		return False
	elif difftime >= amount:
		return True
	else:
		return False

def get_viewres():
	if app.getCheckBox('box_HDmode'):
		return 1200
	else:
		view_res = round(float(baseRes*(app.getScale("Preview Scale")/100)),2)
		return view_res

def final_scale():
	if app.getCheckBox('box_HDmode'):
		return ''
	else:
		return f'-scale "{get_viewres()}x{get_viewres()}>"'

def editorBtn(button):
	log(f'editor btn: {button}',n=0)
	if button == 'btn_Reorder':
		AutoOrder()
	if button == 'btn_ApplyEffects':
		app.thread(loadPreview)
	if button == 'box_AutoOrder':
		SafeReOrder()


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
	args = []
	#content aware
	if app.getCheckBox('box_ContentAware'):
		order = int(app.getSpinBox('order_ContentAware'))
		CA_scale = app.getScale('scale_ContentAware')
		scaleup = f'{round(100*(1+CA_scale/10),2)}%'
		scaledown = f'{round(1/(1+CA_scale/10)*100,2)}%'
		args = args + [(order,f'-scale {scaleup}x{scaleup} -liquid-rescale {scaledown}x{scaledown}')]
	#rotation
	if app.getCheckBox('box_Rotation'):
		order = int(app.getSpinBox('order_Rotation'))
		args = args + [(order,f'-background "rgba(0,0,0,0)" -fill none -rotate {app.getScale("scale_Rotation")}')]
	#horizontal flip
	if app.getCheckBox('box_Flipping_hor'):
		order = int(app.getSpinBox('order_Flipping'))
		args = args + [(order,f'-flop')]
	#vertical flip
	if app.getCheckBox('box_Flipping_vert'):
		order = int(app.getSpinBox('order_Flipping'))
		args = args + [(order,f'-flip')]
	#implode
	if app.getCheckBox('box_Implode'):
		order = int(app.getSpinBox('order_Implode'))
		implode_val = app.getEntry('entry_Implode')
		if implode_val<0:
			implode_val = implode_val*-1
		args = args + [(order,f'-implode {implode_val}')]
	#explode
	if app.getCheckBox('box_Explode'):
		order = int(app.getSpinBox('order_Explode'))
		explode_val = app.getEntry('entry_Explode')
		if explode_val<0:
			explode_val = explode_val*-1
		explode_val = explode_val*-1
		args = args + [(order,f'-implode {explode_val}')]
	#swirl
	if app.getCheckBox('box_Swirl'):
		order = int(app.getSpinBox('order_Swirl'))
		swirl_val = app.getEntry('entry_Swirl')
		if swirl_val<0:
			swirl_val = swirl_val*-1
		args = args + [(order,f'-swirl {swirl_val}')]
	#sworl
	if app.getCheckBox('box_Sworl'):
		order = int(app.getSpinBox('order_Sworl'))
		sworl_val = app.getEntry('entry_Sworl')
		if sworl_val<0:
			sworl_val = sworl_val*-1
		sworl_val = sworl_val*-1
		args = args + [(order,f'-swirl {sworl_val}')]
	#tile
	if app.getCheckBox('box_Tile'):
		order = int(app.getSpinBox('order_Tile'))
		tileArgs = ''
		for x in range(app.getScale('scale_Tile')):
			tileArgs = f'{tileArgs} -scale 33.33% ( +clone +clone ) +append ( +clone +clone ) -append'
		args = args + [(order,tileArgs)]
	#roll
	if app.getCheckBox('box_Roll'):
		order = int(app.getSpinBox('order_Roll'))
		horizontal = app.getScale('scale_Horizontalroll')
		vertical = app.getScale('scale_Verticalroll')
		args = args + [(order,f'-roll +{horizontal}%+{vertical}%')]
	#scale
	if app.getCheckBox('box_Scale'):
		order = int(app.getSpinBox('order_Scale'))
		if app.getOptionBox('options_Scale') == 'Scale up':
			args = args + [(order,f'-scale {app.getScale("scale_Scale")}%')]
		else:
			args = args + [(order,f'-scale {(1/(app.getScale("scale_Scale")))*10000}%')]
	##no new commands after this##
	#animations
	if app.getCheckBox('box_Animations'):
		order = int(app.getSpinBox('order_Animations'))
		item = app.getOptionBox('options_Animations')
		if item == 'Spin':
			args = args + [(order,f'-duplicate 29  -virtual-pixel none -distort SRT "%[fx:360*t/n]" -set delay "%[fx:t==0?240:10]" -loop 0')]
		elif item == 'Angled Scroll':
			args = args + [(order,f'-duplicate 29  -virtual-pixel tile -distort SRT "0,0 1, 0, %[fx:w*t/n],%[fx:h*t/n]" -set delay 10 -loop 0')]
	#custom arguments
	try:
		custom_args = app.getEntry("Custom arguments")
		if custom_args == 'none' or custom_args == '' or custom_args == None:
			log('No custom arguments',n=0)
		else:
			log(f'custom arguments: {custom_args}',n=0)
			args = args + [(1000,f'{custom_args}')]
	except BaseException as e:
		log(e,n=2)
	###end of args
	log(f'Arguments collected',n=1)
	args.sort(key = lambda pair: pair[0])
	args = map(itemgetter(1), args)
	args = " ".join(tuple(args))
	if args == '':
		log(f'No arguments',n=0)
	else:
		log(f'Arguments:{args}',n=0)
	return args

def generateOriginal(path_input):
	log("generating og image")
	try:
		try:
			os.system(f'magick convert "{path_input}" {final_scale()} "temp_og.gif"')
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
		log(f'full command: magick "temp_og.gif" {str(args)} {final_scale()} "temp_pv.gif"')
		magick_output = os.system(f'magick "temp_og.gif" {str(args)} {final_scale()} "temp_pv.gif"')
		if magick_output > 0:
			raise Exception
		log('preview generated',n=0)
		return 'temp_pv.gif'
	except Exception as e:
		if e != None or e != '':
			log(e,n=2)
		if app.getEntry('Custom arguments') == '':
			log(f'Magick error, check python log.',n=2,alert=True)
		else:
			log(f'Magick error, check custom arguments.',n=2,alert=True)
		return 'image_loading_error.gif'


def loadOriginal(path_input):
	app.setImageSize("original_image", get_viewres(),get_viewres())
	app.reloadImage("original_image", generateOriginal(path_input))
	return None

def loadPreview():
	app.setImageSize("preview_image", get_viewres(),get_viewres())
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
		if app.getEntry('Custom arguments') == '':
			log(f'Magick error, check python log.',n=2,alert=True)
		else:
			log(f'Magick error, check custom arguments.',n=2,alert=True)
	else:
		log(f'Sucessfully exported to {new_path}',n=1,alert=True)

def AppAddScale(name,start,end,y=0,x=1,interval=None,current=None,increment=None,label=None):
	if label != None:
		app.addLabel(f'scalelbl_{name}',label,y,x)
		x=x+1
	app.addScale(f'scale_{name}',y,x)
	if current==None:
		current = start
	app.setScaleRange(f'scale_{name}', start,end,curr=current)
	app.showScaleValue(f'scale_{name}')
	app.setScaleLength(f'scale_{name}',10)
	app.setScaleWidth(f'scale_{name}',10)
	if interval == None:
		interval = end-start
	app.showScaleIntervals(f'scale_{name}', interval)
	if increment != None:
		app.setScaleIncrement(f'scale_{name}',increment)

def AppStartEffect(name,label=None,y=5,x=0):
	if label == None:
		label = name
	app.startLabelFrame(f'frame_{name}',label=label)
	app.addNamedCheckBox('Enable',f'box_{name}', 0,0)
	app.addLabel(f'lbl_order{name}','Order:',y+1,x)
	app.addSpinBoxRange(f'order_{name}',0,999,y+1,x+1,reverse=True)

def SafeReOrder(verbal=False):
	log('Checking if safe to re-order')
	boxes = app.getAllSpinBoxes()
	autoOrdered = app.getCheckBox('box_AutoOrder')
	if autoOrdered:
		autoOrdered = False
	else:
		autoOrdered = True
	order = 0
	mismatch = False
	for name,value in boxes.items():
		if autoOrdered:
			if verbal:
				print(f'{value}=={order}?')
			if value != str(order):
				mismatch = True
				if verbal:
					print('mismatch')
		else:
			if verbal:
				print(f'{value}==0?')
			if value != '0':
				mismatch = True
				if verbal:
					print('mismatch')
		order+=1
	log('Check completed',n=1)
	if mismatch == False:
		log('Safe to re-order',n=0)
		AutoOrder()
	else:
		log('Unsafe to re-order, no action taken.',n=0)


def AutoOrder():
	log('Ordering effects')
	boxes = app.getAllSpinBoxes()
	enabled = app.getCheckBox('box_AutoOrder')
	order = 0
	for name in boxes:
		if enabled:
			app.setSpinBox(name,order)
			order+=1
		else:
			app.setSpinBox(name,0)
	if enabled:
		log(f'Ordered 0-{order-1}',n=1)
	else:
		log('All orders set to 0',n=1)



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

app.stopFrame()

###prefrences window
app.startSubWindow('preferences', transient=True)
app.setTransparency(90)
app.setBg("dark gray", override=True,tint=True)
app.setFg("black", override=True)
app.setSize(300, 400)
app.setSticky('new')
app.setStretch('column')
app.addLabelScale("Preview Scale")
app.setScaleRange("Preview Scale", 5, 150, curr=100)
app.showScaleValue("Preview Scale")
app.addNamedCheckBox('HD mode','box_HDmode')
app.addNamedCheckBox('Automatic effect ordering','box_AutoOrder')
app.setCheckBoxChangeFunction('box_AutoOrder',editorBtn)
app.setCheckBox('box_AutoOrder', ticked=True,callFunction=False)
app.setStretch('')
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
app.setSize(330, 400)
app.setSticky('nesw')
app.setStretch('both')
app.setTransparency(90)
app.startScrollPane('effects_scroll',disabled='horizontal')
#content aware
AppStartEffect('ContentAware','Content Aware')
AppAddScale('ContentAware',0,10,current=5)
app.stopLabelFrame()
#rotation
AppStartEffect('Rotation')
AppAddScale('Rotation',0,360,increment=45)
app.stopLabelFrame()
#flipping
AppStartEffect('Flipping')
app.addNamedCheckBox('Horizontal','box_Flipping_hor',0,1)
app.addNamedCheckBox('Vertical','box_Flipping_vert',1,1)
app.stopLabelFrame()
#implode
AppStartEffect('Implode')
app.addNumericEntry('entry_Implode',0,1)
app.setEntry('entry_Implode',0.5)
app.setEntryMaxLength('entry_Implode',5)
app.stopLabelFrame()
#explode
AppStartEffect('Explode')
app.addNumericEntry('entry_Explode',0,1)
app.setEntry('entry_Explode',0.5)
app.setEntryMaxLength('entry_Explode',5)
app.stopLabelFrame()
#swirl
AppStartEffect('Swirl')
app.addNumericEntry('entry_Swirl',0,1)
app.setEntry('entry_Swirl',50)
app.setEntryMaxLength('entry_Swirl',5)
app.stopLabelFrame()
#sworl
AppStartEffect('Sworl')
app.addNumericEntry('entry_Sworl',0,1)
app.setEntry('entry_Sworl',50)
app.setEntryMaxLength('entry_Sworl',5)
app.stopLabelFrame()
#tile
AppStartEffect('Tile')
AppAddScale('Tile',0,5,current=1)
app.stopLabelFrame()
##roll
AppStartEffect('Roll')
AppAddScale('Horizontalroll',0,100,increment=10,label='Horizontal Roll',y=1,x=0)
AppAddScale('Verticalroll',0,100,increment=10,label='Vertical Roll',y=2,x=0)
app.stopLabelFrame()
#scale 
AppStartEffect('Scale')
AppAddScale('Scale',100,1000,interval=900,increment=50)
app.addOptionBox('options_Scale',['Scale up','Scale down'],1,1)
app.stopLabelFrame()
##animations
AppStartEffect('Animations')
app.addOptionBox('options_Animations',['Spin','Angled Scroll'],1,1)
app.stopLabelFrame()
#final
app.stopScrollPane()
app.setSticky('esw')
app.setStretch('column')
app.startFrame('effects_bottom')
app.addNamedButton("Re-order",'btn_Reorder', editorBtn,0,0)
app.addNamedButton("Apply effects",'btn_ApplyEffects',editorBtn,0,2)
app.stopFrame()
app.stopSubWindow()

app.showSubWindow('effectsWindow')
view_res = baseRes*(app.getScale("Preview Scale")/100)
log(f'Resolution: {view_res}',n=0)
AutoOrder()
app.go()
