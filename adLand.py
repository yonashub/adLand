"""
@yonas: extract landing pages from a given url or list of urls.
makes use of phantomjs browser emulator via a python wrapper called phantomcurl


#todo:
    - if len(href)>3*current_url:it is probably an ad
    - handle all redirection , may need to modify the phantomcurl library
    - handle text-ads
limitations:
        -   text ads[todo]
        -   image ads

"""
"""
Observeations:
    -   there are dynamic ads. a frame updating itself

"""



"""
DEPENDENCIES:
    re2 fast regular expression library
        export CFLAGS='-std=c++11'
        pip install re2



"""


from phantomcurl import PhantomCurl
import sys
from bs4 import BeautifulSoup
import urllib
import requests
import time
import random
from urlparse import urlparse,parse_qs
import urlparse as urlparse2
from adblockparser import AdblockRules

import urllib2

try:
    import re2 as re
except:
    import re


#some ads dont exactly follow the rules we developed, so we create a custom rule. this ad forexample shows
# ads as single image with direct link to landing page in href




"""

desired output:
    page domain,
        - ads
    subdomiain[sub pages]
        - ads
        -img class="banner"



modifications made to phantomcurl:
    -   spelling instal to install
    -   ability to shake(scroll down and up) the webpage
    -   option to give delay in seconds to give time for javascript to render
"""

class Adobj:
    advertisers=[]
    crypticadDSPs=["adformdsp.net","zanox.com","adform.net","exactag.com"]
    user_agentstr = "Mozilla/5.0 (Windows NT 10.0; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0"
    user_agentstr2 = "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/32.0.1700.107 Safari/537.36"
    random_ua=user_agentstr if random.randint(0,10)<5 else user_agentstr2

    random_prxy=None
#this easylist doesnt filter some like adform
raw_rules=open("easylist.txt").readlines()
adfilter = AdblockRules(raw_rules)



def init_landing_tags():
    # under-development:list of keywords that identify ad hrefs.
    landingKeys = [
  'mt_lp',
  'redir',
  'ds_dest_url',
  'adurl',
  'cpdir',
  'goto',
  'clickurl',
  'url',
  'rurl',
  'mt_lp',
  'redirect',
  'clickenc',
  'clicks',
  'maxdest',
  'oadest',
  'r',
  'go',
  'xu',]
    return landingKeys
def get_intermediate_hops(originalrurl,request_header):
    interurl=originalrurl
    redirect_re = re.compile('<meta[^>]*?url=(.*?)["\']', re.IGNORECASE)
    hops = []
    tryround=0
    while interurl:
        tryround+=1
        if interurl in hops:
            interurl = None
        else:
            #hops.insert(0, url)
            hops.append(interurl)
            req = urllib2.Request(interurl, headers=request_header)
            try:
                response = urllib2.urlopen(req)
            except Exception:
                if tryround<3:continue
                else: break
            if response.geturl() != interurl:
                #hops.insert(0, response.geturl())
                hops.append(response.geturl())

            # check for redirect meta tag
            match = redirect_re.search(response.read())

            if match:
                interurl = urlparse2.urljoin(interurl, match.groups()[0].strip())
            else:
                interurl = None
    return hops[-1]
def reveal_hidden_landingpage(crypticurl):
    #if it involves DSP or other middleguys, try to emulate clicks to the webpage, and find all landing the webpage
    user_agentstr=Adobj.random_ua#"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0"
    headers = {'User-Agent':user_agentstr}
    return get_intermediate_hops(crypticurl,headers)

def extract_landing_candidate(theurl,thekey,thatframe_id,taburl):
    #try to find the landing page of the given ad, if it is already available as hidden argument in href tag
    print "extracting",theurl
    arguments=urlparse(theurl).query
    potential_landing=parse_qs(arguments,keep_blank_values=1)

    if potential_landing.has_key(thekey):
        potentialLP=potential_landing[thekey][0]

        crypti=False
        for acrypticDSP in Adobj.crypticadDSPs:
            if acrypticDSP in potentialLP:
                crypti=True
                break
        if potential_landing[thekey]=="" or crypti:
            potentialLP=reveal_hidden_landingpage(potentialLP)

        if not type(potentialLP)==list and potentialLP.rstrip("/") not in taburl.split("://")[1].split("/")[0]:

            if thekey=="adurl": #doubleclick sometimes gives two adurls
                try:
                    LP=[_ for _ in [_.split("=")[1] for _ in urllib.unquote(theurl).split("&") if thekey in _ and len(_.split("="))>1] if 'doubleclick' not in _][0]
                    if LP and len([True for cryp in Adobj.crypticadDSPs if LP not in cryp]):
                        Adobj.advertisers.append((taburl, LP))
                        return
                except IndexError as e:
                    print "Landing page returned weird index: ",e,theurl#print "smart",LP,"end of smart"

        Adobj.advertisers.append((taburl, potentialLP))
        #print "Oracle says it is ad:",theurl
        """
        @todo:
            if landing page is a known dsp or an adnetwork: execute that candidate url to get the actual landing page
        """


