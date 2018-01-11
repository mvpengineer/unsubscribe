
#path = '/Users/williamdvorak/Desktop/unsubscribe/git/'

#import sys
#sys.path.insert(0, path)
##print sys.path
#import os
#os.environ["PATH"] += os.pathsep +  path

import time
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import random
import log

from selenium.webdriver.common.keys import Keys
delay = .5
pageDelay = 5

checkboxPositives = ['remove', 'stop', 'unsub', 'off', 'opt out', 'not interested']
buttonPositives = ['remove', 'stop', 'unsub', 'go', 'submit', 'click', 'opt out', 'yes', 'update', 'don\'t send me any', 'don\'t send any', 'stop sending', 'confirm', 'do not email', 'block all emails', 'permanently remove']
radioPositives = ['all', 'none', 'complete']
confirmPositives = ['unsubscribed', 'success', 'thank you', 'updated', 'have removed', 'request has been processed', 'request processed', 'unsubscribe confirmation']
shortConfirmPositives = ['successfully unsubscribed', 'confirmed unsubscribed', 'now unsubscribed', 'unsubscribe successful', 'successfully removed', 'unsubscribe confirmation','unsubscribed successfully', 'been unsubscribed']

js_code = "return document.getElementsByTagName('html')[0].innerHTML;"
  
def getBrowser():
  log.info('getting browser')
  from pyvirtualdisplay import Display
  display = Display(visible=0, size=(80, 60))
  display.start()
  browser = webdriver.Firefox()
  #browser.implicitly_wait(1)
  log.info('got browser')
  return browser, display
    
def getBrowserNoDisplay():
  log.info('getting browser')
  browser = webdriver.Firefox()
  #browser.implicitly_wait(1)
  log.info('got browser')
  return browser

def getPageBody(browser):
  aa = browser.execute_script(js_code)
  if aa:
    return aa
  return browser.page_source

def processPage(unsub, browser):
  try:
    browser = process(unsub, browser)
    if browser == 'done':
      return True
    if browser:
      time.sleep(pageDelay)
      body = getPageBody(browser)
      if not body:
        log.info('did not get a confirm page')
        return False
      
      #log.info('got result', body)
      body = body.lower()
      if  any(pos in body for pos in confirmPositives):
        return True
      log.info('no confirmed unsub,', body[:50])
    return False
  except Exception as e:
    log.info('exception'+ str(e))
  return False

#def click(child):
# try:
#   child.click()
#   return browser
# except Exception as e:
#   log.info('exception', e

def getText(child):
  text = child.text.lower()
  if not text or len(text) < 3:
    text = child.get_attribute('alt')
    if text:
      text = text.lower()
  if not text or len(text) < 3:
    text = child.get_attribute('value')
    if text:
      text = text.lower()
  if not text or len(text) < 3:
    text = child.get_attribute('name')
    if text:
      text = text.lower()
  if not text or len(text) < 3:
    text = child.get_attribute('onclick')
    if text:
      text = text.lower()
  if not text or len(text) < 3:
    return None
  return text
  
def getRadioName(radio):
  return radio.get_attribute('name')
  
def process(unsub, browser):
  url = unsub.url
  email = unsub.email
  browser.get(url)
  time.sleep(pageDelay)
  
  body = getPageBody(browser)
  body = body.lower()
  if any(pos in body for pos in shortConfirmPositives):
    return 'done'

  log.info('main frame')
  ans = processFrame(browser, email)
  if ans:
    return ans

  browser.get(url)
  time.sleep(pageDelay)
  frames = browser.find_elements_by_tag_name('iframe')
  frames = list(reversed(frames))
  numFrames = len(frames)
  for i in range(numFrames):
    frame = frames[i]
    log.info('next frame')
    browser.switch_to.frame(frame)
    time.sleep(pageDelay)
    ans = processFrame(browser, email)
    if ans:
      return ans
    # refresh frames list
    browser.get(url)
    time.sleep(pageDelay)
    frames = browser.find_elements_by_tag_name('iframe')
    frames = list(reversed(frames))
  return ans
  
def doFun(fun, args=None):
  try:
    if not args:
      fun()
      return True
    if args:
      fun(args)
      return True
  except Exception as e:
    log.info('exception', e)
  return False

def selects(browser):
  selects = browser.find_elements_by_xpath("//select")
  for select in selects:
    children = select.find_elements_by_xpath("./option")
    clicked = False
    for child in children:
      text = getText(child)
      if any(pos in text for pos in radioPositives):
        if doFun(child.click):
          clicked = True
          log.info('clicked select')
    if not clicked and children:
      if doFun(children[-1].click): # click the last option, usually unsub all
        log.info('clicked select defaulted last')

def radios(browser, unused):
  lists = []
  radios = browser.find_elements_by_xpath("//input[contains(@type, 'radio')]")
  currentList = []
  currentName = None
  if radios:
    currentName = getRadioName(radios[0])
  for radio in radios:
    name = getRadioName(radio)
    if name != currentName:
      lists.append(currentList)
      currentList = []
      currentName = name
    currentList.append(radio)
  lists.append(currentList)
  for l in lists:
    clicked = False
    for radio in l:
      text = getText(radio)
      if any(pos in text for pos in radioPositives):
        if doFun(radio.click):
          clicked = True
          log.info('clicked radio')
    if not clicked and l:
        if doFun(l[-1].click): # click the last option, usually unsub all
          log.info('clicked radio defaulted last')

