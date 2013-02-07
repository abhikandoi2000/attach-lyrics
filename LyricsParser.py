'''
	Simple parser to parse lyrics from Lyrics.com
	Author : Abhishek Kandoi
	First Made :  Sun, 30 Dec 2012
'''

import string
import urllib2

class Parser:
	#initialize the parser object
	def __init__(self, artist, title):
		self.artist = artist
		self.title = title
		self.lyrics = ""

	def parse(self):
		#clean punctuation marks
		clean_artist = self.artist
		clean_title = self.title
		for c in string.punctuation:
			clean_artist = clean_artist.replace(c, "")
			clean_title = clean_title.replace(c, "")

		#create the url
		url = "http://www.lyrics.com/" + clean_title.replace(" ", "-") + "-lyrics-" + clean_artist.replace(" ", "-") + ".html"

		#open the webpage containing lyrics
		try:
			page = urllib2.urlopen(url, None, 3)
			data = page.read()
		except:
			print "unable to connect to url " + url
			return ""

		#check if page is correct
		title = data
		start = title.find("<title>Lyrics.com")
		if start != -1:		#not found
			print "lyrics title not found"
			return ""
		start = title.find("<title>")
		title = title[(start+7):]
		end = title.find(" Lyrics</title>")
		if end == -1:	#not found
			print "lyrics title end not found"
			return ""
		title = title[:end]

		#extract artist and song title
		songdata = title.split(" - ")

		#check for wrong title page
		#if songdata[0].lower() != self.artist or songdata[1].lower() != self.title:
		if songdata[1].lower() != self.title:
			print "wrong artist data: " + songdata[0] + "-" + songdata[1]
			return ""

		#start extracting data
		self.lyrics = self.get_lyrics(data)
		#capatilize first alphabet of each line
		self.lyrics = string.capwords(self.lyrics, '\n').strip()

		return self.lyrics

	def get_lyrics(self, data):
		lyrics = data
		start = lyrics.find('<div id="lyric_space">')
		if start == -1:
			return "lyrics start not found"
		lyrics = lyrics[(start+22):]
		end = lyrics.find('---')
		if end == -1:
			return "lyrics end not found"
		lyrics = lyrics[:end]

		#remove unwanted data
		lyrics = lyrics.replace('<div id="lyrics" class="SCREENONLY">', '')
		lyrics = lyrics.replace("\n", "")
		lyrics = lyrics.replace("<br />", "\n")
		lyrics = lyrics.strip()
		self.lyrics = lyrics
		print lyrics

		return lyrics