def get_full_page(url, browserObj):

    if not (url.startswith("http://") or url.startswith("https://")):
        "print Url has to start with http:// or https://"
        return None
    #emulate a firefox browser to get the full rendering of the page
    user_agentstr=Adobj.random_ua#"Mozilla/5.0 (Windows NT 10.0; WOW64; rv:41.0) Gecko/20100101 Firefox/41.0"
    heads={
    #"Connection": "keep-alive",
    #"Host": "httpbin.org",
    #"Accept-Encoding": "gzip",
    #"Accept-Language": "ru-RU",
    "User-Agent": user_agentstr,#"Mozilla/5.0 (Unknown; Linux i686) AppleWebKit/534.34 (KHTML, like Gecko) PhantomJS/1.10.0 (development) Safari/534.34",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
  }
    #browserObj=PhantomCurl(user_agent=user_agentstr, cookie_jar=None, proxy=None, timeout_sec=None, inspect_iframes=True, with_content=True, with_request_response=True)
    #browserObj=PhantomCurl(headers=heads, cookie_jar=None, proxy=None, timeout_sec=None, delay=3, inspect_iframes=True, with_content=True, with_request_response=True)

    #PhantomCurl()
    resultObj=browserObj.fetch(url)
    print "page downloaded, going for analysis ..."
    return resultObj

def find_landing_page(atag,thatframe_id,domainpart,taburl):
    # landing page of the website, found in the href attribute of a-tag
    atagurl=atag['href']
    #print atagurl,"<//////////////"
    #print "within find", domainpart, taburl
    landingkeys=init_landing_tags() #get the list of keywords that are associated with landing pages
    for landkey in map(str.strip,landingkeys):
        if landkey+"=" in atagurl:

            #print "------------------"
            extract_landing_candidate(urllib.unquote(atagurl), landkey, thatframe_id,taburl)


def inspect_frames(thatframe, taburl):
    # not ad y probably a tracker
    # filter out zero size iframes
    if thatframe.has_key(u'height'):
        if not thatframe[u'height'].endswith("%"):
            if float(thatframe[u'height'].strip("px")) < 20:
                return
        elif thatframe[u'height'].endswith("%") and float(thatframe[u'width'].strip("px").strip("%"))==0:
            return
    if thatframe.has_key(u'width'):
        if not thatframe[u'width'].endswith("%"):
            if float(thatframe[u'width'].strip("px"))<20:
                return
        elif thatframe[u'width'].endswith("%") and float(thatframe[u'width'].strip("px").strip("%"))==0:
            return
    if thatframe.has_key("frames") and len(thatframe['frames']) > 0:
        for aframe in thatframe['frames']:
            inspect_frames(aframe, taburl)
    parsableframe=unicode(thatframe['content'])
    parsableSoup=BeautifulSoup(parsableframe,"lxml")
    find_ads_in_the_soup(thatframe, parsableSoup, taburl)
def inspect_divs(thatframe, taburl):
    #this function is to catch those ads that are displayed as href links directly inside divs
    page_as=BeautifulSoup(unicode(thatframe[u'content']),"lxml").findAll("a",href=True)
    for page_a in page_as:
        if page_a.parent.name=="div":
            #for oneatag_in_div in page_div.findAll("a",href=True):
            candid_href=page_a['href']
            if candid_href.startswith("/aclk?"):
                #handle for missing "http://doubleclick.net" url in ads
                candid_href="http://doubleclick.net"+candid_href

            if candid_href:
                domainpart=taburl.lstrip("https://").lstrip("http://").lstrip("www.").rsplit("/")[0]

                #check if href is same domain as main url
                if len(candid_href) >= len(domainpart) and domainpart in candid_href[:len(domainpart)+12]:
                    #print "i continue",len(candidate_href) >= len(domainpart),candidate_href,domainpart
                    continue

                #this tag is not from the main website
                adrule_result=adfilter.should_block(candid_href)
                if not adrule_result:
                    #print "not an ad------------->",candidate_href
                    continue
                find_landing_page({'href':candid_href},thatframe.get("id"),domainpart,taburl)


