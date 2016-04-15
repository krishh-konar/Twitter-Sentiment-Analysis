#!/usr/bin/env python
# coding=utf-8


''' 
Fetches streaming tweets in real time.
'''

import API_Tokens as t

import re
import json
import string
import os
import operator
import math

from collections import Counter
from tweepy import OAuthHandler, API
from tweepy.streaming import StreamListener
from tweepy import Stream
from nltk.corpus import stopwords
from collections import defaultdict

import stream_tweets as st

import warnings
warnings.filterwarnings("ignore", category=UnicodeWarning)


########################
### GLOBAL VARIABLES ###
########################

### Basic Emoji's for twitter
emoticons = r"""
	(?:
		[:;=\^\-oO]  #eyes
		[\-_\.]?     #nose (optional)
		[\)\(\]\[\-DPOp_\^\\\/] #mouth
	) """

### Custom tokenizer for tweets
regex_tweets = [
		emoticons,
		r'<[^>]+>',      ## HTML TAGS
		r'(?:@[\w\d_]+)',   ## @-mentions
		r'(?:\#[\w]+)',  ## #HashTags
		r'http[s]?://(?:[a-z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-f][0-9a-f]))+', # URLs
		r"(?:[a-z][a-z'\-_]+[a-z])", # words with - and '
		r'(?:(?:\d+,?)+(?:\.?\d+)?)',  ##numbers
	 	r'(?:[\w_]+)',   #other words
	  	r'(?:\S)'        ## normal text	
	
	]

## compiles all the regular expressions in the above list with or operator using join()
tokens_re = re.compile(r'('+'|'.join(regex_tweets)+')' ,re.IGNORECASE | re.VERBOSE| re.UNICODE)

#removing meaningless words
final_stop_words = stopwords.words("english") + list(string.punctuation) + ['rt','RT','via','Via','http','https',u'\u2026'] + list('QWERTYUIOPLKJHGFDSAZXCVBNMqwertyuioplkjhgfdsazxcvbnm1234567890') + [1,2,3,4,5,6,7,8,9,0]
final_stop_words.append('RT')


## Positive words
positive_words = ['good', 'nice', 'great', 'awesome', 'outstanding','fantastic', 'terrific', 'like', 'love' ]
negative_words = ['bad', 'terrible', 'crap', 'useless', 'hate', 'dick', 'idiot', 'stupid', 'asshole', 'clueless', 'annoying']

with open("negative-words.txt",'r') as f:
	line = f.read()
	negative_words.extend(line.split('\n'))

with open("positive-words.txt",'r') as f:
    line = f.read()
    positive_words.extend(line.split('\n'))



############################
### User-defined modules ###
############################

def tokenize(string):
	return tokens_re.findall(string)


def authenticate():
	''' Authentication for using twitter data '''
	auth = OAuthHandler(t.CONSUMER_KEY, t.CONSUMER_SECRET)
	auth.set_access_token(t.ACCESS_TOKEN,t.ACCESS_TOKEN_SECRET)
	api = API(auth)
	return api, auth


def main():
	api,auth = authenticate()

	#get current window size
	columns = os.popen('stty size', 'r').read().split()[1]
	print
	print '{:^{}}'.format("========================",columns)
	print "{:^{}}".format("|| Sentiment Analysis ||",columns)
	print '{:^{}}'.format("========================",columns)
	print


	query = raw_input('Search query: ')
	num_tweets = int(raw_input('Max number of tweets to fetch: '))
	print '\nFetching Tweets....'
	tweets = st.fetchTweets(auth,query,num_tweets)
	print

	com = defaultdict(lambda: defaultdict(int))
	num_tweets = float(len(tweets))

	word_counter = Counter()
	for tweet in tweets:
		word_list = [word for word in tokenize(tweet.lower()) if not word.startswith(('#','@',"http")) and word not in final_stop_words]
		word_counter.update(word_list)
		
		### Co-Occurances ###
		for i in range(len(word_list)-1):
			for j in range(i+1,len(word_list)):
				word1, word2 = sorted([word_list[i],word_list[j]])
				if word1 != word2:
					com[word1][word2] +=1

	print '\nCreating calculation matrices....'
	
	com_max = []

	for term1 in com:
		term_dict = max(com[term1].items(), key=operator.itemgetter(1))[0:5]
		for term2 in term_dict:
			com_max.append(((term1,term2), com[term1][term2]))
	
	sorted_co_occurances = sorted(com_max, reverse=True,key=operator.itemgetter(1))
		

	### Probabilities and Semantic-Orientation ####
	row_dict = {}
	prob_com = defaultdict(lambda: defaultdict(int))

	for term,n in word_counter.items():
		row_dict[term] = n/num_tweets
		for term2 in com[term]:
			prob_com[term][term2] = com[term][term2] / num_tweets

	PMI = defaultdict(lambda: defaultdict(int))
		
	for term1 in row_dict:
		for term2 in com[term1]:
			#print term1, term2
			try:
				#print row_dict[term2]
				denom = row_dict[term1] * row_dict[term2]
				PMI[term1][term2] = math.log(prob_com[term1][term2] / denom, 2)
			except Exception as e:
				#print 'error: ' + str(e)
				pass

	answer_terms = query.lower().split()
	print '\nCalculating Sematic Orientation....\n'
	semantic_orientation = {}
	

	if len(answer_terms)>1:
	    print 'Individual term Sentiments:'
	    print '---------------------------\n'
	
	for term in answer_terms:
		positive_assoc = sum(PMI[term][term2] for term2 in positive_words)
		negative_assoc = sum(PMI[term][term2] for term2 in negative_words)
		semantic_orientation[term] = positive_assoc - negative_assoc
		if len(answer_terms)>1:
		    print str(term) + ": " + str(semantic_orientation[term])

	if len(answer_terms)>1:
		print '---------------------------\n'
 
	sum_so,num_terms = 0, len(semantic_orientation)
	for key in semantic_orientation.keys():
		if semantic_orientation[key] == 0:
			num_terms-=1
		sum_so += semantic_orientation[key]

	print 'Overall Sentiment for {0}: '.format(query) + str(sum_so/num_terms)
	print


if __name__ == '__main__':
	main()
