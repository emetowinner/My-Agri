from django.urls import path
from . import views

urlpatterns = [
    # Dashboard & Admin URLs
    path('', views.PublicNewsListView.as_view(), name='home'),
    path('dashboard/', views.DashboardView.as_view(), name='dashboard'),

    # Crawl Job URLs
    path('crawl-job/create/', views.CrawlJobCreateView.as_view(), name='create_crawl_job'),
    path('crawl-job/<int:pk>/', views.CrawlJobDetailView.as_view(), name='crawl_job_detail'),

    # Article Review URLs
    path('articles/pending/', views.PendingArticlesView.as_view(), name='pending_articles'),
    path('articles/approved/', views.ApprovedArticlesView.as_view(), name='approved_articles'),
    path('articles/<int:pk>/approve/', views.approve_article, name='approve_article'),
    path('articles/<int:pk>/reject/', views.reject_article, name='reject_article'),
    path('articles/<int:pk>/publish/', views.publish_article, name='publish_article'),

    # Manual Article Submission
    path('articles/add-manual/', views.ManualArticleCreateView.as_view(), name='add_manual_article'),

    # Public News URLs
    path('news/', views.PublicNewsListView.as_view(), name='public_news'),
    path('news/<int:pk>/', views.PublicNewsDetailView.as_view(), name='news_detail'),
]