def find_ads_in_the_soup(thatframe, parsableSoup,taburl):
    """
            todo: find the parent tag  of img-tag and check if it is a-tag and inspect that tag.
            if this parent doesn't have it and it this parent is div, go check its parent
    """


    # CASE 1: image ads: img tag inside a tag
    """
    find ads using images:
        find img attribute, check if its src atrribute satisfies easylist patters an ad
            if yes:
                #save the src domain-name------->this is a middleman (adnetwork,adexchange,DSP...)
                find its parent attribute, if it atag: save the domain-name, as it is a middleman
                    use the list of tags to identify the adurl
                        if the adurl is empty or same as the current domain, excute the whole href value via http get
                                save the target URL before and after the request,
                                    the one before the request is a middleman, the last one is the landingpage
                                        add it to LANDINGPAGeS list
                                        #TODO sometimes the DSP is found to be the landing page, need to take care of it
                        if the adurl is not empty this is the landing page: add it to LANDINGPAGeS list


    """
    for  atag in parsableSoup.findAll('a'):
        #if a tag has attr tag and this tag has image
        if (atag.has_attr("href") or atag.has_attr('data-original-click-url')) and atag.findAll("img"):

            candidate_href=atag['href']
            if candidate_href.startswith("/aclk?"):
                #handle for missing "http://doubleclick.net" url in ads
                candidate_href="http://doubleclick.net"+candidate_href

            if candidate_href:

                #data-original-click-url found in some google ads
                domainpart=taburl.lstrip("https://").lstrip("http://").lstrip("www.").rsplit("/")[0]

                #check if href is same domain as main url
                if len(candidate_href) >= len(domainpart) and domainpart in candidate_href[:len(domainpart)+12]:
                    #print "i continue",len(candidate_href) >= len(domainpart),candidate_href,domainpart
                    continue
                #print "before find 0",atag,type(domainpart),domainpart,taburl,candidate_href
                #handle the special case of adxpose.com tricky ad image
                if len(atag.find_all('img', recursive=False))==1:
                    imgtagcase=atag.find_all('img', recursive=False)[0] #find all images @ the current level
                    if imgtagcase.has_attr("src") and imgtagcase['src'].startswith("https://servedby.adxpose.com/"):
                        adxposetag=atag['href']
                        #print adxposetag
                        print "busted!!!",imgtagcase['src']
                        Adobj.advertisers.append((taburl,adxposetag))
                        continue

                #check if it is extractable url
                #if len(atag['href'])<len(domainpart):
                #    break

                #this tag is not from the main website
                adrule_result=adfilter.should_block(candidate_href)
                if not adrule_result:
                #    #print "not an ad------------->",candidate_href
                    continue
                find_landing_page(atag,thatframe.get("id"),domainpart,taburl)
    #case 2: div ads
    """
    DIV ads: in find_ads_in_div() function

    """

    #for  divtag in parsableSoup.findAll('div'):
    #   print "DIV :",[ _['src'] for _ in divtag.findAll("iframe",{"src":True})]
    #case 3: embed ads



def comparehostnames(url1, url2): #compare if two urls are from same domain
    url1,url2=augment_with_www(url1),augment_with_www(url2)

    return urlparse(url1).netloc.lstrip("www.") == urlparse(url2).netloc.lstrip("www.")

def augment_with_www(url):
    augURL=url
    if not url.startswith("http"):
        augURL="://".join(["http", url])
    if url.startswith("http") and not url.lstrip("http://").lstrip("https://").startswith("www"):
        _=url.split("://")
        augURL= ".".join(["://".join([ _[0],"www"]),_[1]])
    return augURL

def select_actual_content_pages(main_frame,parenturl): #select a subset of five content pages from this website
    contentpages=[]
    page_source=BeautifulSoup(main_frame['content'],"lxml")
    for ahref in page_source.findAll("a",href=True):
        if len(ahref['href'])<20 or ahref['href'] == parenturl:
            continue
        if parenturl.rstrip("/")!=ahref['href'].rstrip("/") and ahref['href'] not in contentpages:

            if comparehostnames(parenturl,ahref['href']) or ahref['href'].startswith("/"):
                if "." not in ahref['href'] and ahref['href'].startswith("/"):
                    contentpages.append(parenturl+ahref['href'])
                elif ahref['href'].rstrip("/") not in [_.rstrip("/") for _ in contentpages]:
                    #print ahref['href'],"yonas",[_.rstrip("/") for _ in contentpages]
                    if not ahref['href'] in contentpages:contentpages.append(ahref['href'])
                #else:print ahref['href'].rstrip("/"),contentpages
            if len(contentpages)==5: #five content pages returned
                return contentpages

