#!/usr/bin/env
'''
Fetch lyrics corresponding to each music file in the given directory
Usage : python attach-lyrics.py <path-to-folder>
Author : Abhishek Kandoi
File Formats Supported : mp3 ogg flac m4a
TODO : add support for aiff aif wma
'''

from LyricsParser import Parser
from Relevance import score
import tagpy
from mutagen.mp4 import MP4
import re
import os
import argparse
import gdata.youtube
import gdata.youtube.service
import json
import urllib2
from pprint import pprint

'''
	Cleans text, does the following
		replace & with and
		remove unwanted symbols
		extract name from string of form "eminem (ft. rihanna)" to "eminem"
		extract name from string of form "eminem - recovery" to "eminems"
		remove "ft. <artist>"
		remove numberings like 15.just Lose it
		remove [dot] from the start of the text
		replace multiple whitespaces with a single whitespace
		strip off the extra whitespaces from start and end

		Example:
			" 1.space  bound (eminem) - recovery " becomes "space bound"
'''
def clean_text(text):
	#replace & with and
	text = re.sub(r'&', r'and', text)

	#remove unwanted symbols
	text = re.sub(r'[^0-9a-zA-Z .\'()-]', r'', text)

	#extract name from string of form "eminem (ft. rihanna)" to "eminem"
	text = re.sub(r'\(.*\)', r'', text)

	#extract name from string of form "eminem - recovery" to "eminems"
	text = re.sub(r'-.*', r'', text)	

	#remove "ft. <artist>"
	text = re.sub(r' ft\. .*', r'', text)

	#for those cases when name starts with n. where n is a number
	#example 15.just Lose It should become just lose it
	text = re.sub(r'([0-9]*)\.', r'', text)

	#for those cases when name starts with a .
	text = re.sub(r'\.(.*)', r'\1', text)

	#replace multiple whitespaces with a single whitespace
	text = re.sub(r'  *', r' ', text)

	#strip off the extra whitespaces from start and end
	text = text.strip()
	return text

'''
	Creates a .lyrics file corresponding to an audio file
	
	Example:
		createFile("/home/abhi", "space bound.mp3", "I am a spacebound rocketship and your hearts the moon")
		will create a file "space bound.lyrics" in the folder /home/abhi with the given lyrics
'''
def createFile(pathtofolder, audiofile, lyrics):
	try:
		file = open(os.path.join(pathtofolder, os.path.splitext(audiofile)[0] + ".lyrics"), 'w')
		file.write(lyrics)
		file.close()
		return True
	except IOError:
		return False

'''
	Get artist name using apple itunes generated json data
	returns artist name if found otherwise "Not Found"

	Example:
		itunes_getartist("space bound", "eminem123") returns eminem
'''
def itunes_getartist(title, artist):
	url = "https://itunes.apple.com/search?term=" + title.replace(" ", "+");
	page = urllib2.urlopen(url, None, 10)
	json_data = page.read().strip()
	#write json data to temporary file
	temp_file = open("music.json", "w")
	temp_file.write(json_data)
	temp_file.close()
	with open('music.json') as data_file:
		data = json.load(data_file)
	#pprint(data)
	#print "Result Count:", data["resultCount"]
	max_score = 0
	artistName = ""
	trackName = ""
	#find the best match for artist name using the title name
	for track in data["results"]:
		if track.has_key("trackName"):
			#print "Comparing", artist, "with", track["artistName"]
			if score(artist, track["artistName"]) > max_score:
				max_score = score(artist, track["artistName"])
				artistName = track["artistName"]
				trackName = track["trackName"]
	if max_score > 0.25:
		#print artistName, ":", trackName
		return artistName
	else:
		#print "Score:", max_score ," ",artistName, ":", trackName
		return "Not Found"

'''
	Get artist name from youtube search result
	Not using for now
'''
'''
def yt_getartist(title):
	client = gdata.youtube.service.YoutubeService()
	query = gdata.youtube.service.YoutubeVideoQuery()
	query.vq = title
	query.orderby = 'relevance'
	query.max_results = 3
	query.start_index = 1
	query.racy = 'include'
	#query.format = 

	#perform youtube query
	feed = client.YoutubeQuery(query)
	print feed.entry

	#extract name of first youtube entry
	firstEntry = feed.entry[0]
	entryTitle = firstEntry.media.title.text

	#seperate artist name and song title
	end = entryTitle.find("-")
	keyword1 = entryTitle[:end].strip().lower()
	keyword2 = entryTitle[end+1:].strip().lower()
	#string.

	return artist, title
'''

#Parse the argument for the location of the directory
parser = argparse.ArgumentParser(description='Fetch lyrics corresponding to each music file in the given directory')
parser.add_argument('pathtofolder')
args = parser.parse_args()
pathtofolder = args.pathtofolder

#testing phase variable
#pathtofolder = "/home/abhi/ACDC"

#supported media extensions
exts = [".mp3", ".ogg", ".flac", ".m4a"]

#list all the audio files in the folder
audio_list = [ audiofile for audiofile in os.listdir(pathtofolder) if os.path.isfile(os.path.join(pathtofolder, audiofile)) and (os.path.splitext(audiofile)[1] in exts) ]

#variables to keep track of statistics
found = 0
not_found = 0
#keep track of replaced title and artist name
#replaced = []

#fetch lyrics corresponding to each audio file
for audiofile in audio_list:
	lyrics_found = False

	#complete path to the song
	path = os.path.join(pathtofolder, audiofile)

	if(os.path.splitext(audiofile)[1] == ".m4a"):
		song = MP4(path)
		artist = str(song.tags['\xa9ART'][0]).lower()
		title = str(song.tags['\xa9nam'][0]).lower()
	else:
		#extract the tags for artist and title
		song = tagpy.FileRef(path)

		#extact required tags
		tags = song.tag()
		artist = tags.artist.lower()
		title = tags.title.lower()

		#clean and extract the title and artist name
		title = clean_text(title)
		artist = clean_text(artist)

	print "Trying to retrieve lyrics for song:", title, "by", artist

	#create a new Parser instance for this song
	parser = Parser(artist, title)

	#parse lyrics the normal way using LyricsParser
	lyrics = parser.parse()
	
	if lyrics != "":	#lyrics found
		lyrics_found = True
	else :	#lyrics not found using normal method, possibly due to incorrectly formatted artist name or title
		#searching itunes for correct artist name
		it_artist = itunes_getartist(title, artist)
		if it_artist != "Not Found":	#found on apple itunes
			parser = Parser( it_artist, title)
			lyrics = parser.parse()
			if lyrics != "":
				lyrics_found = True
		#else:			#not found even on itunes


	#create a lyrics file if lyrics is found
	if lyrics_found:
		#create a lyrics file for the song
		if createFile(pathtofolder, audiofile, lyrics):
			found = found + 1
		else:
			print "Error creating lyrics file."
	else:
		not_found = not_found + 1
		print "Lyrics not found for artist:", artist, "and title:", title


'''
for replacedText in replaced:
	print replacedText
'''

print "Total:", found + not_found
print "Found:", found
print "Non Found", not_found