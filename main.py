from datetime import datetime,timedelta
from types import *
from xbmcswift2 import Plugin
from xbmcswift2 import actions
import HTMLParser
import StringIO
import json
import os
import re
import requests
import sys
import time
import urllib
import xbmc,xbmcaddon,xbmcvfs,xbmcgui
import xbmcplugin
import zipfile
from rpc import RPC
#xbmc.log(repr(sys.argv))

plugin = Plugin()


big_list_view = False

def log(x):
    xbmc.log(repr(x))

def get_icon_path(icon_name):
    addon_path = xbmcaddon.Addon().getAddonInfo("path")
    return os.path.join(addon_path, 'resources', 'img', icon_name+".png")

def remove_formatting(label):
    label = re.sub(r"\[/?[BI]\]",'',label)
    label = re.sub(r"\[/?COLOR.*?\]",'',label)
    return label
    
    
@plugin.route('/play/<url>')
def play(url):
    xbmc.executebuiltin('PlayMedia(%s)' % url)    
    
@plugin.route('/record/<url>')
def record(url):
    core = "record"
    xbmc.executebuiltin('PlayWith(%s)' % core)
    xbmc.executebuiltin('PlayMedia(%s)' % url)      
    
@plugin.route('/folder/<id>/<path>')
def folder(id,path):
    response = RPC.files.get_directory(media="files", directory=path, properties=["thumbnail"])
    files = response["files"]
    dirs = dict([[remove_formatting(f["label"]), f["file"]] for f in files if f["filetype"] == "directory"])
    links = {}
    thumbnails = {}
    for f in files:
        if f["filetype"] == "file":
            label = remove_formatting(f["label"])
            file = f["file"]
            while (label in links):
                label = "%s." % label
            links[label] = file
            thumbnails[label] = f["thumbnail"]

    items = []

    for label in sorted(dirs):
        path = dirs[label]
        context_items = []

        fancy_label = "[B]%s[/B]" % label
        items.append(
        {
            'label': fancy_label,
            'path': plugin.url_for('folder',id=id, path=path),
            'thumbnail': get_icon_path('tv'),
            'context_menu': context_items,
        })

    for label in sorted(links):
        context_items = []
        #path = plugin.url_for('play', id=id, path=links[label])
        #xbmc.log(path)
        #context_items.append(("[COLOR yellow][B]%s[/B][/COLOR] " % 'Play', 'XBMC.RunPlugin(%s)' % (path)))
        items.append(
        {
            'label': label,
            'path': plugin.url_for('record',url=links[label]),
            'thumbnail': thumbnails[label],
            'context_menu': context_items,
        })
    return items    
    
@plugin.route('/plugins')
def plugins():
    all_addons = []
    for type in ["xbmc.addon.video", "xbmc.addon.audio"]:
        response = RPC.addons.get_addons(type=type,properties=["name", "thumbnail"])
        if "addons" in response:
            found_addons = response["addons"]
            all_addons = all_addons + found_addons

    seen = set()
    addons = []
    for addon in all_addons:
        if addon['addonid'] not in seen:
            addons.append(addon)
        seen.add(addon['addonid'])

    items = []


    addons = sorted(addons, key=lambda addon: remove_formatting(addon['name']).lower())
    for addon in addons:
        label = addon['name']
        id = addon['addonid']
        path = "plugin://%s" % id
        context_items = []
        fancy_label = "[B]%s[/B]" % label
        items.append(
        {
            'label': fancy_label,
            'path': plugin.url_for('folder',id=id, path=path),
            'thumbnail': get_icon_path('tv'),
            #'context_menu': context_items,
        })
    return items
    

@plugin.route('/')
def index():
    context_items = []
    items = []

    items.append(
    {
        'label': "Record",
        'path': plugin.url_for('plugins'),
        'thumbnail':get_icon_path('movies'),
        'context_menu': context_items,
    })


    return items

if __name__ == '__main__':
    plugin.run()
    if big_list_view == True:
        view_mode = int(plugin.get_setting('view_mode'))
        plugin.set_view_mode(view_mode)
