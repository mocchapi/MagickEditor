from appJar import gui
import time
from datetime import datetime
import subprocess
import os
import sys
from operator import itemgetter
import configparser
version='1.2.0'
AppInfo = f"""MagickEditor
version {version}
made by Anne Mocha (@mocchapi)
github.com/mocchapi/MagickEditor
"""
all_filetypes = [('images', '*.png'), ('images', '*.jpg'),('images','*.gif'),('images','*.bmp'),('images','*.jpeg'),('All filetypes','*')]
baseRes = 600
config= configparser.ConfigParser()

app = gui("MagickEditor CANARY","500x400",handleArgs=False)
app.setSize('1500x800')
app.setBg("dark gray", override=True,tint=True)
app.setFg("black", override=True)
app.setLocation("CENTER")

app.startSubWindow('secret_sub')
app.addLabel('lbl_og_path',"No image loaded")
app.addLabel('lbl_prevtime','0')
app.addLabel('lbl_terminalcommand','magick')
app.stopSubWindow()


def logThreadAlert(logtype,loginput):
	if logtype==2:
		app.warningBox('Error',loginput)
	else:
		app.infoBox('Info',loginput)

def log(loginput, n=None, alert=False,child=False):
	loginput = str(loginput)
	logtime = datetime.now().strftime('%H:%M:%S')
	if timePassed(600):
		print(('─'*30))
	if alert:
		app.thread(logThreadAlert,n,loginput)
	if n==None:
		indicator='[...]'
	elif n==0:
		indicator='[-i-]'
	elif n==1:
		indicator='[-✓-]'
	elif n==2:
		indicator='[-!-]'
	if child:
		print(f'[{logtime}]   ┕{indicator} {loginput}')
	else:
		print(f'[{logtime}] {indicator} {loginput}')

def collectPlugins(folderName='Plugins'):
	log('Collecting plugins...')
	folder = os.listdir(folderName)
	config = configparser.ConfigParser()
	plugins = []
	for file in folder:
		if file.lower().endswith('.ames'):
			plugins = plugins + [f'{folderName}/{file}']
	log('Plugins collected',n=1)
	log(f'Plugin list:{plugins}',n=0)
	return plugins


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
	if button == 'box_IM6Compatibility':
		if app.getCheckBox('box_IM6Compatibility'):
			log('compatibility mode on',n=0)
			app.setLabel('lbl_terminalcommand','convert')
		else:
			log('compatibility mode off',n=0)
			app.setLabel('lbl_terminalcommand',' magick')

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
			app.thread(saveFile,export_path)
			app.infoBox('Info','Saving, please wait a moment')
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
	removeTemps()
	log('temp files removed',n=0)
	og_path = app.getLabel("lbl_og_path")
	if og_path != "No image loaded":
		loadOriginal(og_path)
		app.thread(loadPreview)

def collect_args():
	log('collecting arguments')
	args = []
	##Plugins
	for plugin in plugins:
		pluginFile=open(plugin)
		config.read_file(pluginFile)
		pluginName = config['info']['name']
		order = int(app.getSpinBox(f'order_{config["info"]["name"]}'))
		if app.getCheckBox(f'box_{config["info"]["name"]}'):
			log(f'Loading plugin effect for {plugin}')
			output=config['output']['output']
			outputVar=output
			for section in config.sections():
				if section.startswith('input:'):
					if section[6:].startswith('optionbox'):
						try:
							outputVar = outputVar.replace(f'<{section}>',str(app.getOptionBox(f'optionbox_{pluginName}_{section[16:]}')))
						except BaseException as e:
							pass
					if section[6:].startswith('scale:'):
						try:
							outputVar = outputVar.replace(f'<{section}>',str(app.getScale(f'scale_{pluginName}_{section[12:]}')))
						except BaseException as e:
							pass
			if '<' in outputVar and '>' in outputVar:
				log(f'Potential unhandled variable: "{outputVar}"',n=2,child=True)
			args = args + [(order,outputVar)]
		pluginFile.close()


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
	#invert
	if app.getCheckBox('box_Invert'):
		order = int(app.getSpinBox('order_Invert'))
		args = args + [(order,'-channel RGB -negate')]
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

	#spread
	if app.getCheckBox('box_Spread'):
		order = int(app.getSpinBox('order_Spread'))
		spreadVal = app.getScale('scale_Spread')
		args = args + [(order,f'-spread {spreadVal}')]
	#fuzzy
	if app.getCheckBox('box_Fuzzy'):
		order = int(app.getSpinBox('order_Fuzzy'))
		Fuz_scale = app.getScale('scale_Fuzzy')
		if Fuz_scale >0:
			scaleup = f'{round((100*(Fuz_scale*2)),2)}%'
			scaledown = f'{round((1/(Fuz_scale*2))*100,2)}%'
			args = args + [(order,f'-resize {scaledown} -resize {scaleup}')]
	#pixelate
	if app.getCheckBox('box_Pixelate'):
		order = int(app.getSpinBox('order_Pixelate'))
		Pix_scale = app.getScale('scale_Pixelate')
		if Pix_scale >0:
			scaleup = f'{round((100*(Pix_scale*2)),2)}%'
			scaledown = f'{round((1/(Pix_scale*2))*100,2)}%'
			args = args + [(order,f'-scale {scaledown} -scale {scaleup}')]
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
			os.system(f'{app.getLabel("lbl_terminalcommand")} "{path_input}" {final_scale()} "temp_og.gif"')
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
			removeTemps(exclude='temp_og.gif')
		except BaseException as e:
			log(e,n=2)
		og_image = app.getLabel("lbl_og_path")
		if og_image == "No image loaded":
			log('No original image loaded', n=2)
			return 'no_image_loaded.gif'
		args = collect_args()
		app.reloadImage("preview_image", 'loading.gif')
		log(f'full command: {app.getLabel("lbl_terminalcommand")} "temp_og.gif" {str(args)} {final_scale()} "temp_pv.gif"',n=0)
		magick_output = os.system(f'{app.getLabel("lbl_terminalcommand")} "temp_og.gif" {str(args)} {final_scale()} "temp_pv.gif"')
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
	magick_output = os.system(f'{app.getLabel("lbl_terminalcommand")} "{og_path}" {args} "{new_path}"')
	if magick_output >0:
		if app.getEntry('Custom arguments') == '':
			log(f'Magick error, check python log.',n=2,alert=True)
		else:
			log(f'Magick error, check custom arguments.',n=2,alert=True)
	else:
		log(f'Sucessfully exported to {new_path}',n=1,alert=True)