def ass(browser, unused):
  aTags = browser.find_elements_by_xpath("//a")
  aTags = reversed(aTags)
  for aTag in aTags:
    text = getText(aTag)
    if not text:
      continue
    if not aTag.is_displayed() or not aTag.is_enabled():
      continue
    #log.info(aTag.tag_name, text, aTag.get_attribute('type'))
    if any(pos in text for pos in buttonPositives):
      time.sleep(delay)
      funn = aTag.submit
      if aTag.get_attribute('onclick'):
        funn = aTag.click
      if doFun(funn):
        log.info('a tag submitted')
        return browser
  return None

def buttons(browser, unused):
  buttonTags = browser.find_elements_by_xpath("//button")
  buttonTags = reversed(buttonTags)
  for buttonTag in buttonTags:
    text = getText(buttonTag)
    if not text:
      continue
    if not buttonTag.is_displayed() or not buttonTag.is_enabled():
      continue
    #log.info(buttonTag.tag_name, text, buttonTag.get_attribute('type'))
    if any(pos in text for pos in buttonPositives):
      time.sleep(delay)
      if doFun(buttonTag.click):
        log.info('clicked button')
        return browser
  return None

def onclicks(browser, unused):
  clickTags = browser.find_elements_by_xpath("//*[@onclick]")
  clickTags = reversed(clickTags)
  for clickTag in clickTags:
    text = getText(clickTag)
    if not text:
      continue
    if not clickTag.is_displayed() or not clickTag.is_enabled():
      continue
    #log.info(clickTag.tag_name, text, clickTag.get_attribute('type'))
    if any(pos in text for pos in buttonPositives):
      time.sleep(delay)
      jss = clickTag.get_attribute('onclick')
      browser.execute_script(jss)
      return browser
  return None

def forms(browser, email):
  forms = browser.find_elements_by_xpath("//form")
  forms = reversed(forms)  
  
  for form in forms:
    children = form.find_elements_by_xpath(".//*")
    for child in children:
      text = getText(child)
      if not child.is_displayed() or not child.is_enabled():
        continue
      #log.info(child.tag_name, text, child.get_attribute('type'))  
      if child.tag_name == "input":
        if child.get_attribute('type') == "text":
          doFun(child.clear)
          doFun(child.send_keys,email)
          continue
        if not text:
          continue
        if child.get_attribute('type') == "checkbox":
          if any(pos in text for pos in checkboxPositives) and not child.is_selected():
            if doFun(child.click):
              log.info('clicked checkbox')
          continue
        if child.get_attribute('type') == "button" and any(pos in text for pos in buttonPositives):
          time.sleep(delay)
          if doFun(child.submit):
            return browser
          continue
        if child.get_attribute('type') == "image" and any(pos in text for pos in buttonPositives):
          time.sleep(delay)
          if doFun(child.submit):
            return browser
          continue
        if child.get_attribute('type') == "submit" and any(pos in text for pos in buttonPositives):
          time.sleep(delay)
          doFun(child.submit)
          return browser
      if not text:
        continue
      if child.tag_name == "button" and any(pos in text for pos in buttonPositives):
        time.sleep(delay)
        if doFun(child.submit):
          return browser
        continue
      if child.tag_name == "a" and any(pos in text for pos in buttonPositives):
        time.sleep(delay)
        funn = child.submit
        if child.get_attribute('onclick'):
          funn = child.click
        if doFun(funn):
          log.info('subbimmets a tag')
          return browser
        continue
  return None

def processFrame(browser, email):  
  funs = [radios, forms, ass, buttons, onclicks]
  for ff in funs:
    result = None
    try:
      result = ff(browser, email)
    except Exception as e:
      log.info('exception', e)
    if result:
      return browser
    
  return None

def subbbmit():
  submitTags = browser.find_elements_by_xpath("//*[@onsubmit]")
  submitTags = reversed(submitTags)
  for submitTag in submitTags:
    #log.info(submitTag.tag_name, submitTag.get_attribute('type'))
    time.sleep(delay)
    jss = submitTag.get_attribute('onsubmit')
    browser.execute_script(jss)
    return browser
    
def clickRecursive(elem):
  children = elem.find_elements_by_xpath(".//*")
  children = [elem] + children
  for child in children:
    #log.info(child.tag_name, getText(child))
    return doFun(child.click)
  return False

def refreshBrowser(browser,display):
  body = ''
  try:
    browser.get('https://www.google.com/search?q=check+browser')
    time.sleep(pageDelay)
    body = getPageBody(browser).lower()
  except Exception as e:
    log.warn('refreshing browser', str(e))
  if 'whatsmybrowser.org' not in body:
    browser.quit()
    display.popen.kill()
    time.sleep(2)
    browser,display = getBrowser()
  return browser,display
  
            
  
''' code to consider fixing (grammerly)
  
  
  <span class="_ada80c-title _ada80c-titleNormal _ada80c-pointer" data-reactid="31">Unsubscribe From All Email Lists</span><span class="_ada80c-sub _ada80c-subNormal" data-reactid="32">You will still receive important transactional and billing-related emails</span></div><div class="_74305d-button _610808-button" data-qa="btnUpdate" data-reactid="33">Update my preferences</div>
  
  
'''
  
  