#_*_coding:utf-8_*_
__author__ = 'zhangzhiyong'
from django.conf.urls import url
from app02.views import *

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^article/$', article, name='article'),
    url(r'^login', do_login, name='login'),
    url(r'^reg', do_reg, name='reg'),
    url(r'^logout$', do_logout, name='logout'),
    url(r'^comment/post/$', comment_post, name='comment_post'),
    url(r'^category/$', category, name='category'),
    url(r'^tag/$', tag, name='tag'),

     url(r'^archive/$', archive, name='archive'),
]