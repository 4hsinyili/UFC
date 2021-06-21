# for django
from django.shortcuts import render, redirect

# for django api rate limiter
from django.utils.decorators import method_decorator
from ratelimit.decorators import ratelimit

# for django restful api
from rest_framework import views
from rest_framework.response import Response
from rest_framework.parsers import JSONParser

# for mongo db control
from pymongo import MongoClient

# for timing
import datetime

# home-made modules
# for mysql and mongo query
from .models import Favorites, Noteq
from .mongo_query import DashBoardQuery, FavoritesQuery, FiltersQuery, SearcherQuery, DinerInfoQuery

# for return data to frontend
from .serializers import DinerSerializer, FilterSerializer, DashBoardSerializer

# for gile handling
import env
import conf

# my utility belt
import utils

# Create your views here.
MONGO_EC2_URI = env.MONGO_EC2_URI
DB_NAME = conf.DB_NAME
LOG_COLLECTION = conf.LOG_COLLECTION
MATCHED_COLLECTION = conf.MATCHED_COLLECTION
MATCH = conf.MATCH
TRIGGERED_BY_LIST = conf.TRIGGERED_BY_LIST
PAGE_LIMIT = conf.PAGE_LIMIT

admin_client = MongoClient(MONGO_EC2_URI)
db = admin_client[DB_NAME]
checker = utils.Checker(db, MATCHED_COLLECTION, LOG_COLLECTION, r_triggered_by=MATCH)
searcher = SearcherQuery(db, MATCHED_COLLECTION)


def assemble_diners_response(diners, offset, limit, diners_count):
    if not diners:
        return Response({
            'no_data': 1
        })
    if offset + limit < diners_count:
        has_more = True
    else:
        has_more = False
    if has_more:
        next_offset = offset + limit
    else:
        next_offset = 0
    data = DinerSerializer(diners, many=True).data
    response = Response({
            'next_offset': next_offset,
            'has_more': has_more,
            'max_page': diners_count // limit,
            'data_count': len(diners),
            'data': data,
            'no_data': 0
            })
    return response


def check_user_authenticated(user):
    if user.is_authenticated:
        user = user
    else:
        user = False
    return user


class DashBoardAPI(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        dashboard_waiter = DashBoardQuery(db, LOG_COLLECTION, TRIGGERED_BY_LIST)
        end_date_time = datetime.datetime.strptime(request.data['end_date_time'], '%Y-%m-%d %H:%M')
        start_date_time = datetime.datetime.strptime(request.data['start_date_time'], '%Y-%m-%d %H:%M')
        result = dashboard_waiter.main(end_date_time, start_date_time)
        data = DashBoardSerializer(result, many=False).data
        return Response({
            'data': data
        })


class DinerSearchAPI(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        # start = time.time()
        condition = request.data['condition']
        user = check_user_authenticated(request.user)
        offset = request.data['offset']
        triggered_at = checker.get_triggered_at()
        diners, diners_count = searcher.get_search_result(condition, triggered_at, offset, user)
        response = assemble_diners_response(diners, offset, PAGE_LIMIT, diners_count)
        # stop = time.time()
        # print('post DinerSearch took: ', stop - start, 's.')
        return response


class DinerShuffleAPI(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        # start = time.time()
        user = check_user_authenticated(request.user)
        triggered_at = checker.get_triggered_at()
        diners = searcher.get_random(triggered_at, user)
        response = assemble_diners_response(diners, 0, PAGE_LIMIT, 6)
        # stop = time.time()
        # print('post DinerSearch took: ', stop - start, 's.')
        return response


class DinerInfoAPI(views.APIView):
    parser_classes = [JSONParser]

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='GET'))
    def get(self, request):
        # start = time.time()

        uuid_ue = self.request.query_params.get('uuid_ue', '')
        uuid_fp = self.request.query_params.get('uuid_fp', '')

        user = check_user_authenticated(request.user)
        info_waiter = DinerInfoQuery(db, MATCHED_COLLECTION)
        diner = info_waiter.get_diner(uuid_ue, uuid_fp, user)
        if not diner:
            return Response({'data': '404'})
        data = DinerSerializer(diner, many=False).data
        # stop = time.time()
        # print('get DinerInfo took: ', stop - start, 's.')
        return Response({'data': data})


class FiltersAPI(views.APIView):

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='GET'))
    def get(self, request):
        # start = time.time()
        checker = utils.Checker(db, MATCHED_COLLECTION, LOG_COLLECTION, r_triggered_by=MATCH)
        triggered_at = checker.triggered_at
        filters_waiter = FiltersQuery(db, MATCHED_COLLECTION)
        filters = filters_waiter.get_filters(triggered_at)
        data = FilterSerializer(filters, many=False).data
        # stop = time.time()
        # print('get Filters took: ', stop - start, 's.')
        return Response({'data': data})


