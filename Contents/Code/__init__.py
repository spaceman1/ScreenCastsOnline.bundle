#
#  __init__.py
#  ScreenCastsOnline
#
#  Created by James Clarke on 01/09/2009.
#  Copyright (c) 2009 Plex. All rights reserved.
#

from PMS import *

SITEMAP_URL   = "http://www.screencastsonline.com/sco_info/info/sitemapcategory.html"
RSS_URL_FREE  = "http://www.screencastsonline.com/feeds/scofree.xml"
RSS_URL_2010  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2010_%s.xml"
RSS_URL_2009  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2009_%s.xml"
RSS_URL_2008  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2008_%s.xml"
RSS_URL_2007  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2007_%s.xml"
RSS_URL_2006  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2006_%s.xml"
RSS_URL_2005  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2005_mixed.xml"
BLACKLIST_URL = "http://www.screencastsonline.com/Extra_Premium/feeds/scoblacklist"

LOGGED_IN = False

def Start():
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")
  MediaContainer.viewGroup = "List"
  MediaContainer.noCache = True
  MediaContainer.art = R("art-default.png")
  DirectoryItem.thumb = R("icon-sco.png")
  VideoItem.thumb = R("icon-sco.png")
  PrefsItem.thumb = R("icon-sco.png")
  HTTP.SetCacheTime(7200)
  Prefs.SetDialogTitle(L("ScreenCastsOnline Preferences"))
  if Dict.Get("blacklist") is None: Dict.Reset()
  LogIn()
  SetTitle1()

def SetTitle1():
  if LOGGED_IN:
    MediaContainer.title1 = L("ScreenCastsOnline Extra!")
  else:
    MediaContainer.title1 = L("ScreenCastsOnline")

def CreateDict():
  Dict.Set("blacklist", [])

def GetVideoDef():
  if Prefs.Get("hd"): return "HD"
  else: return "ED"
  
def UpdateCache():
  if LOGGED_IN:
    videoDef = GetVideoDef()
    HTTP.Request(RSS_URL_2005)
    HTTP.Request(RSS_URL_2006 % videoDef)
    HTTP.Request(RSS_URL_2007 % videoDef)
    HTTP.Request(RSS_URL_2008 % videoDef)
    HTTP.Request(RSS_URL_2009 % videoDef)
    HTTP.Request(RSS_URL_2010 % videoDef)
    UpdateBlacklist()
  else:
    HTTP.Request(RSS_URL_FREE)

def UpdateBlacklist():
  blacklist_json = HTTP.Request(BLACKLIST_URL)
  if blacklist_json is not None:
    try:
      Dict.Set("blacklist", JSON.ObjectFromString(blacklist_json))
    except:
      Dict.Set("blacklist", [])
  else:
    Dict.Set("blacklist", [])

def LogIn():
  global LOGGED_IN
  username = Prefs.Get("username")
  password = Prefs.Get("password")
  if (username != "" and password != ""):
    try:
      # Set the password & request a members-only page
      HTTP.SetPassword("www.screencastsonline.com", Prefs.Get("username"), Prefs.Get("password"))
      result = HTTP.Request("http://www.screencastsonline.com/Extra_Premium/info/overview.html", cacheTime=0)
      if result is not None:
        LOGGED_IN = True
        UpdateBlacklist()
        return True
      else:
        LOGGED_IN = False
        return False
    except:
      LOGGED_IN = False
      return False
  LOGGED_IN = False
  return False
  
def ValidatePrefs():
  LogIn()
  Thread.Create(UpdateCache)
  SetTitle1()
  if not LOGGED_IN:
    return MessageContainer("Unable to log in to ScreenCastsOnline", "The username or password you provided was incorrect.")

