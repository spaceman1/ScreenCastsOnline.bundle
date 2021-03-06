#
#  __init__.py
#  ScreenCastsOnline
#
#  Created by James Clarke on 01/09/2009.
#  Copyright (c) 2009 Plex. All rights reserved.
#

import time
from base64 import b64encode

SITEMAP_URL   = "http://www.screencastsonline.com/sco_info/info/sitemapcategory.html"
RSS_URL_FREE  = "http://www.screencastsonline.com/feeds/scofree.xml"
RSS_URL_2011  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2011_%s.xml"
RSS_URL_2010  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2010_%s.xml"
RSS_URL_2009  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2009_%s.xml"
RSS_URL_2008  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2008_%s.xml"
RSS_URL_2007  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2007_%s.xml"
RSS_URL_2006  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2006_%s.xml"
RSS_URL_2005  = "http://www.screencastsonline.com/Extra_Premium/feeds/scoextra_prem_2005_mixed.xml"
BLACKLIST_URL = "http://www.screencastsonline.com/Extra_Premium/feeds/scoblacklist"

####################################################################################################
def Start():
  Plugin.AddPrefixHandler("/video/sco", MainMenu, "ScreenCastsOnline", "icon-default.png", "art-default.jpg")
  Plugin.AddViewGroup("List", viewMode="List", mediaType="items")

  MediaContainer.viewGroup = "List"
  MediaContainer.art = R("art-default.jpg")

  DirectoryItem.thumb = R("icon-sco.png")
  VideoItem.thumb = R("icon-sco.png")
  PrefsItem.thumb = R("icon-sco.png")

  HTTP.CacheTime = 7200
  if Dict["blacklist"] is None: Dict.Reset()

####################################################################################################
def AuthHeader():
  header = {}

  if Prefs["username"] and Prefs["password"]:
    header = {"Authorization": "Basic " + b64encode(Prefs["username"] + ":" + Prefs["password"])}
    Log(header)

  return header

####################################################################################################
def SetTitle1():
  if LoggedIn():
    MediaContainer.title1 = "ScreenCastsOnline Extra!"
  else:
    MediaContainer.title1 = "ScreenCastsOnline"

####################################################################################################
def GetVideoDef():
  if Prefs["hd"]: return "HD"
  else: return "ipod" # Used to be "ED"

####################################################################################################
def UpdateBlacklist():
  blacklist_json = HTTP.Request(BLACKLIST_URL, headers=AuthHeader()).content
  if blacklist_json is not None:
    try:
      blacklist_json = blacklist_json.replace(',\n]', '\n]')
      Dict["blacklist"] = JSON.ObjectFromString(blacklist_json)
    except:
      Dict["blacklist"] = []
  else:
    Dict["blacklist"] = []

####################################################################################################
def LoggedIn():
  try:
    result = HTTP.Request("http://www.screencastsonline.com/Extra_Premium/info/overview.html#" + str(time.time()), cacheTime=0, headers=AuthHeader()).content
    UpdateBlacklist()
    Log(" --> Login successful")
    return True
  except:
    Log(" --> Login failed")
    return False

####################################################################################################
def ValidatePrefs():
  if LoggedIn() == False:
    return MessageContainer("Unable to log in to ScreenCastsOnline", "The username or password you provided is incorrect.")

####################################################################################################
def MainMenu():
  SetTitle1()
  d = MediaContainer(noCache=True)

  # Main menu code for Extra! members
  if LoggedIn():
    # Get the video definition
    videoDef = GetVideoDef()

    # Add all the items, using the appropriate feeds
    d.Append(Function(DirectoryItem(RSSDirectory, title="ScreenCasts from 2011: SCO0283 and above"), url=RSS_URL_2011 % videoDef, label="2011"))
    d.Append(Function(DirectoryItem(RSSDirectory, title="ScreenCasts from 2010: SCO0232 - SCO0282"), url=RSS_URL_2010 % videoDef, label="2010"))
    d.Append(Function(DirectoryItem(RSSDirectory, title="ScreenCasts from 2009: SCO0181 - SCO0231"), url=RSS_URL_2009 % videoDef, label="2009"))
    d.Append(Function(DirectoryItem(RSSDirectory, title="ScreenCasts from 2008: SCO0131 - SCO0180"), url=RSS_URL_2008 % videoDef, label="2008"))
    d.Append(Function(DirectoryItem(RSSDirectory, title="ScreenCasts from 2007: SCO0081 - SCO0130"), url=RSS_URL_2007 % videoDef, label="2007"))
    d.Append(Function(DirectoryItem(RSSDirectory, title="ScreenCasts from 2006: SCO0027 - SCO0080"), url=RSS_URL_2006 % videoDef, label="2006"))
    d.Append(Function(DirectoryItem(RSSDirectory, title="ScreenCasts from 2005: SCO0001 - SCO0026"), url=RSS_URL_2005, label="2005", mixed=True))
    d.Append(PrefsItem(title="Preferences"))

  # Main menu code for other users
  else:
    d.Append(Function(DirectoryItem(RSSDirectory, title="Recent Free ScreenCasts"), url=RSS_URL_FREE, label="Free"))
    d.Append(PrefsItem(title="Log in to access ScreenCasts for Extra! members only"))
  return d

####################################################################################################
def RSSDirectory(sender, url, label=None, mixed=False):
  # Check whether we should be using HD versions & create the added_titles array for mixed mode
  HD = Prefs["hd"]
  logged_in = LoggedIn()
  added_titles = []

  # Set the container title
  dir = MediaContainer(title2=label)

  # Fetch the feed
  feed = XML.ElementFromURL(url, headers=AuthHeader())

  # Get the blacklist (only used when logged in)
  if logged_in:
    blacklist = Dict["blacklist"]
  else:
    blacklist = []

  # Iterate through the feed items
  for item in feed.xpath("/rss/channel/item/enclosure[contains(@type,'video')]/parent::item"): # Ignore audio, pdf, etc.
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

    # If logged in, we need to do additional processing
    if logged_in:

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
      title = title.replace("[HD]","").replace("[DT]","").replace("[ED]","").replace("[iPod]","")
      dir.Append(Function(VideoItem(PlayVideo, title=title, subtitle=subtitle, thumb=Function(GetThumb, url=thumb)), url=url))

  return dir

####################################################################################################
def PlayVideo(sender, url):
  HTTP.SetPassword("www.screencastsonline.com", Prefs["username"], Prefs["password"])
  return Redirect(url)

####################################################################################################
def GetThumb(url):
  if url is not None:
    try:
      data = HTTP.Request(url, cacheTime=CACHE_1MONTH).content
      return DataObject(data, 'image/png')
    except:
      pass

  return Redirect(R("icon-sco.png"))
