import re, csv
from tldextract import extract
from urllib2 import urlopen
from bs4 import BeautifulSoup as BS
from string import punctuation
from selenium import webdriver
from time import sleep
from random import uniform

class Search_Result(object):
	def __init__(self,resultDict):
		self.target = resultDict['name']
		self.mods = resultDict['searchmods']
		self.url = resultDict['url']
		self.title = resultDict['title']
		self.desc = resultDict['desc']
		self.match = resultDict['correct']
		self.aftermatch = resultDict['aftermatch']
		self.subdomain = resultDict['subdomain']
		self.domain = resultDict['domain']
		self.suffix = resultDict['suffix']
		self.features = self.score()
		self.mm_domain = self.domain + '.' + self.suffix

	def __repr__(self):
		try:
			return u"%s ~ %s\n%s: %s" % (self.url,self.target,self.title,self.desc)
		except:
			return u"%s ~ %s\n---could not print---" % (self.url,self.target)

	def dict(self):
		output = {\
			'target':self.target,\
			'mods':self.mods,\
			'domain':self.url,\
			'domain_title':self.title,\
			'domain_desc':self.desc,\
			'domain_match':self.match}
		return output

	def features(self):
		feature = {}
		titlename = retitle(self.target)
		middlename = remiddle(self.target)
		titlematch = re.search(titlename,self.title)
		titlemiddlematch = re.search(titlename, self.title)
		partialmatch = 'do'
		if titlematch:
			feature['titlematch'] = 1
			feature['fulltitlematch'] = 1
		elif partialmatch:
			feature['partialmatch'] = 1
		else:
			feature['nomatch'] = 1
		if titlemiddlematch:
			feature['titlemiddlematch'] = 1
		else:
			feature['titlemiddlematch'] = 0
		#split on '|', strip(), and then take minimum ld?
		splitpieces = self.title.split('|')
		minimumdistance = min([levenshtein_distance(piece,self.target)\
								for piece in pieces])
		feature['minimumdistance'] = minimumdistance

		ld = levenshtein_distance(self.target,self.title)
		return feature

	def score(self):
		#scikit-learn
		pass
		titlename = retitle(self.target)
		middlename = remiddle(self.target)
		titlematch = re.search(titlename,self.title)
		titlemiddlematch = re.search(titlename, self.title)

	def attributes(self):
		self.target.replace(', inc.','([, ]? inc.)?')

	def urlscore(name,rank,infodict):
		score = rank
		title,desc = infodict.values()[0]
		newname = rename(name)
		titlematch = re.search(newname,title.lower())
		if titlematch:
			extras = titlematch.group(1).strip().split()
			exempt = exempts() + re.findall(r"[\w']+", name)
			extrawords = [extra for extra in extras if extra not in exempt]
			score += 3*len(extrawords)
			middlematch = re.search(titlename(name),title.lower())
			if middlematch:
				try:
					score += 5*len(middlematch.group(1).strip().split())
				except:
					pass

		elif re.search(newname,desc.lower()):
			score += 1
			middlematch = re.search(titlename(name),title.lower())
			if middlematch:
				try:
					score += 5*len(middlematch.group(1).strip().split())
				except:
					pass
		else:
			score += 2
			score += listdiff(title.split(),name.split())
		return score

class Search_Result_List(list):
	def __repr__(self):
		return 'Search_Result_List with %i entries' % len(self)

	def mm_domains(self):
		for domain in self:
			if domain:
				print domain.mm_domain
			else:
				print 

	def descs(self):
		for domain in self:
			if domain:
				print domain.desc
			else:
				print

	def titles(self):
		for domain in self:
			if domain:
				print domain.title
			else:
				print

#--------------------Functions for finding the domain and creating the class--------------------------

def bing_domain_list(names):
	# Pull bing results for a list of names with automatic sleeping in between to appease internet

	if type(names) != list:
		assert False, "Input must be a list"
	results = Search_Result_List()
	for name in names:
		result = bing_domain(name)
		print name
		try:
			print result.url
			print result.desc
		except:
			pass
		print
		results.append(result)
		sleep(uniform(0.5,1.5))
	return results

def bing_domain(name):
	# Pull bing results with reasonable error handling

	if type(name) != str:
		name = str(name)
	try:
		result = get_bing_domain(name)
	except:
		return None
	if result:
		return Search_Result(result)
	else:
		return None


