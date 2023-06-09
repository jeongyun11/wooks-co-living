from django.shortcuts import render, redirect
from .forms import PostForm, CommentForm
from .models import Post, Comment
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Count
from taggit.models import Tag
from datetime import datetime, timedelta

# Create your views here.
def index(request):
    all_posts = Post.objects.all()
    categories = Post.objects.values_list('category', flat=True).distinct()

    category = request.GET.get('category')
    q = request.GET.get('q')
    tag = request.GET.get('tag')

    if category:
        posts = Post.objects.filter(category=category).order_by('-created_at')
    else:
        posts = Post.objects.all().order_by('-created_at')

    if q:
        posts = posts.filter(
            Q(title__icontains=q) |
            Q(content__icontains=q) |
            Q(user__username__icontains=q)
        ).distinct()
        
    if tag:
        posts = posts.filter(tags__name=tag)

    # Get the tags related to the filtered posts
    filtered_tags = Tag.objects.filter(post__in=all_posts).annotate(num_times=Count('taggit_taggeditem_items')).order_by('-num_times')[:10]

    context = {
        'categories': categories,
        'posts': posts,
        'filtered_tags': filtered_tags,
        'category': category,
        'all_posts': all_posts,
    }
    return render(request, 'communities/index.html', context)


def category(request, category):
    posts = Post.objects.filter(category=category).order_by('-created_at')
    context = {
        'posts': posts,
    }
    return render(request, 'communities/category.html')

@login_required
def create(request):
    if request.method == "POST":
        tags = request.POST.get('tag','').split(',')
        post_form = PostForm(request.POST)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.user = request.user
            post.save()
            for tag in tags:
                tag = tag.strip()
                if tag != '':
                    post.tags.add(tag)
            post.save()
            return redirect('communities:detail', post.pk)
    else:
        post_form = PostForm()
    context = {
        'post_form': post_form,
    }
    return render(request, 'communities/create.html', context)

