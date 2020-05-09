'''
Prompt 
Write a server that acts as a bit.ly-like URL shortener.

The primary interface should be a JSON API that allows the following: 
● Create a random short link for arbitrary URLs, e.g., bit.ly/2FhfhXh 
○ The same URL should always generate the same random short link 
● Allow creating custom short links to arbitrary URLs, e.g., bit.ly/my-custom-link 
○ Multiple custom short links may map to the same URL 
● Provide a route for returning stats on a given short link, including: 
○ When the short link was created 
○ How many times the short link has been visited total 
○ A histogram of number of visits to the short link per day 
● Of course, the server itself should handle redirecting short links to the URLs it creates 
Everything else is up to you: the routes for the API, what its parameters and return values are, how it handles errors. Of course, I will be happy to talk any of these things out, but you are empowered to make whatever design decisions you like (and ideally explain them!). 

# TODO
Submission 
The goal should be to have a functioning server running locally on your computer (and ideally easy to run on someone else’s computer). Code should be submitted as a Git repo, with an initial commit when you start working. We don’t expect you to spend more than four hours on this problem, though we won’t strictly time you. At the end it should be as close to deployable as possible. We’ll go over it together to look at the code, and give you a chance to explain your design choices. 
Please be prepared to demo what you built when we review it together. 

Expectations 
Code. The final should be clean and easy to read, extensible, and narrowly scoped to the use-case. We don’t expect any crazy fancy abstractions, or for you to predict what features we’d want to add, but the code shouldn’t be painfully difficult to extend if we needed to either. 
Architecture + scaling. You should be able to talk through your architecture + explain the issues you would expect to face as you scale your solution. 
Comments. We don’t expect this to be crazy documented, only commented as much as you think would be needed in a production, deadline-driven environment. (Which is to say explain things that might be confusing, but otherwise the code can speak for itself.) 
Tests. Likewise we don’t expect a full suite of unit, integration and acceptance test, nor do you need to practice test-drive-development, but the key requirements should be tested—and testable—in a reasonable way. 
Language + technology. You can write the server in any language and using any technologies you choose (including your choice of database). There are no limitations on using open-source libraries, though be prepared to explain your choices. 
Help. Feel free to use the internet or whatever resources you need. The code itself should, of course, be your own. 

# TODO
Extra credit 
If you have extra time, implement any of the following features for extra credit. Or just be prepared to, like, talk about them: 
# TODO
● Deploy the server to an accessible URL 
# TODO
● Number of “unique” visitors to a given short link (you can define how we track visitors) 
# TODO
● A “global stats” endpoint, that aggregates some interesting stats across your URL-shortening platform (e.g., total number of links/visits per domain, histogram of total visits across the site)

'''

import hashlib
import json
import time
import urllib

from flask import Flask, request, jsonify, redirect
from flask_restful import Resource, Api, abort
# this may be non-pythonic, but that's what peewee documentation says to do
from peewee import *
from playhouse.shortcuts import model_to_dict, dict_to_model

import models

# TODO: these should come from ENV vars in production
DEBUG = True
HOST = '0.0.0.0'
PORT = 5000
baseurl = '{}:{}'.format(HOST, PORT)

app = Flask(__name__)
api = Api(app)


@app.before_request
def before_request():
    models.DATABASE.connect()


@app.after_request
def after_request(response):
    models.DATABASE.close()
    return response


# ###### #
# ROUTES #
# ###### #

# 1. URLs
# ###

class New_URL(Resource):
    '''
    This route is '/'
    only used to make a post to create a new url.
    '''

    def post(self):
        '''
        creates a new url shortlink without a custom link
        '''
        # try to create a url for the link
        try:
            url = models.URL.create(
                link=request.form['link'],
                hashstr=hashlib.md5(
                    bytes(request.form['link'], 'utf-8')).hexdigest()
                )
            return ({
                'hash': url.hashstr,
                'shortened link': '{}/{}'.format(baseurl, url.hashstr),
                'destination': url.link,
            }, 201)
        except IntegrityError:
            # if a url already exists for the hash, return the original hash
            url = models.URL.get(hashstr=hashlib.md5(
                    bytes(request.form['link'], 'utf-8')
                ).hexdigest())
            # return 200
            return ({
                'hash': url.hashstr,
                'link': '{}/{}'.format(baseurl, url.hashstr),
                'destination': url.link,
                }, 200)


api.add_resource(New_URL, '/')


class URL(Resource):
    '''
    Handles creating custom url shortlinks, as well as redirecting urls
    '''

    def get(self, urlhash):
        try:
            url = models.URL.get(hashstr=urlhash)
            models.Visit.create(url=url, ip=request.remote_addr)
            return redirect(url.link)
        except DoesNotExist:
            abort(404)

    def post(self, urlhash):
        '''
        creates a new url shortlink optional custom link
        '''
        try:
            url = models.URL.create(
                link=request.form['link'],
                hashstr=urllib.parse.quote(urlhash)
            )
            return ({
                'hash': url.hashstr,
                'link': '{}/{}'.format(baseurl, url.hashstr),
                'destination': url.link,
            }, 201)

        except IntegrityError:
            url = models.URL.get(hashstr=urlhash)
            return ({
                'hash': url.hashstr,
                'link': '{}/{}'.format(baseurl, url.hashstr),
                'destination': url.link,
                }, 200)
        # else:
        #     url = models.URL.create(
        #         link=request.form['link'],
        #         hashstr=hashstr
        #         )

# add the resource to the api
api.add_resource(URL, '/<urlhash>')


class Stats(Resource):
    '''
    Handles stats about a specific route
    '''
    def get(self, urlhash):
        url = models.URL.get(hashstr=urlhash)
        created = str(url.created)
        visits = models.Visit.select().join(
            models.URL).where(
                models.URL.hashstr == urlhash)

        histogram = {}
        visitors = []
        for visit in visits:
            if not visit.ip in visitors:
                visitors.append(visit.ip)
            date_str = str(visit.date)
            if date_str in histogram:
                histogram[date_str] += 1
            else:
                histogram[date_str] = 1
        return {
            'created': created,
            'visits': visits.count(),
            'histogram': histogram,
            'unique visitors':len(visitors)
        }


api.add_resource(Stats, '/<urlhash>/stats/')


if __name__ == '__main__':
    models.initialize()
    if DEBUG:
        app.run(debug=DEBUG, host=HOST, port=PORT)
    # TODO: make an else for running in prod