def get_bing_domain(name,searchmod = ''):
	# Program to pull bing results for a given query and try to find the most likely domain

	searchname = name.strip().replace(',',' ').replace(' ','+')
	namesearchmod = searchmod.strip().replace(',', ' ').replace('.',' ')
	searchurl = 'http://www.bing.com/search?q=' + searchname + '+' + namesearchmod
	try:
		response = urlopen(searchurl)
	except:
		print 'Could not open url'
		return None
	soup = BS(response.read())
	ol = soup.find_all('ol')[0]
	results = ol.find_all('li','b_algo')
	if len(results) == 0:
		print 'Did not find any results'
		return None
	try:	
		outputdict = {i+1:{'url':result.a['href'],'title':result.a.text,'name':name,\
							'desc':result.p.text,'rank':i+1,'correct' : 0,\
							'domain':extract(result.a['href']).domain,\
							'subdomain':extract(result.a['href']).subdomain,\
							'suffix':extract(result.a['href']).suffix,\
							'aftermatch':0,'searchmods':searchmod} for\
			i,result in enumerate(results)}
	except:
		print 'Could not parse results'
		return None
	rematch(outputdict)
	if len(outputdict) == 0:
		print 'Did not find any results'
		return None
	else:
		url,score = besturl(name,outputdict)
		if url >= 0:
			return outputdict[url]
		else:
			print 'Did not find a reasonable result'
			return None


def retitle(name):
	titlename = name.replace(', inc.','[^\w-](, inc.)?').replace('.','[. ]?')\
		.replace(',','[, ]?').lower()
	titlename = r'[\:\-\|]?([\w ]*)'+titlename
	return titlename

def remiddle(name):
	middlename = name.replace('.','[. ]?').replace(', inc','[^\w-]( .*), inc').replace(',',\
		'[, ]?').lower()
	return middlename

def exempts():
	commons = ['home','the','of','official','website','site']+list(punctuation)
	return commons

def rename(name):
	rename = name.lower().replace(',','[, ]?')\
						.replace('[, ]? inc.','[^\w-]([, ]? inc.)?')\
						.replace('[, ]? llc.','[^\w-]([, ]? llc.)?')\
						.replace('.','[. ]?').lower()
	rename = r'[\:\-\|]?([\w ]*)'+rename
	return rename

def titlename(name):
	titlename = name.lower().replace('.','[. ]?').replace(', inc','[^\w-]( .*), inc').\
						replace(', inc','[^\w-]( .*), inc').replace(',','[, ]?')
	return titlename

def rematch(urldict):
	# Avoid common false domains
	for key in urldict.keys():
		url = urldict[key]['url']
		if not re.match('https?:\/\/[\w\d\.-]+\/?$',url):
			del urldict[key]	
		#all elif statements eliminate specific group urls that break the above formula	
		elif re.match('(.*)\.md\.com\/?',url):
			del urldict[key]
		elif re.match('(.*)\.tumblr\.com\/?',url):
			del urldict[key]
		elif re.match('(.*)\.hub\.biz\/?',url):
			del urldict[key]
		elif re.match('(.*)\.cutestat\.com\/?',url):
			del urldict[key]
		elif re.match('(.*)\.nz\/?',url):
			del urldict[key]
		elif re.match('(.*)\.alibaba.com\/?',url):
			del urldict[key]
		elif re.match('(.*)\.jewelleryandgemstones.com\/?',url):
			del urldict[key]
		elif re.match('(.*)\.dinehere.us\/?',url):
			del urldict[key]
		elif re.match('(.*)\.openfos.com\/?',url):
			del urldict[key]
	#return urldict

def besturl(name,urldict):
	bestscore = 6
	bestrank = None
	for i in urldict.keys():
		score = urlscore(name,i,urldict[i])
		if score < bestscore:
			bestscore = score
			bestrank = i
	return bestrank, bestscore

def urlscore(name,rank,infodict):
	score = rank
	title = infodict['title']
	desc = infodict['desc']
	newname = rename(name)
	titlematch = re.search(newname,title.lower())
	if titlematch:
		extras = titlematch.group(1).strip().split()
		exempt = exempts() + re.findall(r"[\w']+", name)
		extrawords = [extra for extra in extras if extra not in exempt]
		score += 3*len(extrawords)
		middlematch = re.search(titlename(name),title.lower())
		if middlematch:
			try:
				score += 5*len(middlematch.group(1).strip().split())
			except:
				pass
	elif re.search(newname,desc.lower()):
		score += 1
		middlematch = re.search(titlename(name),title.lower())
		if middlematch:
			try:
				score += 5*len(middlematch.group(1).strip().split())
			except:
				pass
	else:
		score += 2
		score += listdiff(title.split(),name.split())
	return score

def listdiff(A,B):
	b = set(B)
	a = set(A)
	diffset = [aa for aa in a if aa not in b] + [bb for bb in b if bb not in a]
	return len(diffset)

def levenshtein_distance(string1,string2):
	if len(string1) > len(string2):
		string1,string2 = string2,string1
	distances = range(len(string1) + 1)
	for index2,char2 in enumerate(string2):
		new_distances = [index2+1]
		for index1,char1 in enumerate(string1):
			if char1 == char2:
				new_distances.append(distances[index1])
			else:
				new_distances.append(1 + min((distances[index1], 
					distances[index1+1], new_distances[-1])))
		distances = new_distances
	return distances[-1]
