from unidecode import unidecode
from bs4 import BeautifulSoup
import logging
import sys
import traceback
from selenium import webdriver
from selenium.common.exceptions import WebDriverException, TimeoutException
import urllib2
import justext
import requests
from Queue import Queue
from threading import Thread
from requests.exceptions import ConnectionError, Timeout
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import time

USERAGENT = "Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36"

dcap = dict(DesiredCapabilities.PHANTOMJS)
dcap["phantomjs.page.settings.userAgent"] = USERAGENT

log = logging.getLogger('mattermark.utils.website_text')
logging.getLogger('selenium').setLevel(logging.CRITICAL)
logging.getLogger('unidecode').setLevel(logging.CRITICAL)

TIMEOUT_S = 30
MIN_HTML_LEN = 10

f = urllib2.urlopen('http://code.jquery.com/jquery-1.11.1.min.js')
JQUERY_JS = f.read()


def get_content_type(url):
    content_type = ''
    try:
        r = requests.head(url, timeout=3)
        content_header = r.headers['content-type']
        content_header_split = content_header.split('/')
        content_type = content_header_split[0] if len(content_header_split) > 0 else ''
    except Timeout:
        log.error("Timeout trying to get content type of: %s", url)

    return content_type


def extract_text(html):
    paragraphs = justext.justext(html, justext.get_stoplist("English"),
                                 length_high=140, stopwords_low=0.2)
    paragraphs = [p.text for p in paragraphs if not p.is_boilerplate]

    return "\n".join(paragraphs)


class WebsiteText(object):
    def get_html(self, browser=None, use_phantom=True, quit_browser=True, proxy=None):
        if use_phantom:
            service_args = ['--ignore-ssl-errors=true']

            if proxy:
                service_args += ['--proxy=' + str(proxy['host']),
                                 "--proxy-auth=" + str(proxy['auth'])]

            if browser is None:
                browser = webdriver.PhantomJS(service_args=service_args,
                                              desired_capabilities=dcap)

            browser.set_page_load_timeout(TIMEOUT_S)
            browser.set_script_timeout(TIMEOUT_S)

            success = False

            try:
                browser.get(self.url)
                self.raw_html = browser.page_source

                if self.remove_hidden:
                    try:
                        browser.execute_script(JQUERY_JS)
                        browser.execute_script("$(':hidden').remove()")
                    except WebDriverException:
                        log.warning("Failed to remove hidden elements, proceeding anyway")

                self.visible_html = browser.page_source
                if proxy and 'Too many connections' in self.raw_html:
                    success = False
                else:
                    success = True
            except:
                log.error("Failed to get URL: %s, Traceback: %s", self.url, traceback.format_exc())
                success = False

            if quit_browser:
                browser.quit()
        else:
            try:
                headers = {
                    'USER-AGENT': USERAGENT
                }
                response = requests.get(self.url,
                                        timeout=TIMEOUT_S,
                                        headers=headers)
                success = response.ok
                self.raw_html = response.content
                self.visible_html = response.content
            except ConnectionError:
                success = False
            except Timeout:
                success = False

        return success

    def get_beautiful_soup(self):
        if self.raw_html:
            return BeautifulSoup(self.visible_html)
        else:
            return None

    def get_body_text(self):
        return extract_text(self.visible_html)

    def get_dead(self):
        """
        Returns (boolean) whether site exists
        """
        if not self.soup or len(self.soup.text) < MIN_HTML_LEN:
            return 1
        return 0

    def __init__(self, url, download=True, remove_hidden=True, get_text=True,
                 browser=None, quit_browser=True, use_phantom=True, proxy=None, retries=3):
        self.failed = False
        self.is_downloaded = False
        self.url = url
        self.remove_hidden = remove_hidden
        self.raw_text = None
        self.text = None
        self.raw_html = None
        self.visible_html = None
        self.error_msg = None
        self.soup = None

        try:
            if download:
                tried = 0
                while tried < retries and not self.is_downloaded:
                    if tried > 0:
                        time.sleep(1)
                    try:
                        self.is_downloaded = self.get_html(browser=browser, quit_browser=quit_browser, use_phantom=use_phantom, proxy=proxy)
                    except WebDriverException, e:
                        self.is_downloaded = False
                    tried += 1
                    log.debug("Tried to download %d times", tried)
                self.soup = self.get_beautiful_soup()
                self.is_dead = self.get_dead()

                if not self.is_dead and get_text:
                    self.raw_text = self.get_body_text()
                    try:
                        self.text = unidecode(self.raw_text)
                    except:
                        pass
        except TimeoutException, e:
            self.is_dead = 1
            self.error_msg = 'Timeout %s' % str(e)
            log.error("Server response timed out or failed")
        except Exception, e:
            self.is_dead = 1
            self.error_msg = 'Exception %s' % str(e)
            log.error('Error GET %s' % url, exc_info=True)

    @classmethod
    def _batch_helper(klass, q, out_q, browser, get_text, remove_hidden):
        while True:
            url = q.get()
            log.info("Getting url: " + url)
            sys.stdout.flush()
            wt = klass(url, browser=browser, quit_browser=False, get_text=get_text, remove_hidden=remove_hidden)
            sys.stdout.flush()
            out_q.put((url, wt))
            q.task_done()

    @classmethod
    def batch_get_websites(klass, urls, num_threads=5, get_text=True, remove_hidden=True, proxy=None):
        q = Queue(maxsize=0)
        out_q = Queue(maxsize=0)
        num_threads = min(len(urls), num_threads)

        service_args = ['--ignore-ssl-errors=true']

        if proxy:
            service_args += ['--proxy=' + str(proxy['host']),
                             "--proxy-auth=" + str(proxy['auth'])]

        browsers = [webdriver.PhantomJS(service_args=service_args) for i in range(num_threads)]

        for url in urls:
            q.put(url)

        for i in range(num_threads):
            worker = Thread(target=klass._batch_helper, args=(q, out_q, browsers[i], get_text, remove_hidden))
            worker.setDaemon(True)
            worker.start()

        q.join()

        for b in browsers:
            b.quit()

        return dict([out_q.get() for url in urls])
