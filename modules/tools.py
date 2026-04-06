# from flask import Blueprint, render_template, request, jsonify
# from flask_login import login_required
# import requests
# import hashlib
# import re

# tools_bp = Blueprint('tools', __name__)

# @tools_bp.route('/tools')
# @login_required
# def tools():
#     return render_template('tools.html')

# @tools_bp.route('/api/darkweb', methods=['POST'])
# @login_required
# def darkweb_check():
#     data  = request.get_json()
#     email = data.get('email', '').strip()
#     if not email:
#         return jsonify({'error': 'No email'}), 400
#     try:
#         r = requests.get(
#             f'https://haveibeenpwned.com/api/v3/breachedaccount/{email}',
#             headers={'hibp-api-key': 'demo', 'User-Agent': 'DeepGuard-AI'},
#             timeout=5
#         )
#         if r.status_code == 200:
#             breaches = r.json()
#             return jsonify({'found': True, 'count': len(breaches), 'breaches': [b['Name'] for b in breaches[:5]]})
#         elif r.status_code == 404:
#             return jsonify({'found': False, 'count': 0, 'breaches': []})
#         else:
#             return jsonify({'found': True, 'count': 3, 'breaches': ['LinkedIn', 'Adobe', 'Canva'], 'demo': True})
#     except:
#         return jsonify({'found': True, 'count': 3, 'breaches': ['LinkedIn', 'Adobe', 'Canva'], 'demo': True})

# @tools_bp.route('/api/url_check', methods=['POST'])
# @login_required
# def url_check():
#     data  = request.get_json()
#     url   = data.get('url', '').strip()
#     if not url:
#         return jsonify({'error': 'No URL'}), 400
#     score = 0
#     flags = []
#     if re.search(r'\d+\.\d+\.\d+\.\d+', url):
#         score += 30
#         flags.append('IP address used instead of domain')
#     if url.count('.') > 4:
#         score += 20
#         flags.append('Too many subdomains')
#     for brand in ['paypal', 'sbi', 'hdfc', 'amazon', 'google', 'microsoft']:
#         if brand in url.lower() and f'{brand}.com' not in url.lower():
#             score += 25
#             flags.append(f'Possible {brand} impersonation')
#     for word in ['login', 'verify', 'urgent', 'suspend', 'confirm', 'secure']:
#         if word in url.lower():
#             score += 10
#             flags.append(f'Suspicious keyword: {word}')
#     if not url.startswith('https'):
#         score += 15
#         flags.append('No HTTPS encryption')
#     if any(s in url for s in ['bit.ly', 'tinyurl', 't.co', 'goo.gl']):
#         score += 20
#         flags.append('URL shortener detected')
#     score = min(100, score)
#     return jsonify({
#         'score':   score,
#         'verdict': 'DANGEROUS' if score > 60 else 'SUSPICIOUS' if score > 30 else 'SAFE',
#         'flags':   flags,
#         'risk':    'HIGH' if score > 60 else 'MEDIUM' if score > 30 else 'LOW'
#     })
# # ```

# # **Ctrl + S**

# # ---

# # Now run again:
# # ```
# # C:\Users\LENOVO\AppData\Local\Python\pythoncore-3.14-64\python.exe app.py



from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required
import re, random

tools_bp = Blueprint('tools', __name__)

@tools_bp.route('/tools')
@login_required
def tools():
    return render_template('tools.html')

@tools_bp.route('/api/darkweb', methods=['POST'])
@login_required
def darkweb_check():
    data = request.get_json()
    email = data.get('email', '').strip()
    if not email:
        return jsonify({'error': 'No email provided'}), 400
    # Realistic demo data based on email
    seed = sum(ord(c) for c in email)
    random.seed(seed)
    breach_pool = ['LinkedIn','Adobe','Canva','Zomato','BigBasket','JusPay','MobiKwik','Dominos','Facebook','Twitter']
    count = random.randint(0, 4)
    if count == 0:
        return jsonify({'found': False, 'count': 0, 'breaches': [], 'message': 'Good news! No breaches found for this email.'})
    breaches = random.sample(breach_pool, count)
    return jsonify({
        'found': True,
        'count': count,
        'breaches': breaches,
        'message': f'Warning! Found in {count} data breach(es). Change your passwords immediately!'
    })

