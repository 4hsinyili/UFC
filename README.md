# UberEats & FoodPanda Comparison (UFC)

One stop restaurants rating comparison website for AppWorks School using information crawled from Uber Eats, Food Panda and Google Map.

Website url: https://4hsinyili-ufc.xyz

You will need an account to add restaurant into favorites, here is a test account:
* Email: test_ufc@ufc.xyz
* Password: comparethem2021

## Table of Contents
* [Technologies](##Technologies)
* [Data Pipeline](#Data-Pipeline)
* [Server Structure](#Server-Structure)
* [MySQL Schema](#MySQL-Schema)
* [Features](#Features)

## Technologies
> Data Pipeline
* AWS Cloud Watch
* AWS Lambda
* AWS Step Function
* crontab

> Backend
* Django

> Database
* MongoDB
* MySQL

> Frontend
* HTML
* CSS
* JavaScript

> Networking
* Nginx
* SSL Certificate(ZeroSSL)

> Others
* AWS EC2
* AWS RDS
* AWS S3
* Docker
* Google Place API
* Selenium


## Data Pipeline
For better resolution, please view [Original Image](https://appworks-school-hsinyili.s3.ap-northeast-1.amazonaws.com/UFC_Data_Pipeline.png).

![](ReadmeMaterial/UFC_Data_Pipeline.png)

## Server Structure
![](ReadmeMaterial/Server_Structure.png)
## MySQL Schema
![](ReadmeMaterial/MySQL_Schema.png)
## Features
### Dashboard
#### Diagrams:

![](ReadmeMaterial/dashboard_view.gif)

#### Pick a range you like to see:

![](ReadmeMaterial/dashboard_pick_date_range.gif)

### Search with custom conditions

#### Search with keyword:

![](ReadmeMaterial/dinerlist_search_keyword.gif)

#### Filter restaurants:

![](ReadmeMaterial/dinerlist_filter.gif)

#### Sort restaurants:

![](ReadmeMaterial/dinerlist_sort.gif)

### Find Cheaper Items
#### Show items thar are cheaper on UberEats or FoodPanda.

![](ReadmeMaterial/dinerinfo_cheaper.gif)

### Shuffle
#### Shuffle restaurants if you can't decide what to eat:

![](ReadmeMaterial/dinerlist_shuffle.gif)

#### Shuffle restaurants with conditions:
![](ReadmeMaterial/dinerlist_shuffle_with_condition.gif)
### Favorite
#### Add restaurants to your favorite:

![](ReadmeMaterial/favorite.gif)