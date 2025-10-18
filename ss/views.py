from django.http import Http404, JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect, render, get_object_or_404
from .forms import UrlForm, UserRegistrationForm, CustomDomainForm
from .models import Url, Click, CustomDomain
from .analytics import get_geolocation, parse_user_agent, get_client_ip
from decouple import config
import requests
import base64
from django.contrib.auth import login
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q, Avg
from ratelimit.decorators import ratelimit
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

    # Статистика кликов
    clicks_total = Click.objects.filter(url__user=user).count()
    click_day_counts = []
    for d in days:
        c = Click.objects.filter(url__user=user, created_at__date=d).count()
        click_day_counts.append(c)

    # Топ ссылок по кликам
    top_urls = (
        Url.objects.filter(user=user)
        .annotate(clicks_num=Count('clicks'))
        .order_by('-clicks_num', '-created_at')[:5]
    )

    context = {
        "total": total,
        "recent": recent,
        "active_count": active_count,
        "inactive_count": inactive_count,
        "avg_length": round(avg_length, 1),
        "last_created": last_created,
        "day_labels": day_labels,
        "day_counts": day_counts,
        "clicks_total": clicks_total,
        "click_day_counts": click_day_counts,
        "top_urls": top_urls,
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
@ratelimit(key='user_or_ip', rate='10/m', block=True)
def shorten(request):
    try:
        if request.method == "POST":
            urlObject = Url(user=request.user)
            urlForm = UrlForm(request.POST, instance=urlObject, user=request.user)
            if urlForm.is_valid():
                url = urlForm.cleaned_data["url"]
                result = isSecure(url)
                vendors, security_check_passed = result[0], result[1]
                
                # If security check failed (error occurred), show error
                if not security_check_passed:
                    return render(request, "ss/security.html", {"url": url, "shorten": True, "secure": False, "vendors": vendors})
                
                # If security check passed and URL is safe, create short URL
                if vendors and not any(v.get('result') == 'malicious' for v in vendors.values() if isinstance(v, dict)):
                    shortUrl = urlForm.save()
                    id = shortUrl.id
                    return render(request, "ss/url.html", {"url": shortUrl.url, "short": hash(id), "custom_domain": shortUrl.custom_domain})
                
                # If URL is malicious, show security report
                return render(request, "ss/security.html", {"url": url, "shorten": True, "secure": False, "vendors": vendors})
            return render(request, "ss/shorten.html", {"form": urlForm})
        else:
            form = UrlForm(user=request.user)
        return render(request, "ss/shorten.html", {"form": form})
    except Exception as e:
        # Log the error for debugging
        import traceback
        print(f"Error in shorten view: {e}")
        print(f"Traceback: {traceback.format_exc()}")
        form = UrlForm(user=request.user)
        return render(request, "ss/shorten.html", {"form": form, "error": f"Произошла ошибка: {str(e)}"})

@login_required(login_url='register')
@ratelimit(key='user_or_ip', rate='60/m', block=True)
def redirectUrl(request, short):
    id = getId(short)
    url = get_object_or_404(Url, id=id)
    if url.status:
        # фиксируем клик с аналитикой
        try:
            ip = get_client_ip(request)
            ua = request.META.get('HTTP_USER_AGENT', '')
            referer = request.META.get('HTTP_REFERER', '')
            
            # Получаем геолокацию
            geo_data = get_geolocation(ip)
            
            # Парсим user agent
            ua_data = parse_user_agent(ua)
            
            # Создаем запись клика с полной аналитикой
            Click.objects.create(
                url=url,
                user=request.user if request.user.is_authenticated else None,
                ip_address=ip,
                user_agent=ua,
                referer=referer,
                country=geo_data['country'],
                region=geo_data['region'],
                city=geo_data['city'],
                latitude=geo_data['latitude'],
                longitude=geo_data['longitude'],
                browser=ua_data['browser'],
                os=ua_data['os'],
                device_type=ua_data['device_type']
            )
        except Exception:
            pass
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
    return render(request, "ss/url.html", {"url": url.url, "short": hash(url.id), "custom_domain": url.custom_domain})


@login_required(login_url='register')
def analytics(request, id):
    """View detailed analytics for a specific URL"""
    url = get_object_or_404(Url, id=id)
    if request.user != url.user:
        raise Http404
    
    clicks = Click.objects.filter(url=url).order_by('-created_at')
    
    # Построение короткой ссылки с учетом кастомного домена
    scheme = 'https' if request.is_secure() else 'http'
    host = url.custom_domain.domain if getattr(url, 'custom_domain', None) else request.META.get('HTTP_HOST', '')
    short_code = str(hash(url.id))
    short_url = f"{scheme}://{host}/{short_code}"
    
    # Статистика по странам
    country_stats = clicks.values('country').annotate(count=Count('id')).order_by('-count')
    
    # Статистика по браузерам
    browser_stats = clicks.values('browser').annotate(count=Count('id')).order_by('-count')
    
    # Статистика по устройствам
    device_stats = clicks.values('device_type').annotate(count=Count('id')).order_by('-count')
    
    # Статистика по дням (последние 30 дней)
    today = timezone.now().date()
    days = [(today - datetime.timedelta(days=i)) for i in range(29, -1, -1)]
    day_labels = [d.strftime('%d.%m') for d in days]
    day_counts = []
    for d in days:
        count = clicks.filter(created_at__date=d).count()
        day_counts.append(count)
    
    context = {
        'url': url,
        'clicks': clicks[:50],  # Последние 50 кликов
        'total_clicks': clicks.count(),
        'country_stats': country_stats[:10],
        'browser_stats': browser_stats[:10],
        'device_stats': device_stats,
        'day_labels': day_labels,
        'day_counts': day_counts,
        'short_url': short_url,
    }
    
    return render(request, "ss/analytics.html", context)


@login_required(login_url='register')
def domains(request):
    """Manage custom domains"""
    if request.method == "POST":
        form = CustomDomainForm(request.POST)
        if form.is_valid():
            domain = form.save(commit=False)
            domain.user = request.user
            domain.save()
            return redirect('domains')
    else:
        form = CustomDomainForm()
    
    user_domains = CustomDomain.objects.filter(user=request.user)
    
    context = {
        'form': form,
        'domains': user_domains,
    }
    return render(request, "ss/domains.html", context)


@login_required(login_url='register')
def toggle_domain(request, domain_id):
    """Toggle domain active status"""
    domain = get_object_or_404(CustomDomain, id=domain_id, user=request.user)
    domain.is_active = not domain.is_active
    domain.save()
    return redirect('domains')


@login_required(login_url='register')
def delete_domain(request, domain_id):
    """Delete a custom domain"""
    domain = get_object_or_404(CustomDomain, id=domain_id, user=request.user)
    domain.delete()
    return redirect('domains')


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
        api = config('api', default='').strip()
        if not api:
            return [{'error': 'VirusTotal API key is missing. Set "api" in .env'}], True

        headers = {"accept": "application/json", "x-apikey": api}

        # Try to get existing report
        get_url = f"https://www.virustotal.com/api/v3/urls/{url_id}"
        res = requests.get(get_url, headers=headers).json()

        # If not found, submit and briefly poll
        if 'error' in res:
            submit = requests.post("https://www.virustotal.com/api/v3/urls", headers=headers, data={"url": url}).json()
            analysis_id = submit.get('data', {}).get('id')
            if analysis_id:
                import time
                for _ in range(5):
                    analysis = requests.get(f"https://www.virustotal.com/api/v3/analyses/{analysis_id}", headers=headers).json()
                    status_attr = analysis.get('data', {}).get('attributes', {}).get('status')
                    if status_attr == 'completed':
                        break
                    time.sleep(2)
                res = requests.get(get_url, headers=headers).json()

        if 'error' in res:
            return [{'error': res.get('error', {}).get('message', 'Unknown error')}], False

        if 'data' not in res or 'attributes' not in res['data']:
            return [{'error': 'Invalid response from VirusTotal API'}], False

        vendors = res['data']['attributes'].get('last_analysis_results', {})
        status = True
        for vendor in vendors:
            if vendors[vendor].get('result') == 'malicious':
                status = False
        if not vendors:
            return [{'error': 'Analysis report not ready yet. Please retry shortly.'}], False
        return [vendors, status]
    except Exception as e:
        return [{'error': f'Error checking URL: {str(e)}'}], False


@csrf_protect
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
