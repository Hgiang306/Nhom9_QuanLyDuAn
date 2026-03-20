# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import json


class ChatbotController(http.Controller):

    @http.route('/chatbot/message', type='json', auth='user', methods=['POST'])
    def send_message(self, message, conversation_id=None, **kwargs):
        result = request.env['chatbot.assistant'].process_message(message, conversation_id)
        return result

    @http.route('/chatbot/history', type='json', auth='user', methods=['POST'])
    def get_history(self, conversation_id, **kwargs):
        conv = request.env['chatbot.conversation'].browse(conversation_id)
        if not conv.exists():
            return {'messages': []}
        messages = []
        for msg in conv.message_ids:
            messages.append({
                'content': msg.content,
                'is_user': msg.is_user,
                'timestamp': msg.timestamp.strftime('%H:%M') if msg.timestamp else '',
            })
        return {'messages': messages}
