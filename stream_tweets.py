#!/usr/bin/env python

''' 
Fetches streaming tweets in real time.
'''

import API_Tokens as t
import json
from tweepy import OAuthHandler, API
from tweepy.streaming import StreamListener
from tweepy import Stream
import os
import sys

tweet_list = []

### Custom made listener Class; deals with all the incoming streaming data
class MyListener(StreamListener):

	def __init__(self,api=None,num_tweets=1000):
		#super(MyListener,self).__init__()
		self.api=api
		self.num_tweets=num_tweets
		self.__counter = 0

	# Write all the incoming data in buffer.json file
	def on_data(self,data):

		try:
			# with open("tweets_test.json","a") as f:
			# 	j = json.loads(data)
			# 	tweet_text = j['text'].encode("utf-8")
			# 	if self.__counter >= self.num_tweets:
			# 		return False
			# 	#dump tweets as a dictionary for easy retrival
			# 	json.dump({"tweet":tweet_text},f)
			# 	f.write('\n')
			# 	self.__counter+=1
			# 	sys.stdout.write("\rTweets fetched: {0}/{1}".format(self.__counter,self.num_tweets))
			# 	sys.stdout.flush()
			
			j = json.loads(data)
			tweet_list.append(j['text'].encode("utf-8"))
			if self.__counter >= self.num_tweets:
				return False
			self.__counter+=1
			sys.stdout.write("\rTweets fetched: {0}/{1}".format(self.__counter,self.num_tweets))
			sys.stdout.flush()

		except Exception as e:
			pass

		return True

	def on_error(self,status):
		print status
		return True

def fetchTweets(auth,query,num_tweets=1000):
	try:
		#creating Streaming_API instance
		stream = Stream(auth, MyListener(num_tweets=num_tweets),include_rts=False)
		stream.filter(track = [query])
		return tweet_list
	except KeyboardInterrupt:
		print '\n Stopped Fetching Tweets.'
		exit()

def main():
	#creating a REST_API instance
	api, auth = authenticate()

	#search query
	query = raw_input('Search query: ')
	num_tweets = int(raw_input('Max number of tweets to fetch: '))
	fetchTweets(auth,query,num_tweets)


def authenticate():
	''' Authentication for using twitter data '''
	auth = OAuthHandler(t.CONSUMER_KEY, t.CONSUMER_SECRET)
	auth.set_access_token(t.ACCESS_TOKEN,t.ACCESS_TOKEN_SECRET)
	api = API(auth)
	return api, auth

if __name__ == '__main__':
	main()
