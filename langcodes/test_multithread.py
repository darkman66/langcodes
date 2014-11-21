"""
This file implements testing ing langcodes module for multithreaded env

Problem is still there if you try to acccess that module from multiple places at once
"""
import threading
from twisted.internet import reactor
from tag_parser import parse_tag


def parseMe(i, tag):
    print i, parse_tag(tag)



def startProcessing():
    for i, tag in enumerate(('en_US', 'en', 'en_gb')):
        reactor.callInThread(parseMe, i, tag)


reactor.callInThread(startProcessing)
reactor.run()