class FavoritesAPI(views.APIView):

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        user = check_user_authenticated(request.user)
        if not user:
            return Response({'message': 'need login'})
        request_data = request.data
        uuid_ue = request_data['uuid_ue']
        uuid_fp = request_data['uuid_fp']
        activate = request_data['activate']
        favorite_sqlrecord = Favorites.manager.update_favorite(user, uuid_ue, uuid_fp, activate)
        favorites_count = Favorites.manager.count_favorites(user)
        response = Response({'message': 'update favorite success', 'result': str(favorite_sqlrecord)})
        response.set_cookie('ufc_favorites_count', favorites_count)
        return response

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='GET'))
    def get(self, request):
        user = check_user_authenticated(request.user)
        if not user:
            return Response({'message': 'need login'})

        offset = int(self.request.query_params.get('offset', None))
        favorites_count = request.COOKIES.get('ufc_favorites_count')
        if favorites_count is None:
            favorites_count = Favorites.manager.count_favorites(request.user)
        else:
            favorites_count = int(favorites_count)
        if favorites_count == 0:
            response = Response({
                'no_data': 1
            })
            response.set_cookie('ufc_favorites_count', favorites_count)
            return response

        favorites_waiter = FavoritesQuery(db, MATCHED_COLLECTION)
        diners = favorites_waiter.get_favorites_diners(user, offset)
        response = assemble_diners_response(diners, offset, PAGE_LIMIT, favorites_count)
        response.set_cookie('ufc_favorites_count', favorites_count)
        return response


class NoteqAPI(views.APIView):

    @method_decorator(ratelimit(key='ip', rate='5/s', block=True, method='POST'))
    def post(self, request):
        user = check_user_authenticated(request.user)
        if not user:
            return Response({'message': 'need login'})
        request_data = request.data
        uuid_ue = request_data['uuid_ue']
        uuid_fp = request_data['uuid_fp']
        uuid_gm = request_data['uuid_gm']
        noteq_sqlrecord = Noteq.manager.add_noteq(request.user, uuid_ue, uuid_fp, uuid_gm)
        # print(noteq_sqlrecord)
        return Response({'message': 'update favorite success', 'result': str(noteq_sqlrecord)})


def dinerlist_view(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/dinerlist.html', {'user_is_authenticated': True, 'current_page': '店家列表'})
    else:
        return render(request, 'Diner_app/dinerlist.html', {'user_is_authenticated': False, 'current_page': '店家列表'})


def dinerinfo_view(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/dinerinfo.html', {'user_is_authenticated': True, 'current_page': '店家資訊'})
    else:
        return render(request, 'Diner_app/dinerinfo.html', {'user_is_authenticated': False, 'current_page': '店家資訊'})


def favorites_view(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/favorites.html', {'user_is_authenticated': True, 'current_page': '收藏'})
    else:
        return redirect('/user/login')


def dashboard_view(request):
    if request.user.is_authenticated:
        return render(request, 'Diner_app/dashboard.html', {'user_is_authenticated': True, 'current_page': '儀表板'})
    else:
        return render(request, 'Diner_app/dashboard.html', {'user_is_authenticated': False, 'current_page': '儀表板'})


def test_500_view():
    return Response({'message': 'success'})


def test_lambda_ip_view(request):
    def get_client_ip(request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            print("returning FORWARDED_FOR")
            ip = x_forwarded_for.split(',')[-1].strip()
        elif request.META.get('HTTP_X_REAL_IP'):
            print("returning REAL_IP")
            ip = request.META.get('HTTP_X_REAL_IP')
        else:
            print("returning REMOTE_ADDR")
            ip = request.META.get('REMOTE_ADDR')
        return ip
    ip = get_client_ip(request)
    print('------------ IP --------------')
    print(ip)
    print('++++++++++++ IP ++++++++++++++')
    return redirect('/')

# def forSSL(request):
#     file_content = env.VERIFY_DOMAIN
#     return HttpResponse(file_content, content_type='text/plain')
