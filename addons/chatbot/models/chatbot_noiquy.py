# -*- coding: utf-8 -*-
import os
import requests
from odoo import fields, models, api, modules, _
from odoo.exceptions import UserError

class ChatbotNoiQuyChat(models.Model):
    _name = "chatbot.noiquy.chat"
    _description = "Chatbot AI Nội Quy"
    _inherit = ['mail.thread']

    question = fields.Text(string="Nhập câu hỏi")
    answer = fields.Text(string="AI phản hồi", readonly=True)

    def _get_noiquy_content(self):
        module_path = modules.get_module_path('chatbot')
        file_path = os.path.join(module_path, 'data', 'noiquy.md')
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        return ""

    def action_ask(self):
        for rec in self:
            if not rec.question:
                continue
            
            user_q = rec.question
            rec.message_post(body=f"<b>Bạn:</b> {user_q}")
            content_md = self._get_noiquy_content()

            # Lấy lịch sử chat để AI nhớ ngữ cảnh
            history_messages = self.env['mail.message'].sudo().search([
                ('model', '=', self._name),
                ('res_id', '=', rec.id),
                ('message_type', '=', 'comment'),
            ], limit=10, order='id desc')

            messages = []
            messages.append({"role": "system", "content": f"Bạn là trợ lý nội quy công ty. Dữ liệu: {content_md}"})

            for msg in reversed(history_messages):
                role = "assistant" if "AI:" in (msg.body or "") else "user"
                clean_body = (msg.body or "").replace('<p>', '').replace('</p>', '').replace('<b>', '').replace('</b>', '').replace('<div style="color: #008f8c;">', '').replace('</div>', '')
                messages.append({"role": role, "content": clean_body})

            messages.append({"role": "user", "content": user_q})
            api_key = self.env["ir.config_parameter"].sudo().get_param("groq.api.key")

            try:
                response = self._call_groq_v2(messages, api_key)
                rec.message_post(body=f"<div style='color: #008f8c;'><b>AI:</b> {response}</div>")
                rec.write({'question': '', 'answer': response})
            except Exception as e:
                rec.message_post(body=f"<span style='color: red;'>Lỗi: {str(e)}</span>")
        return True

    def _call_groq_v2(self, messages, api_key):
        url = "https://api.groq.com/openai/v1/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": 0.5
        }
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]