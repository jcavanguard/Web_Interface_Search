import argparse, argcomplete
import os
import sys
import errno
from selenium import webdriver
from selenium.webdriver import DesiredCapabilities
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException 
from urllib.parse import urlparse
import urllib.request

try:
    from multiprocessing import Pool, freeze_support
except ImportError:
    Pool = None

class Selenium_Web_Capture:
    def __init__(self, driver_name: str, environment: str, mode: str, urls):
        """Constructor for the Selenium_Web_Capture."""
        self.urls = urls
        self.driver_name = driver_name
        self.environment = environment
        self.driver = self.driver_setup()
        self.run(mode)

    def __str__(self):
        """Returns a string representation of the object."""
        if self.environment:
            print("This selenium driver is configured to run in {0} with a headless environment.".format(self.driver))
        else:
            print("This selenium driver is configured to run in {0} in a normal runtime environment.".format(self.driver))

    def run(self, mode: str):
        if mode == 'cli':
            if type(self.urls) == str():
                self.capture(url)
            else:
                if Pool:
                    freeze_support()
                    pool = Pool(processes=16)
                    for url in self.urls:
                        pool.apply_async(self.capture, args=(url))
                else:
                    for url in self.urls:
                        self.capture(url)
        else:
            urls = []
            try:
                contents = open(str(self.urls), 'r')
                for line in contents:
                    line = str(line.strip())
                    line = line.split(',')
                    domain=line[0].strip()
                    port=line[1].strip()
                    if port == '443':
                        url_ct = 'https://{0}'.format(domain)
                        urls.append(url_ct)
                    else:
                        url_ct = 'https://{0}:{1}'.format(domain, port)
                        urls.append(url_ct)
                    if port == '80':
                        url_pt = 'http://{0}'.format(domain)
                        urls.append(url_pt)
                    else:
                        url_pt = 'http://{0}:{1}'.format(domain, port)
                        urls.append(url_pt)
                contents.close()
                if Pool:
                    freeze_support()
                    pool = Pool(processes=16)
                    for url in urls:
                        pool.apply_async(self.capture(url))
                else:
                    for url in self.urls:
                        self.capture(url)
            except OSError:
                print("Could not open/read file:", self.URL_list)
                sys.exit(1)

    def capture(self, url: str):
        """Attempts to capture information at the assigned URL."""
        print(str("Working on {0}".format(url)))
        domain = self.parse_url(url)
        try:
            self.driver.get(url)
            self.capture_photo(domain)
            self.capture_code(domain)
        except OSError as exc:
            print("The connection to {0} has produced the following error: {1}".format(url, exc))
        except WebDriverException as exc:
            message = exc.msg.replace('%20',' ')
            message = message.replace('%3A',':')
            print("The connection to {0} has timed out. More information available here: {1}".format(url, message))
        else:
            print("Exited normally, bad thread; restarting.")

    def driver_setup(self, timeout=6500):
        """Initializes the selenium driver for the current use case."""
        # TODO: Add implementation for other web browsers.
        options = None
        driver = None
        if self.driver_name == 'FireFox':
            options = FirefoxOptions()
            if self.environment == 'headless':
                options.add_argument("--headless")
            driver = webdriver.Firefox(options=options)
        dataPath = "{0}/{1}".format(os.path.abspath(os.path.curdir), "tmp")
        print("Your shizle is in {0}".format(dataPath))
        if not os.path.exists(dataPath):
            try:
                os.makedirs(dataPath)
            except OSError as exc:
                print("Read/write access to this directory is required.")
                sys.exit(0)
            except Exception:
                print("Something else")
                sys.exit(0)
        driver.implicitly_wait(timeout/1000.0)
        return driver
        
    def parse_url(self, url: str) -> str:
        """Collects the domain from a url and returns it."""
        parsed_url = urlparse(url)
        return parsed_url.netloc

    def capture_photo(self, domain: str):
        """Attempts taking a photograph of the web page body."""
        S = lambda X: self.driver.execute_script('return document.body.parentNode.scroll'+X)
        self.driver.set_window_size(S('Width'),S('Height')) # May need manual adjustment
        self.driver.find_element_by_tag_name('body').screenshot('./tmp/{0}.png'.format(domain))

    def capture_code(self, domain: str):
        """Attempts to capture the xml of the current web page."""
        code = self.driver.find_element_by_xpath('/html').text
        self.write_file('./tmp/{0}.xml'.format(domain), code)

    def write_file(self, file_name: str, contents: str):
        try:
            file_write = open("{0}".format(file_name), 'w')
            file_write.write(contents)
        except:
            pass


def main(args: str):
    """Argument parser from the command line."""
    freeze_support()
    parser = argparse.ArgumentParser(description='Checks website code and collects a snapshot.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--file', metavar='./tmp', dest='temp', default=None, type=str, help='Target file containing a list of URIs.')
    group.add_argument('--url', nargs='*', metavar='URL', dest='url', default=None, type=str, help='Target URL or a list of urls in the command line.')
    parser.add_argument('--driver', metavar='driver', dest='driver', default='FireFox', type=str, help='Driver for the browser you are testing.')
    parser.add_argument('--environment', metavar='environment', dest='environment', default='', type=str, help='Headless environment variable.')
    argcomplete.autocomplete(parser)
    args = parser.parse_args(args)
    driver = args.driver
    environment = args.environment
    mode = 'cli'
    if args.temp:
        mode = 'file'
        Selenium_Web_Capture(args.driver, args.environment, mode, args.temp)
    else:
        Selenium_Web_Capture(args.driver, args.environment, mode, args.url)

if __name__ == '__main__':
    main(sys.argv[1:])