def create_browser_object():


    heads={
    #"Connection": "keep-alive",
    #"Host": "httpbin.org",
    #"Accept-Encoding": "gzip",
    #"Accept-Language": "ru-RU",
    "User-Agent": Adobj.random_ua,#"Mozilla/5.0 (Unknown; Linux i686) AppleWebKit/534.34 (KHTML, like Gecko) PhantomJS/1.10.0 (development) Safari/534.34",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
  }
    browserObj=PhantomCurl(headers=heads, cookie_jar=None, proxy=None, timeout_sec=None, delay=3, inspect_iframes=True, with_content=True, with_request_response=True)
    return browserObj

def inspect_page(main_frame, urltofetch,current_page):
    print "\n","\t"*9,"************GOING FOR CONTENT PAGE: ", current_page, "***********\n"
    inspect_frames(main_frame, current_page) #image ads
    inspect_divs(main_frame, current_page)   #div ads

def start_automation(starturl):


    #if not random_useragenti:

    urltofetch = starturl
    print "starting automation..."
    if not starturl.startswith("http"):
        print "url has to start with http(s)://"
        return
    #for i in [".", ".", "."]*3 + [".\n"]:
    #    time.sleep(10)
    #    print i,
    browserObj = create_browser_object()
    main_frame = get_full_page(urltofetch, browserObj)
    print "got the page"
    if not main_frame:
        print("no response from URL: %s try again ..."%starturl)
    contentpages_to_fetch = select_actual_content_pages(main_frame, starturl)

    if not contentpages_to_fetch:
        #contentpages_to_fetch
        print("\n\tnull list of content pages found",contentpages_to_fetch)
        return
    for pagetofetch in contentpages_to_fetch:#inspect five random pages on the website
        #display the pages from current page
        main_frame_i = get_full_page(pagetofetch,browserObj)
        #print main_frame_i
        if main_frame_i:
            inspect_page(main_frame_i, urltofetch,pagetofetch)
def write_ads_to_file(url_as_name):
   print "==="*70
   print "  "*10,"LANDING PAGES OF ADS DETECTED ON FIVE SUB PAGES UNDER",url_as_name,"   "*10
   print "==="*70
   print "fetch_time", "..."*10, "URL","..."*20,"ad"
   print "___"*70
   #candidfilename=time.ctime().replace(":","_").replace(" ","-")+".csv"
   #fileout=open(url_as_name.lstrip("https://").lstrip("http://").split("/")[0].replace(".","_")+".txt","w")
   candidfilename="adLand.log"
   fileout=open(candidfilename,"a")
   fileout.write("TIMESTAMP --- URL --- LANDING PAGES\n")
   strtime=str(time.time())
   for j,lp in Adobj.advertisers:
       print strtime,"..."*10,j,"..."*10,lp,'\n'
       fileout.write(strtime+" --- "+str(j)+" --- "+str(lp)+"\n")
   fileout.flush()
   fileout.close()

if __name__ == '__main__':


    if len(sys.argv)>2:
        print sys.argv
        urltofetch = sys.argv[1]
        useragent_list = sys.argv[2]
        proxylist = sys.argv[3]
        random_useragent,random_proxy=None, None
        if useragent_list:
            random_useragent= random.choice(open(urltofetch).read().split('\n')[:]).strip()
            Adobj.random_ua=random_useragent

        if proxylist:
            random_proxy= random.choice(open(proxylist).read().split('\n')[:]).strip()
            if len(random_proxy.split(":"))!=3:
                print "proxy has to be of the form address:port got %s"%random_proxy
                exit(0)
            Adobj.random_prxy=random_proxy
        if urltofetch.endswith(".txt"):#if list of urls to fetchis given url per line
            listurltofetch= open(urltofetch).read().split('\n')[:]
            for urltofetch in listurltofetch:
                start_automation(urltofetch)
                """
                main_frame=get_full_page(urltofetch)
                if main_frame:inspect_frames(main_frame,urltofetch)
                """
                write_ads_to_file(urltofetch)

    elif len(sys.argv)==2: # else read url from comand line version
        urltofetch=sys.argv[1]
        print urltofetch
        start_automation(urltofetch)
        write_ads_to_file(urltofetch)
    #print "detected Ads:  "
    else:
        print "usage 1 :python  % urllist.txt useragentlist.txt proxylist.txt "%sys.argv[0]
        print "usage 2 :python  % http://www.example.com "%sys.argv[0]
        exit(0)
