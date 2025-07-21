from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from .forms import UrlForm, UserRegistrationForm
from .models import Url
from decouple import config
import requests
import base64
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from django.utils import timezone
import datetime
from django.db.models.functions import Length

# Create your views here.

def home(request):
    if not request.user.is_authenticated:
        return HttpResponseRedirect(reverse('register'))
    return redirect('dashboard')

@login_required(login_url='register')
def dashboard(request):
    user = request.user
    urls = Url.objects.filter(user=user).order_by('-created_at')
    total = urls.count()
    recent = urls[:5]
    active_count = urls.filter(status=True).count()
    inactive_count = urls.filter(status=False).count()
    avg_length = urls.aggregate(avg=Avg(Length('url')))['avg'] or 0
    last_created = urls.first().created_at if total else None

    # Готовим данные по дням (последние 7 дней)
    today = timezone.now().date()
    days = [(today - datetime.timedelta(days=i)) for i in range(6, -1, -1)]
    day_labels = [d.strftime('%d.%m') for d in days]
    day_counts = []
    for d in days:
        count = urls.filter(created_at__date=d).count()
        day_counts.append(count)

    context = {
        "total": total,
        "recent": recent,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "avg_length": round(avg_length, 1),
        "last_created": last_created,
        "day_labels": day_labels,
        "day_counts": day_counts,
    }
    return render(request, "ss/dashboard.html", context)


def register(request):
    if request.method == "POST":
        newUserForm = UserRegistrationForm(request.POST)
        if newUserForm.is_valid():
            saveSession = newUserForm.cleaned_data["saveSession"]
            newUser = newUserForm.save()
            login(request, newUser)
            if "urls" in request.session and saveSession:
                id_list = request.session["urls"]
                Url.objects.filter(id__in=id_list).update(user=request.user)
            return redirect("dashboard")
        return render(request, "registration/register.html", {"form": newUserForm})
    return render(request, "registration/register.html", {"form": UserRegistrationForm()})

@login_required(login_url='register')
def shorten(request):
    if request.method == "POST":
        urlObject = Url(user=request.user)
        urlForm = UrlForm(request.POST, instance=urlObject)
        if urlForm.is_valid():
            url = urlForm.cleaned_data["url"]
            result = isSecure(url)
            vendors, status = result[0], result[1]
            if status:
                shortUrl = urlForm.save()
                id = shortUrl.id
                return render(request, "ss/url.html", {"url": shortUrl.url, "short": hash(id)})
            return render(request, "ss/security.html", {"url": url, "shorten": True, "secure": status, "vendors": vendors})
        return render(request, "ss/shorten.html", {"form": urlForm})
    return render(request, "ss/shorten.html", {"form": UrlForm()})

@login_required(login_url='register')
def redirectUrl(request, short):
    id = getId(short)
    url = get_object_or_404(Url, id=id)
    if url.status:
        result = isSecure(url.url)
        vendors, status = result[0], result[1]
        return render(request, "ss/security.html", {"url": url.url, "secure": status, "vendors": vendors})
    return redirect("dashboard")#, message="url isn't active")

@login_required(login_url='register')
def viewUrls(request):
    user = request.user
    urls = Url.objects.filter(user=user)
    return render(request, "ss/myUrls.html", {"urls":urls})

@login_required(login_url='register')
def viewUrl(request, id):
    url = get_object_or_404(Url, id = id)
    if request.user != url.user:
        raise Http404
    return render(request, "ss/url.html", {"url": url.url, "short": hash(url.id)})


def hash(id):
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    shortUrl = ""
    while int(id):
        char = int(id % 62)
        shortUrl = alphabet[char-1] + shortUrl
        id /= 62
    return shortUrl


def getId(shortUrl):
    alphabet = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"
    id = 0
    base = 62
    reversedShortUrl = shortUrl[::-1]
    for idx, char in enumerate(reversedShortUrl):
        num = alphabet.index(char) + 1
        id += num * pow(base, idx)
    return id


def isSecure(url):
    try:
        url_id = base64.urlsafe_b64encode(f"{url}".encode()).decode().strip("=")
        api = config('api')
        api_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        headers = {
            "accept": "application/json",
            "x-apikey": api
        }
        response = requests.get(api_url, headers=headers)
        res = response.json()
        
        # Проверяем, есть ли ошибка в ответе
        if 'error' in res:
            # Если URL не найден или другие ошибки API
            return [{'error': res.get('error', {}).get('message', 'Unknown error')}, True]
        
        # Проверяем, есть ли data в ответе
        if 'data' not in res or 'attributes' not in res['data']:
            return [{'error': 'Invalid response from VirusTotal API'}, True]
        
        vendors = res['data']['attributes'].get('last_analysis_results', {})
        status = True
        for vendor in vendors:
            if vendors[vendor].get('result') == 'malicious':
                status = False
        return [vendors, status]
    except Exception as e:
        # В случае любых ошибок считаем URL безопасным
        return [{'error': f'Error checking URL: {str(e)}'}, True]


@csrf_exempt
@require_http_methods(["DELETE"])
def deleteUrl(request, url_id):
    """API endpoint для удаления URL"""
    try:
        url = get_object_or_404(Url, id=url_id)
        
        # Проверяем права доступа
        if request.user.is_authenticated:
            if url.user != request.user:
                return JsonResponse({'error': 'Access denied'}, status=403)
        else:
            # Для неавторизованных пользователей проверяем сессию
            if 'urls' not in request.session or url_id not in request.session['urls']:
                return JsonResponse({'error': 'Access denied'}, status=403)
            # Удаляем из сессии
            request.session['urls'].remove(url_id)
            request.session.modified = True
        
        url.delete()
        return JsonResponse({'success': True, 'message': 'URL deleted successfully'})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
