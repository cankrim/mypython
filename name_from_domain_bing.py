# -*- coding: utf-8 -*-
from tldextract import extract
from urllib2 import urlopen
from bs4 import BeautifulSoup as BS
import logging
import re

log = logging.getLogger(__name__)


class Bing_Search_Result(object):
    #remove these sites from results
    regexes = [
        '(.*)\.md\.com\/?',
        '(.*)\.tumblr\.com\/?',
        '(.*)\.hub\.biz\/?',
        '(.*)\.cutestat\.com\/?',
        '(.*)\.nz\/?',
        '(.*)\.alibaba.com\/?',
        '(.*)\.jewelleryandgemstones.com\/?',
        '(.*)\.dinehere.us\/?',
        '(.*)\.openfos.com\/?'
    ]
    #replace these common foreign characters
    translate_table = {
        0xe4: u'a',
        ord(u'ö'): u'o',
        ord(u'ü'): u'u',
        ord(u'ú'): u'u',
        ord(u'ß'): u'B',
        ord(u'é'): u'e',
        ord(u'ñ'): u'n',
    }
    #strip these words from name result
    to_replace = ['Welcome',
                  'welcome',
                  'WELCOME',
                  'Welcome to',
                  'welcome to',
                  'WELCOME to',
                  'WELCOME TO',
                  'Blog',
                  'blog',
                  'Home Page',
                  'Homepage',
                  'home page',
                  'homepage',
                  'HOME PAGE'
    ]
    #truncate name on these words or characters
    to_truncate = [' Inc',
                   ' INC',
                   ' (',
                   'llc',
                   'LLC',
                   'Ltd',
                   'LTD',
                   'ltd',
                   'Pvt',
                   'pvt',
                   'PVT',
                   'Pty',
                   'Pte',
                   '. '
    ]



    def get_bing_name(self, domain):
        """
            This uses the company domain to hit bing and return name
            returns: single name
        """
        if not isinstance(domain, str):
            domain = str(domain)
        try:
            result = self.get_name(domain)
        except Exception, e:
            log.error("Something is wrong with bing for domain {}. {}.".format(domain, e), exc_info=True)
            result = None
        if result != 0:
            if result is not None:
                return result
        elif result == 0:
            return None
        else:
            return None

    #Hits bing
    def get_name(self, given, searchmod=''):
        namesearchmod = searchmod.strip().replace(',', ' ').replace('.', ' ')
        searchurl = 'http://www.bing.com/search?q=' + given + '+' + namesearchmod
        try:
            response = urlopen(searchurl)
        except Exception, e:
            log.warning("Could not open bing url for domain: {}. {}.".format(given, e), exc_info=True)
            return None
        soup = BS(response.read())
        ol = soup.find_all('ol')[0]
        results = ol.find_all('li', 'b_algo')
        if len(results) == 0:
            return None
        try:
            outputdict = {i: {'url': result.a['href'], 'title': result.a.text, \
                              'domain': extract(result.a['href']).domain, \
                              'subdomain': extract(result.a['href']).subdomain, \
                              'suffix': extract(result.a['href']).suffix, \
                              'given': given} for i, result in enumerate(results)}
        except Exception, e:
            log.warning('Could not parse bing results for domain: {}. {}'.format(given, e), exc_info=True)
            return None
        self.rematch(outputdict)
        if len(outputdict) == 0:
            return None
        else:
            for i in outputdict:
                title = self.translate(outputdict[i]['title'])
                title = self.strip_words(title, given)
                title = re.split("[,|\-:>!/]+", title)[0].strip()
                title = re.split('\s\s+', title)[0].strip()
                outputdict[i]['title'] = title
            dom_match = self.domain_match(given, outputdict)
            return dom_match

    #takes out common external sites
    def rematch(self, urldict):
        for key in urldict.keys():
            url = urldict[key]['url']
            site_regexes = self.regexes
            for regexstring in site_regexes:
                if re.match(regexstring, url):
                    del urldict[key]

    #transaltes foreign characters into unicode characters
    def translate(self, title):
        table = self.translate_table
        new = title.translate(table)
        new = new.encode('ascii', 'ignore')
        return new


    def strip_words(self, title, domain):
        str_replace = self.to_replace
        homes = ['Home ',
                 'HOME ']
        # for products ie. Monobot by Mono Labs
        by = re.search(" by ", title)
        if by:
            title = title.split(" by ")
            title = title[1]
        # strips common words
        for rep in str_replace:
            test = re.search(rep, title)
            if test:
                title = title.replace(rep, "").strip()
        for home in homes:
            test1 = re.search(home, title)
            home = 'home'
            test2 = re.search(home, domain)
            if test1:
                if not test2:
                    title = title.replace(home, "").strip()
        return title

    #truncates names on these words/characters
    def truncate_names(self, title):
        str_truncate = self.to_truncate
        # truncate after given words/characters
        for trun in str_truncate:
            test = trun in title
            if test:
                title = title.split(trun)[0]
        return title

    #makes sure that result has the same domain as domain given
    def domain_match(self, domain, outputdict):
        newdict = {}
        for i in outputdict:
            found_domain = outputdict[i]['domain'] + '.' + outputdict[i]['suffix']
            if domain == found_domain:
                n = len(newdict)
                newdict[n] = outputdict[i]
        if len(newdict) > 0:
            return newdict[0]
        else:
            return None