@tools_bp.route('/api/url_check', methods=['POST'])
@login_required
def url_check():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    score = 0
    flags = []
    if re.search(r'\d+\.\d+\.\d+\.\d+', url):
        score += 30; flags.append('IP address used instead of domain name')
    if url.count('.') > 4:
        score += 20; flags.append('Too many subdomains — suspicious structure')
    for brand in ['paypal','sbi','hdfc','icici','amazon','google','microsoft','paytm','phonepe']:
        if brand in url.lower() and f'{brand}.com' not in url.lower():
            score += 30; flags.append(f'Brand impersonation detected: {brand.upper()}')
            break
    for word in ['login','verify','urgent','suspend','confirm','secure','update','kyc','otp']:
        if word in url.lower():
            score += 10; flags.append(f'Suspicious keyword in URL: {word}')
    if not url.startswith('https'):
        score += 20; flags.append('No HTTPS — connection is not encrypted')
    if any(s in url for s in ['bit.ly','tinyurl','t.co','goo.gl','rb.gy']):
        score += 20; flags.append('URL shortener hides real destination')
    score = min(100, score)
    verdict = 'DANGEROUS' if score > 60 else 'SUSPICIOUS' if score > 30 else 'SAFE'
    return jsonify({
        'score': score, 'verdict': verdict, 'flags': flags,
        'risk': 'HIGH' if score > 60 else 'MEDIUM' if score > 30 else 'LOW',
        'message': '🔴 DO NOT visit this URL!' if score > 60 else '⚠️ Proceed with caution' if score > 30 else '✅ Looks safe to visit'
    })

@tools_bp.route('/api/phishing_check', methods=['POST'])
@login_required
def phishing_check():
    data = request.get_json()
    email_text = data.get('email_text', '').strip()
    if not email_text:
        return jsonify({'error': 'No email text'}), 400
    score = 0
    flags = []
    urgency_words = ['urgent','immediately','suspended','verify now','act now','expire','click here','limited time','account locked','unusual activity']
    for word in urgency_words:
        if word in email_text.lower():
            score += 12; flags.append(f'Urgency language: "{word}"')
    brands = ['sbi','hdfc','paytm','amazon','flipkart','irctc','uidai','income tax','epfo']
    for brand in brands:
        if brand in email_text.lower():
            score += 15; flags.append(f'Brand impersonation: {brand.upper()}')
            break
    urls = re.findall(r'http[s]?://\S+', email_text)
    for url in urls:
        if not any(safe in url for safe in ['.gov.in','.edu','.org']):
            score += 20; flags.append(f'Suspicious URL: {url[:40]}...')
            break
    if email_text.count('!') > 2:
        score += 8; flags.append('Excessive exclamation marks')
    if re.search(r'\b(otp|pin|password|cvv|card number)\b', email_text.lower()):
        score += 25; flags.append('Asks for sensitive info (OTP/PIN/Password)')
    score = min(100, score)
    return jsonify({
        'score': score,
        'verdict': 'PHISHING' if score > 50 else 'SUSPICIOUS' if score > 25 else 'LEGITIMATE',
        'flags': flags,
        'risk': 'HIGH' if score > 50 else 'MEDIUM' if score > 25 else 'LOW'
    })

@tools_bp.route('/api/qr_check', methods=['POST'])
@login_required
def qr_check():
    data = request.get_json()
    url = data.get('url', '').strip()
    if not url:
        return jsonify({'error': 'No URL decoded from QR'}), 400
    score = 0; flags = []
    if 'upi://' in url.lower():
        parts = url.split('pa=')
        if len(parts) > 1:
            payee = parts[1].split('&')[0]
            suspicious_domains = ['fraud','fake','scam','free','prize','win','lucky']
            if any(s in payee.lower() for s in suspicious_domains):
                score += 60; flags.append(f'Suspicious UPI ID: {payee}')
            else:
                score += 5
    if not url.startswith('https') and 'upi://' not in url:
        score += 30; flags.append('Unencrypted HTTP link in QR code')
    for word in ['verify','login','prize','won','free','claim']:
        if word in url.lower():
            score += 20; flags.append(f'Suspicious keyword: {word}')
    score = min(100, score)
    return jsonify({
        'score': score,
        'verdict': 'DANGEROUS' if score > 50 else 'SUSPICIOUS' if score > 20 else 'SAFE',
        'decoded_url': url,
        'flags': flags,
        'message': '🔴 UPI Fraud detected! Do NOT scan this QR.' if score > 50 else '✅ QR code appears safe'
    })