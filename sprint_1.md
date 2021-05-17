# 05/11 - 05/18
## 05/11
Create Trello Board, Backlog

## 05/12
Build UE, FP crawler to crawl diner list
1. Use Selenium to build both crawlers.
2. PJ finds that there are API on both websites that could retrun diner list.
3. FP's vendors API is easy to request, and will return as many diners as it have with custom limit.
4. UE's not that easy, it has offset, limit and hasMore with a complicated rule that makes response unstable.
5. Since FP's API is easy to use, and selenium scroll will take almost forever( 2 hours), I use FP's API to get diner list.
6. I use selenium to get UE's list, but find out that I will need diner's uuid to make further request for diner detail.
7. However, uuid could only be found in UE's feedAPI response. Fortunately, I found a package called selenium-wire, that could interpret every request and response during selenium working.

## 05/13
Extend UE, FP crawler to crawl diners' detail
1. Using first day's result, I could send requests to UE and FP to get diners' detail.
2. Although it needs lots of work to get and clean data, it's working.

## 05/14
Build GM review crawler
1. There is Google Map API that could return store detail include reviews, however, it will only return 5 latest.
2. So I had to use selenium to get info, click button and scroll to get latest 40 reviews.
3. Selenium-wire is useless since GM's request and response are hard to read and parse.

## 05/15, 05/16, 05/17
Error proofed All crawlers
1. All crawlers are working while crawl small amounts of diners, but sometime they will crash.
2. Thus I add lots of try/except block in my crawlers to prevent crash and log errors to DB.
3. I will have to find more elegant way in the future, and must try to log those messages to AWS CloudWatch, but it's working for now, after a long, painful process.

## 05/17
AWS Lambda with selenium
1. I found and use these tutorials to use selenium on AWS Lambda
[Docker 基礎中文教學](https://cwhu.medium.com/docker-tutorial-101-c3808b899ac6)
[pychromeless, a project to combine python, chrome, selenium on AWS lambda](https://github.com/jairovadillo/pychromeless)
[More detailed tutorial on pychromeless](https://robertorocha.info/setting-up-a-selenium-web-scraper-on-aws-lambda-with-python/)
2. I could use selenium to open headless chrome and print current_url now, but I still need to find out:how to use selenium-wire, multiple crawler, crawler after crawler

## 05/18
