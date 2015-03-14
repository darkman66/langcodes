# -*- coding: utf-8; -*-

"""
This file implements testing ing langcodes module for multithreaded env

Problem is still there if you try to acccess that module from multiple places at once
"""
import threading
from twisted.internet import reactor
from langcodes.tag_parser import parse_tag
from langcodes import standardize_tag

def parseMe(i, tag):
    print i, parse_tag(tag)



def stopMe():
    reactor.stop()

def startProcessing():
    for i, tag in enumerate(('en_US', 'en', 'en_gb')):
        #reactor.callInThread(parseMe, i, tag)
        print '-'*10, parseMe(i, tag)

print "script will STOP working after 5s"

#reactor.callLater(5, stopMe)
#reactor.callInThread(startProcessing)
#reactor.run()

startProcessing()

print standardize_tag('eng_US')