scaleList = ['start','end','x','interval','current','increment','label']
def AppAddScale(name,start,end,y=None,x=1,interval=None,current=None,increment=None,label=None,single=True,tooltip=None):
	if label != None:
		app.addLabel(f'scalelbl_{name}',label,y,x)
		x=x+1
		single=False
	if y==None:
		if single==True:
			y=0
		else:
			row=app.getRow()
			if row==1:
				row=row+1
			y=row
	try:
		app.addScale(f'scale_{name}',y,x)
		if tooltip!=None:
			app.setScaleTooltip(f'scale_{name}',tooltip)
			app.enableScaleTooltip(f'scale_{name}')
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
	except BaseException as e:
		log(e,n=2)

def appAddOptionbox(name,optionList,label=None,single=True,x=1,tooltip=None):
	if label != None:
		app.addLabel(f'optionboxlbl_{name}',y,x)
		x=x+1
		single=False
	if single == True:
		y=0
	else:
		row=app.getRow()
		if row ==1:
			row=row+1
		y=row
	app.addOptionBox(f'optionbox_{name}',optionList,y,x)
	if tooltip!=None:
		app.setOptionBoxTooltip(f'optionbox_{name}',tooltip)
		app.enableOptionBoxTooltip(f'optionbox_{name}')

def AppStartEffect(name,label=None,author='unknown',version='unknown'):
	if label == None:
		label = name
	app.startLabelFrame(f'frame_{name}',label=label)
	app.addNamedCheckBox('Enable',f'box_{name}', 0,0)
	app.setCheckBoxTooltip(f'box_{name}',f'{name}\nBy: {author}\nVersion: {version}')
	app.enableCheckBoxTooltip(f'box_{name}')

def AppStopEffect(name,x=0):
	y=app.getRow()+10
	app.addLabel(f'lbl_order{name}','Order:',y,x)
	app.addSpinBoxRange(f'order_{name}',0,999,y,x+1,reverse=True)
	app.stopLabelFrame()

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
				log(f'{value}=={order}?')
			if value != str(order):
				mismatch = True
				if verbal:
					log('mismatch')
		else:
			if verbal:
				log(f'{value}==0?')
			if value != '0':
				mismatch = True
				if verbal:
					log('mismatch')
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

def removeTemps(exclude='None'):
	try:
		if os.path.exists('temp_pv.gif') and 'temp_pv.gif'!=exclude:
			os.remove('temp_pv.gif')
		if os.path.exists('temp_og.gif') and 'temp_og.gif'!=exclude:
			os.remove('temp_og.gif')
	except BaseException as e:
		log(e,n=2)

def checkStop():
	removeTemps()
	return True



tools = ["OPEN", "SAVE", "REFRESH", "WIZARD",
        "SETTINGS", "ABOUT"]

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
if os.name != 'posix':
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
app.addNamedCheckBox('ImageMagick v6 compatibility mode','box_IM6Compatibility')
app.setCheckBoxChangeFunction('box_IM6Compatibility',editorBtn)
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
if os.name != 'posix':
	app.setTransparency(90)
app.startScrollPane('effects_scroll',disabled='horizontal')