def detail(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    comments = post.comments.filter(parent_comment=None)
    comment_form = CommentForm()

    comment_pk = request.session.pop('comment_pk', None)

    if comment_pk:
        comment = Comment.objects.get(pk=comment_pk)
        comment_section_id = f'comment-{comment.pk}'
    else:
        comment = None
        comment_section_id = None

    if not request.session.get("post_viewed_{}".format(post_pk)):
        post.views += 1
        post.save()
        request.session["post_viewed_{}".format(post_pk)] = True
    
    context = {
        'post': post,
        'comments': comments,
        'comment_form': comment_form,
        'comment': comment,
        'comment_section_id': comment_section_id,
        'likes_count': post.like_users.count()-post.dislike_users.count()
    }
    response = render(request, 'communities/detail.html', context)

    # 조회수 기능 (쿠키 사용)
    expire_date, now = datetime.now(), datetime.now()
    expire_date += timedelta(days=1)
    expire_date = expire_date.replace(hour=0, minute=0, second=0, microsecond=0)
    expire_date -= now
    max_age = expire_date.total_seconds()

    cookie_value = request.COOKIES.get('hitboard', '_')

    if f'_{post.pk}_' not in cookie_value:
        cookie_value += f'{post.pk}_'
        response.set_cookie('hitboard', value=cookie_value, max_age=max_age, httponly=True)
        post.views += 1
        post.save()
    return response

def delete(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    if post.user == request.user:
        post.delete()
    return redirect('communities:index')

def update(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    if request.method == "POST":
        post.tags.clear()
        tags = request.POST.get('tag','').split(',')
        update_form = PostForm(request.POST, instance=post)
        if update_form.is_valid():
            update = update_form.save()
            for tag in tags:
                tag = tag.strip()
                if tag != '':
                    update.tags.add(tag)
            update.save()
            return redirect('communities:detail', post.pk)
    else:
        update_form = PostForm(instance=post)
    context = {
        'post': post,
        'update_form': update_form,
    }
    return render(request, 'communities/update.html', context)

@login_required
def scrapes(request, post_pk):
    post = Post.objects.get(pk=post_pk)

    if post.user == request.user:
        error_message = "자신의 글은 스크랩할 수 없습니다."
        return JsonResponse({"error": error_message})
    
    if post.scrape_users.filter(pk=request.user.pk).exists():
        post.scrape_users.remove(request.user)
        is_scraped = False
    else:
        post.scrape_users.add(request.user)
        is_scraped = True
    
    context = {
        "is_scraped": is_scraped,
    }

    return JsonResponse(context)

@login_required
def likes(request, post_pk):
    post = Post.objects.get(pk=post_pk)
    like_value = request.POST.get("like_value")

    if post.user == request.user:
        error_message = "자신의 글은 추천할 수 없습니다."
        return JsonResponse({"error": error_message})

    if like_value == "like":
        if post.like_users.filter(pk=request.user.pk).exists():
            post.like_users.remove(request.user)
            is_liked = False
            is_disliked = False

        elif post.dislike_users.filter(pk=request.user.pk).exists():
            post.dislike_users.remove(request.user)
            post.like_users.add(request.user)
            is_liked = True
            is_disliked = False

        else:
            post.like_users.add(request.user)
            is_liked = True
            is_disliked = False

    else:
        if post.dislike_users.filter(pk=request.user.pk).exists():
            post.dislike_users.remove(request.user)
            is_liked = False
            is_disliked = False

        elif post.like_users.filter(pk=request.user.pk).exists():
            post.like_users.remove(request.user)
            post.dislike_users.add(request.user)
            is_liked = False
            is_disliked = True

        else:
            post.dislike_users.add(request.user)
            is_liked = False
            is_disliked = True

    context = {
        "is_liked": is_liked,
        "is_disliked": is_disliked,
        "post_like": post.like_users.count()-post.dislike_users.count()
    }

    return JsonResponse(context)

@login_required
def comment_create(request, post_pk, parent_pk):
    post = Post.objects.get(pk=post_pk)
    if request.method == 'POST':
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.user = request.user
            comment.post = post
            if parent_pk != 0:
                parent_comment = Comment.objects.get(pk=parent_pk)
                comment.parent_comment = parent_comment
                comment.depth = parent_comment.depth + 10
                if comment.depth > 50:
                    comment.depth = 10
            comment.save()
            request.session['comment_pk'] = comment.pk

            return redirect('communities:detail', post.pk)

def comment_update(request, post_pk, comment_pk):
    comment = Comment.objects.get(pk=comment_pk)
    if request.method == "POST":
        comment_update_form = CommentForm(request.POST, instance=comment)
        if comment_update_form.is_valid():
            comment_update_form.save()
            return redirect('communities:detail', post_pk)
        else:
            print(comment_update_form.errors)
        
def comment_delete(request, post_pk, comment_pk):
    comment = Comment.objects.get(pk=comment_pk)

    if request.user == comment.user:
        comment.delete()

    post = Post.objects.get(pk=post_pk)
    comments = post.comments.filter(parent_comment=None)
    first_comment = comments.first()

    request.session['comment_pk'] = first_comment.pk

    return redirect('communities:detail', post_pk)

@login_required
def comment_likes(request, post_pk, comment_pk):
    comment = Comment.objects.get(pk=comment_pk)
    if request.user in comment.like_users.all():
        comment.like_users.remove(request.user)
        comment_is_liked = False
    else:
        comment.like_users.add(request.user)
        comment_is_liked = True
    context = {
        'comment_is_liked': comment_is_liked
    }
    return JsonResponse(context)

@login_required
def comment_dislikes(request, post_pk, comment_pk):
    comment = Comment.objects.get(pk=comment_pk)
    if request.user in comment.dislike_users.all():
        comment.dislike_users.remove(request.user)
        comment_is_disliked = False
    else:
        comment.dislike_users.add(request.user)
        comment_is_disliked = True
    context = {
        'comment_is_disliked': comment_is_disliked
    }
    return JsonResponse(context)