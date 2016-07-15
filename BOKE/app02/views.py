#_*_ coding:utf-8_*_

from django.shortcuts import render,redirect,HttpResponse
from django.contrib.auth.hashers import make_password
from django.contrib.auth import login,logout,authenticate
from django.core.paginator import Paginator,InvalidPage,EmptyPage,PageNotAnInteger
from django.conf import settings
from django.db.models import Count
# Create your views here.
from django.db import connection
from models import *
from forms import *
import json

def global_setting(request):
    SITE_URL = settings.SITE_URL
    SITE_NAME = settings.SITE_NAME
    SITE_DESC = settings.SITE_DESC
    MEDIA_URL = settings.MEDIA_URL
    # 分类信息获取（导航数据）
    category_list = Category.objects.all()[:6]

    # 文章归档数据
    archive_list = Article.objects.distinct_date()
    print '---------',archive_list
    # 广告数据（同学们自己完成）
    # 标签云数据（同学们自己完成）
    tag_list = Tag.objects.all()[:6]

    '''
    article_tag = Article.objects.values('tag').order_by('-tag')
    #article_tag_list = Article.objects.all().filter(tag=article_tag)
    article_tag_list = [Article.objects.get( pk=i['tag'] ) for  i in article_tag]
    print '=======',article_tag
    print '====55===',article_tag_list
    '''

    # 评论排行
    comment_count_list = Comment.objects.values('article').annotate(comment_count=Count('article')).order_by('-comment_count') #评论数的列表，根据评论的多少排序
    #print '---------',comment_count_list
    article_comment_list = [Article.objects.get(pk=comment['article']) for comment in comment_count_list] #文章评论列表，根据评论多的找到相应的文章
    #print '===33====',article_comment_list
    # 友情链接数据（同学们自己完成）
     # 文章排行榜数据（按浏览量和站长推荐的功能同学们自己完成）
    #站长推荐
    article_recommend = Article.objects.filter(is_recommend=True)
    #print '=======',article_recommend
    #浏览排行
    article_click_count = Article.objects.all().order_by('-click_count')
    #print '+++++++',article_click_count
#+++++++ [{'click_count': 0}, {'click_count': 8}, {'click_count': 0}, {'click_count': 6}]

    return locals()

def archive(request):
    try:
        # 先获取客户端提交的信息
        year = request.GET.get('year', None)
        month = request.GET.get('month', None)
        article_list = Article.objects.filter(date_publish__icontains=year+'-'+month)
        article_list = getPage(request, article_list)
    except Exception as e:
        print e
        #logger.error(e)
    return render(request, 'archive.html', locals())


def index(request):
    try:
        article_list = Article.objects.all()
        article_list = getPage(request,article_list)
    except Exception as e:
        print e
    return render(request,'index.html',locals())

def getPage(request,article_list):
    paginator = Paginator(article_list,2)
    try:
        page = int(request.GET.get('page',1))
        article_list = paginator.page(page)
    except(EmptyPage,InvalidPage,PageNotAnInteger):
        article_list=paginator.page(1)
    return article_list


# 文章详情
def article(request):
    try:
        # 获取文章id
        id = request.GET.get('id', None)
        try:
            # 获取文章信息
            article = Article.objects.get(pk=id)
        except Article.DoesNotExist:
            return render(request, 'failure.html', {'reason': '没有找到对应的文章'})


        # 评论表单
        comment_form = CommentForm({'author': request.user.username,
                                    'email': request.user.email,
                                    'url': request.user.url,
                                    'article': id}
                                   if request.user.is_authenticated()
                                   else{'article': id})

        # 获取评论信息
        comments = Comment.objects.filter(article=article).order_by('id')
        comment_count = comments.count()
        #print '=====',comment_count
        #comment_count_list = Comment.objects.values('article').annotate(comment_count=Count('article')).order_by('-comment_count')
        #article_comment_list = [Article.objects.get(pk=comment['article']) for comment in comment_count_list]
        comment_list = []
        for comment in comments:
            for item in comment_list:
                if not hasattr(item, 'children_comment'):
                    setattr(item, 'children_comment', [])
                if comment.pid == item:
                    item.children_comment.append(comment)
                    break
            if comment.pid is None:
                comment_list.append(comment)
    except Exception as e:
        print e
        #logger.error(e)
    return render(request, 'article.html', locals())





# 登录
def do_login(request):
    try:
        if request.method == 'POST':
            login_form = LoginForm(request.POST)
            if login_form.is_valid():
                # 登录
                username = login_form.cleaned_data["username"]
                password = login_form.cleaned_data["password"]
                user = authenticate(username=username, password=password)
                if user is not None:
                    user.backend = 'django.contrib.auth.backends.ModelBackend' # 指定默认的登录验证方式
                    login(request, user)
                else:
                    return render(request, 'failure.html', {'reason': '登录验证失败'})
                return redirect(request.POST.get('source_url'))
            else:
                return render(request, 'failure.html', {'reason': login_form.errors})
        else:
            login_form = LoginForm()
    except Exception as e:
        print e
    return render(request, 'login.html', locals())

# 注册
def do_reg(request):
    try:
        if request.method == 'POST':
            reg_form = RegForm(request.POST)
            if reg_form.is_valid():
                user = User.objects.create(username=reg_form.cleaned_data["username"],
                                           email = reg_form.cleaned_data["email"],
                                           url = reg_form.cleaned_data['url'],
                                           password = make_password(reg_form.cleaned_data['password']),)
                user.save()

                #登录
                user.backend = 'django.contrib.auth.backends.ModelBackend'
                login(request,user)
                return redirect(request.POST.get('source_url'))
            else:
                return render(request, 'failure.html', {'reason': reg_form.errors})

        else:
            reg_form = RegForm()
    except Exception as e:
        print e
    return render(request,'reg.html',locals())

# 注销
def do_logout(request):
    try:
        logout(request)
    except Exception as e:
        print e
        #logger.error(e)
    return redirect(request.META['HTTP_REFERER'])


# 提交评论
def comment_post(request):
    try:
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            #获取表单信息
            comment = Comment.objects.create(username=comment_form.cleaned_data["author"],

                                             content = comment_form.cleaned_data['comment'],
                                             article_id = comment_form.cleaned_data['article'],
                                             user = request.user if request.user.is_authenticated()else None)
            comment.save()
        else:
            return render(request, 'failure.html', {'reason': comment_form.errors})
    except Exception as e:
        print e
        #logger.error(e)
    return redirect(request.META['HTTP_REFERER'])



def category(request):
    try:
        # 先获取客户端提交的信息
        cid = request.GET.get('cid', None)
        try:
            category = Category.objects.get(pk=cid)
        except Category.DoesNotExist:
            return render(request, 'failure.html', {'reason': '分类不存在'})
        article_list = Article.objects.filter(category=category)
        article_list = getPage(request, article_list)
    except Exception as e:
        print e
        #logger.error(e)
    return render(request, 'category.html', locals())

def tag(request):
    try:
        tid = request.GET.get('tid',None)
        try:
            tag = Tag.objects.get(pk=tid)
        except Tag.DoesNotExist:
            return render(request,'failure.html',{'reason':'标签不存在'})

        article_list =Article.objects.filter(tag=tag)
        article_list = getPage(request,article_list)
    except Exception as e:
        print e
        #logger.error(e)
    return render(request, 'tag.html', locals())