##plugins babey!!
plugins = collectPlugins()
usedSectionNames = []
for plugin in plugins:
	log(f'Loading plugin UI for {plugin}')
	modules=0
	pluginFile=open(plugin)
	config.read_file(pluginFile)
	pluginName = config['info']['name']
	AppStartEffect(pluginName,author=config['info']['author'],version=config['info']['version'])
	for section in config.sections():
		if section.startswith('input:'):
			if section[6:].startswith('optionbox:'):
				optionbox=config[section]
				try:
					tooltip=optionbox['tooltip']
				except:
					tooltip=None
				if modules>0:
					single=False
				appAddOptionbox(f'{pluginName}_{section[16:]}',optionbox['options'].split(','),single=single,tooltip=tooltip)
				modules=modules+1
			if section[6:].startswith('scale:') and section not in usedSectionNames:
				scale=config[section]
				try:
					tooltip=scale['tooltip']
				except:
					tooltip=None
				try:
					current=scale['current']
				except:
					current=None
				try:
					interval=scale['interval']
				except:
					interval=None
				try:
					increment=scale['increment']
				except:
					increment=None
				if modules>0:
					single=False
				else:
					single=True
				AppAddScale(f'{pluginName}_{section[12:]}',int(scale['start']),int(scale['end']),current=current,interval=interval,increment=increment,single=single,tooltip=tooltip)
				usedSectionNames.append(section)
				modules=modules+1
	pluginFile.close()
	log('Loaded.',n=0,child=True)
	AppStopEffect(pluginName)

#content aware
AppStartEffect('ContentAware','Content Aware')
AppAddScale('ContentAware',0,10,current=5)
AppStopEffect('ContentAware')
#rotation
AppStartEffect('Rotation')
AppAddScale('Rotation',0,360,increment=45)
AppStopEffect('Rotation')
#flipping
AppStartEffect('Flipping')
app.addNamedCheckBox('Horizontal','box_Flipping_hor',0,1)
app.addNamedCheckBox('Vertical','box_Flipping_vert',1,1)
AppStopEffect('Flipping')
#implode
AppStartEffect('Implode')
app.addNumericEntry('entry_Implode',0,1)
app.setEntry('entry_Implode',0.5)
app.setEntryMaxLength('entry_Implode',5)
AppStopEffect('Implode')
#explode
AppStartEffect('Explode')
app.addNumericEntry('entry_Explode',0,1)
app.setEntry('entry_Explode',0.5)
app.setEntryMaxLength('entry_Explode',5)
AppStopEffect('Explode')
#invert
AppStartEffect('Invert')
AppStopEffect('Invert')
#swirl
AppStartEffect('Swirl')
app.addNumericEntry('entry_Swirl',0,1)
app.setEntry('entry_Swirl',50)
app.setEntryMaxLength('entry_Swirl',5)
AppStopEffect('Swirl')
#sworl
AppStartEffect('Sworl')
app.addNumericEntry('entry_Sworl',0,1)
app.setEntry('entry_Sworl',50)
app.setEntryMaxLength('entry_Sworl',5)
AppStopEffect('Sworl')
#tile
AppStartEffect('Tile')
AppAddScale('Tile',0,5,current=1)
AppStopEffect('Tile')
##roll
AppStartEffect('Roll')
AppAddScale('Horizontalroll',0,100,increment=10,label='Horizontal Roll',y=1,x=0)
AppAddScale('Verticalroll',0,100,increment=10,label='Vertical Roll',y=2,x=0)
AppStopEffect('Roll')
#scale
AppStartEffect('Scale')
AppAddScale('Scale',100,1000,interval=900,increment=50)
app.addOptionBox('options_Scale',['Scale up','Scale down'],1,1)
AppStopEffect('Scale')
#Spread
AppStartEffect('Spread')
AppAddScale('Spread',0,30,increment=1)
AppStopEffect('Spread')
##fuzzy
AppStartEffect('Fuzzy')
AppAddScale('Fuzzy',0,10,increment=1)
AppStopEffect('Fuzzy')
##Pixelate
AppStartEffect('Pixelate')
AppAddScale('Pixelate',0,10,increment=1)
AppStopEffect('Pixelate')
##animations
AppStartEffect('Animations')
app.addOptionBox('options_Animations',['Spin','Angled Scroll'],1,1)
AppStopEffect('Animations')
#final (No ui code below)
app.stopScrollPane()
app.setSticky('esw')
app.setStretch('column')
app.startFrame('effects_bottom')
app.addNamedButton("Re-order",'btn_Reorder', editorBtn,0,0)
app.addNamedButton("Apply effects",'btn_ApplyEffects',editorBtn,0,2)
app.stopFrame()
app.stopSubWindow()

##final initialisation
app.showSubWindow('effectsWindow')
view_res = baseRes*(app.getScale("Preview Scale")/100)
log(f'Resolution: {view_res}',n=0)

try:
	system.os('magick -version')
	log(f'Running ImageMagick v7+, no compatibility needed')
	app.setCheckBox('box_IM6Compatibility',ticked=False)
except:
	log(f'Running ImageMagick v6, compatibility mode enabled')
	app.setCheckBox('box_IM6Compatibility',ticked=True)

app.setStopFunction(checkStop)
AutoOrder()
log(f'Initialisation completed.',n=1)

terminalArgs=sys.argv
if len(terminalArgs)>1:
	log(f'Loading {terminalArgs[1]} via commandline',n=0)
	loadOriginal(terminalArgs[1])
	app.thread(loadPreview)
app.go()