@handler("/video/sco", "PLUGIN_NAME")
def MainMenu():
  d = MediaContainer()
  
  # Main menu code for Extra! members
  if LOGGED_IN:
    # Get the video definition
    videoDef = GetVideoDef()
    
    # Add all the items, using the appropriate feeds
    d.Append(Function(DirectoryItem(RSSDirectory, title=L("ScreenCasts from 2010: SCO0232 and above")), url=RSS_URL_2010 % videoDef, label=L("2010")))
    d.Append(Function(DirectoryItem(RSSDirectory, title=L("ScreenCasts from 2009: SCO0181 - SCO0231")), url=RSS_URL_2009 % videoDef, label=L("2009")))
    d.Append(Function(DirectoryItem(RSSDirectory, title=L("ScreenCasts from 2008: SCO0131 - SCO0180")), url=RSS_URL_2008 % videoDef, label=L("2008")))
    d.Append(Function(DirectoryItem(RSSDirectory, title=L("ScreenCasts from 2007: SCO0081 - SCO0130")), url=RSS_URL_2007 % videoDef, label=L("2007")))
    d.Append(Function(DirectoryItem(RSSDirectory, title=L("ScreenCasts from 2006: SCO0027 - SCO0080")), url=RSS_URL_2006 % videoDef, label=L("2006")))
    d.Append(Function(DirectoryItem(RSSDirectory, title=L("ScreenCasts from 2005: SCO0001 - SCO0026")), url=RSS_URL_2005, label=L("2005"), mixed=True))
    #d.Append(PrefsItem(title=L("Preferences")))

  # Main menu code for other users
  else:
    d.Append(Function(DirectoryItem(RSSDirectory, title=L("Recent Free ScreenCasts")), url=RSS_URL_FREE, label=L("Free")))
    d.Append(PrefsItem(title=L("Log in to access ScreenCasts for Extra! members only")))
  return d
  
def RSSDirectory(sender, url, label=None, mixed=False):
  # Check whether we should be using HD versions & create the added_titles array for mixed mode
  HD = Prefs.Get("hd")
  added_titles = []
  
  # Set the container title
  dir = MediaContainer(title2=label)
  
  # Fetch the feed
  feed = XML.ElementFromURL(url)
  
  # Get the blacklist (only used when logged in)
  if LOGGED_IN:
    blacklist = Dict.Get("blacklist")
  else:
    blacklist = []
    
  # Iterate through the feed items
  for item in feed.xpath("//rss/channel/item"):
    # Track whether the item should be added
    should_add = False
    
    # Get the attributes
    title = item.xpath("title")[0].text
    subtitle = item.xpath("pubDate")[0].text
    url = item.xpath("enclosure")[0].get("url")
    
    # Check for a thumbnail
    thumb = None
    thumbEl = item.xpath("media:thumbnail", namespaces={"media":"http://search.yahoo.com/mrss/"})
    if len(thumbEl) > 0:
      thumb = thumbEl[0].get("url")
    
    # Stop if it's an iPod video, or it's a HD video and we're in ED mode
    if title.find("[iPod]") == -1 and (HD or not HD and title.find("[HD]") == -1):
      
      # If logged in, we need to do additional processing
      if LOGGED_IN:
      
        # If the title is blacklisted, stop
        if title not in blacklist:
        
          # If the show identifier not has already been added, add the item
          if title[1:8] not in added_titles:
          
            # Add the show identifier to the added_titles array
            if mixed and HD: added_titles.append(title[1:8])
            should_add = True
            
          # If in HD mode, and a title has already been added, but this item is in HD,
          # remove the previous item & add this one instead
          elif HD and title.find("[HD]") != -1:
            dir.Pop(len(dir)-1)
            should_add = True
      
      # If not logged in, just add the item
      else:
        should_add = True
    
    # If the item should be added, add it
    if should_add:
      # Clean up the title first
      title = title.replace("[HD]","").replace("[DT]","").replace("[ED]", "")
      dir.Append(VideoItem(url, title=title, subtitle=subtitle, thumb=thumb))
    
  return dir
