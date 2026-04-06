from flask import Blueprint, render_template, request, jsonify
from flask_login import current_user
from models import db, Chat
from datetime import datetime
import urllib.request
import json

chatbot_bp = Blueprint('chatbot', __name__)

SYSTEM_PROMPT = """You are DeepGuard AI, an expert cybersecurity assistant for India.
You specialize in: deepfake detection, phishing, QR code fraud, UPI scams, data breaches,
dark web threats, password security, and online safety.
Keep answers short (3-5 sentences), practical, use emojis, mention Indian context when relevant."""

API_KEY = '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'  # ⚠️ Replace with your real key


def get_ai_response(message, history=[]):
    try:
        messages = []

        for h in history[-6:]:
            messages.append({"role": "user", "content": h.message})
            messages.append({"role": "assistant", "content": h.response})

        messages.append({"role": "user", "content": message})

        payload = json.dumps({
            "model": "claude-sonnet-4-20250514",
            "max_tokens": 500,
            "system": SYSTEM_PROMPT,
            "messages": messages
        }).encode('utf-8')

        req = urllib.request.Request(
            'https://api.anthropic.com/v1/messages',
            data=payload,
            headers={
                'Content-Type': 'application/json',
                'anthropic-version': '2023-06-01',
                'x-api-key': API_KEY
            },
            method='POST'
        )

        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return data['content'][0]['text']

    except Exception as e:
        print(f'AI Error: {e}')
        return get_fallback_response(message)


def get_fallback_response(message):
    msg = message.lower()

    responses = {
        'deepfake': '🎭 A deepfake uses AI to replace someone face or voice. Signs: blurring around hairlines, unnatural blinking, lip-sync lag. Use DeepGuard Detect to verify suspicious media!',
        'phishing': '📧 Phishing emails create false urgency and link to fake sites. Always check sender domain carefully. Never click suspicious links in emails or WhatsApp.',
        'password': '🔐 Use 12+ characters with uppercase, numbers and symbols. Use different passwords for every account and enable 2FA everywhere.',
        'qr': '🔲 QR fraud is rising fast in India! Always verify merchant name after scanning. Never enter your PIN to receive money — that is always a scam!',
        'upi': '💸 Never share your UPI PIN with anyone. Banks NEVER ask for your PIN over phone. Sending Rs.1 to receive money is always a scam!',
        'hack': '🚨 If hacked: change all passwords immediately, enable 2FA, check bank statements, and report at cybercrime.gov.in or call 1930.',
        'darkweb': '🌑 The dark web is where stolen data is sold. Use our Dark Web Monitor to check if your email appeared in known data breaches.',
        'breach': '🌑 If your data was breached: change passwords on ALL accounts using that email, enable 2FA, and monitor your bank statements.',
        'scam': '⚠️ Common India scams: lottery fraud, KYC update scams, fake job offers, loan app fraud. Report at cybercrime.gov.in or call 1930.',
        'vpn': '🔒 A VPN encrypts your internet traffic. Use it on public WiFi.',
        'virus': '🛡️ Install antivirus, keep Windows updated, never download from unknown sites.',
        'otp': '🔢 Never share your OTP with anyone — not even banks.',
        'wifi': '📶 Public WiFi is risky. Avoid banking or use VPN.',
        'help': '🤖 Ask me about deepfakes, phishing, scams, UPI, passwords, etc!'
    }

    for key, response in responses.items():
        if key in msg:
            return response

    return '🛡️ I am DeepGuard AI. Ask me anything about online safety, scams, or cybersecurity.'


@chatbot_bp.route('/chatbot')
def chatbot():
    history = []

    if current_user.is_authenticated:
        history = Chat.query.filter_by(user_id=current_user.id)\
            .order_by(Chat.created_at.asc()).limit(20).all()

    return render_template('chatbot.html', history=history)


@chatbot_bp.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json()

    if not data:
        return jsonify({'error': 'No data'}), 400

    message = data.get('message', '').strip()

    if not message:
        return jsonify({'error': 'Empty message'}), 400

    history = []

    if current_user.is_authenticated:
        history = Chat.query.filter_by(user_id=current_user.id)\
            .order_by(Chat.created_at.desc()).limit(6).all()
        history.reverse()

    response = get_ai_response(message, history)

    if current_user.is_authenticated:
        try:
            chat_entry = Chat(
                user_id=current_user.id,
                message=message,
                response=response,
                created_at=datetime.utcnow()
            )
            db.session.add(chat_entry)
            db.session.commit()
        except:
            pass

    return jsonify({'response': response})


    

    

    