from django.urls import path
from . import views

# Imports for implementing RSS feed
from .feeds import LatestPostsFeed

# Мы определили пространство имен приложения в переменной app_name
app_name = 'blog'

urlpatterns = [
    path('', views.post_list, name='post_list'),  # for Post List FBV
    path('tag/<slug:tag_slug>/', views.post_list, name='post_list_by_tag'),  # for Post List FBV
    # path('', views.PostListView.as_view(), name='post_list'),  # for Post List CBV
    path(
        '<int:year>/<int:month>/<int:day>/<slug:post>/',
        views.post_detail,
        name='post_detail'
    ),
    path('<int:post_id>/share/', views.post_share, name='post_share'),
    path('feed/', LatestPostsFeed(), name='post_feed'),
    path('search/', views.post_search, name='search'),
]
