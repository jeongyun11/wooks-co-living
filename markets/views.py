from django.shortcuts import render, redirect
from .models import Post, Postimage
from .forms import PostForm, PostImageForm, DeleteImageForm
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

# Create your views here.

def index(request):
    dis = request.GET.get('dis')
    category = request.GET.get('category')
    q = request.GET.get('q')

    if dis == 'town':
        posts = Post.objects.filter(user__town=request.user.town)
    else:
        posts = Post.objects.filter(user__building=request.user.building)

    if category == 'used':
        posts = posts.filter(price__gt=0)
    elif category == 'free':
        posts = posts.filter(price=0)
    
    if q:
        posts = posts.filter(title__icontains=q)

    posts = posts.order_by('-pk')

    context = {'posts': posts}
    return render(request, 'markets/index.html', context)

def detail(request, market_pk):
    post = Post.objects.get(pk=market_pk)

    user_posts = post.user.user_markets_posts.order_by('-pk').exclude(pk=market_pk)[:6]

    if not request.session.get("post_viewed_{}".format(market_pk)):
        post.views += 1
        post.save()
        request.session["post_viewed_{}".format(market_pk)] = True

    context = {'post': post, 'user_posts': user_posts}
    return render(request, 'markets/detail.html', context)

@login_required
def create(request):
    if request.method == 'POST':
        post_form = PostForm(request.POST)
        files = request.FILES.getlist('image_first')

        if post_form.is_valid():
            form = post_form.save(commit=False)
            form.user = request.user
            form.save()
            for i in files:
                Postimage.objects.create(image_first=i, post=form)
            return redirect('markets:detail', form.pk)
        else:
            print(post_form.errors)
    else:
        post_form = PostForm()
        postimage_form = PostImageForm()

    context = {'post_form': post_form, 'postimage_form': postimage_form}
    return render(request, 'markets/create.html', context)

@login_required
def update(request, market_pk):
    post = Post.objects.get(pk=market_pk)

    if request.method == 'POST':
        post_form = PostForm(request.POST, instance=post)
        delete_ids = request.POST.getlist('delete_images')
        delete_form = DeleteImageForm(post=post, data=request.POST)
        files = request.FILES.getlist('image_first')

        if post_form.is_valid() and delete_form.is_valid():
            form = post_form.save()
            form.postimages.filter(pk__in=delete_ids).delete()
            for i in files:
                Postimage.objects.create(image_first=i, post=form)
            return redirect('markets:detail', form.pk)
        else:
            print(post_form.errors)

    else:
        post_form = PostForm(instance=post)
        delete_form = DeleteImageForm(post=post)
    if post.postimages.exists():
        postimage_form = PostImageForm(instance=post.postimages.first())
    else:
        postimage_form = PostImageForm()
    context = {
        'post': post,
        'post_form': post_form,
        'delete_form': delete_form,
        'postimage_form': postimage_form,
    }
    return render(request, 'markets/update.html', context)

@login_required
def delete(request, market_pk):
    post = Post.objects.get(pk=market_pk)
    if request.user == post.user:
        post.delete()
    return redirect('markets:index')

@login_required
def likes(request, market_pk):
    post = Post.objects.get(pk=market_pk)

    if post.user == request.user:
        error_message = "자신의 글은 관심글로 등록할 수 없습니다."
        return JsonResponse({'error': error_message})

    if request.user != post.user:
        if post.like_users.filter(pk=request.user.pk).exists():
            post.like_users.remove(request.user)
            is_liked = False
        else:
            post.like_users.add(request.user)
            is_liked = True

    context = {'is_liked': is_liked}
    return JsonResponse(context)