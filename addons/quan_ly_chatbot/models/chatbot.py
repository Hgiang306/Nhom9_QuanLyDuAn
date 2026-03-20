# -*- coding: utf-8 -*-
import re
import json
import logging
import os
import requests
from odoo import models, fields, api

_logger = logging.getLogger(__name__)
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"


class ChatbotConversation(models.Model):
    _name = 'chatbot.conversation'
    _description = 'Cuộc hội thoại Chatbot'
    _order = 'create_date desc'

    name = fields.Char('Tiêu đề', compute='_compute_name', store=True)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    message_ids = fields.One2many('chatbot.message', 'conversation_id', string='Tin nhắn')
    active = fields.Boolean(default=True)

    @api.depends('message_ids')
    def _compute_name(self):
        for r in self:
            first = r.message_ids.filtered(lambda m: m.is_user).sorted('create_date')[:1]
            if first:
                r.name = (first.content[:50] + '...') if len(first.content) > 50 else first.content
            else:
                r.name = f'Hội thoại #{r.id or "mới"}'


class ChatbotMessage(models.Model):
    _name = 'chatbot.message'
    _description = 'Tin nhắn Chatbot'
    _order = 'create_date asc'

    conversation_id = fields.Many2one('chatbot.conversation', ondelete='cascade')
    content = fields.Text('Nội dung', required=True)
    is_user = fields.Boolean('Từ người dùng', default=True)
    timestamp = fields.Datetime(default=fields.Datetime.now)
    intent = fields.Char('Intent')


class ChatbotAssistant(models.Model):
    _name = 'chatbot.assistant'
    _description = 'Chatbot Assistant'

    name = fields.Char('Tên', default='AI Assistant')
    active = fields.Boolean(default=True)
    gemini_api_key = fields.Char('Gemini API Key')
    use_gemini = fields.Boolean('Dùng Gemini AI', default=True)
    temperature = fields.Float('Temperature', default=0.7)
    max_tokens = fields.Integer('Max Tokens', default=1000)

    # ── System prompt ─────────────────────────────────────────────────────────
    def _get_system_prompt(self):
        today = fields.Date.today().strftime('%d/%m/%Y')
        return f"""Bạn là AI Assistant - trợ lý thông minh của hệ thống Quản lý Dự Án & Công Việc.
Ngày hôm nay: {today}

🎯 Nhiệm vụ:
1. Hỗ trợ tra cứu thông tin dự án, công việc
2. Hướng dẫn quy trình tạo/giao/phê duyệt công việc
3. Cảnh báo công việc quá hạn, rủi ro dự án
4. Thống kê nhanh tiến độ dự án

📋 Quy tắc:
- Trả lời ngắn gọn, rõ ràng bằng tiếng Việt
- Dùng emoji phù hợp, bullet points dễ đọc
- Luôn thân thiện và chuyên nghiệp
- Nếu không có dữ liệu cụ thể, hướng dẫn người dùng tìm ở đâu"""

    # ── Gemini API ────────────────────────────────────────────────────────────
    def _call_gemini(self, message, context=''):
        try:
            api_key = self.gemini_api_key or os.environ.get('GEMINI_API_KEY', '')
            if not api_key:
                _logger.warning("Gemini: Không có API key")
                return None
            _logger.info(f"Gemini: Đang gọi API, key={api_key[:8]}...")
            prompt = f"{self._get_system_prompt()}\n\nDữ liệu hệ thống:\n{context}\n\nCâu hỏi: {message}"
            resp = requests.post(
                f"{GEMINI_API_URL}?key={api_key}",
                json={"contents": [{"parts": [{"text": prompt}]}],
                      "generationConfig": {"temperature": self.temperature, "maxOutputTokens": self.max_tokens}},
                headers={"Content-Type": "application/json"},
                timeout=30,
            )
            _logger.info(f"Gemini: HTTP status={resp.status_code}")
            if resp.status_code == 200:
                data = resp.json()
                return data['candidates'][0]['content']['parts'][0]['text']
            else:
                _logger.warning(f"Gemini: Lỗi {resp.status_code} - {resp.text[:300]}")
        except Exception as e:
            _logger.warning(f"Gemini error: {e}")
        return None

    # ── Context từ hệ thống ───────────────────────────────────────────────────
    def _get_context(self, intent):
        lines = []
        try:
            user = self.env.user
            nv = self.env['nhan_vien'].search([('user_id', '=', user.id)], limit=1)
            lines.append(f"Người dùng: {user.name}" + (f" | Nhân viên: {nv.name}" if nv else ""))

            # Thống kê dự án
            DuAn = self.env['du_an']
            lines.append(f"Dự án đang thực hiện: {DuAn.search_count([('tien_do_du_an','=','dang_thuc_hien')])}")
            lines.append(f"Dự án hoàn thành: {DuAn.search_count([('tien_do_du_an','=','hoan_thanh')])}")

            # Thống kê công việc
            CV = self.env['cong_viec']
            lines.append(f"Công việc đang thực hiện: {CV.search_count([('trang_thai','=','dang_thuc_hien')])}")
            lines.append(f"Công việc chờ phê duyệt: {CV.search_count([('trang_thai','=','cho_phe_duyet')])}")
            lines.append(f"Công việc quá hạn: {CV.search_count([('han_chot','<',fields.Datetime.now()),('trang_thai','not in',['hoan_thanh','tu_choi'])])}")

            # Công việc của user hiện tại
            if nv:
                my_cv = CV.search([('nhan_vien_ids', 'in', nv.id), ('trang_thai', 'not in', ['hoan_thanh', 'tu_choi'])], limit=5)
                if my_cv:
                    lines.append(f"Công việc của {nv.name}:")
                    for cv in my_cv:
                        lines.append(f"  - {cv.ten_cong_viec} [{cv.trang_thai}] | Dự án: {cv.du_an_id.ten_du_an}")

            # Rủi ro
            RuiRo = self.env['rui_ro']
            lines.append(f"Rủi ro mức đỏ chưa xử lý: {RuiRo.search_count([('muc_do_rui_ro','=','do'),('trang_thai','!=','da_xu_ly')])}")
        except Exception as e:
            _logger.warning(f"Context error: {e}")
        return "\n".join(lines)

    # ── Intent detection ──────────────────────────────────────────────────────
    def _detect_intent(self, msg):
        msg = msg.lower()
        patterns = {
            'cong_viec_cua_toi': [r'công việc của tôi', r'việc của tôi', r'task của tôi', r'tôi có việc'],
            'du_an':             [r'dự án', r'project', r'tiến độ dự án'],
            'qua_han':           [r'quá hạn', r'trễ hạn', r'deadline', r'hết hạn'],
            'rui_ro':            [r'rủi ro', r'risk', r'cảnh báo'],
            'thong_ke':          [r'thống kê', r'báo cáo', r'tổng quan', r'bao nhiêu', r'số lượng'],
            'huong_dan':         [r'làm sao', r'cách', r'hướng dẫn', r'như thế nào', r'quy trình'],
            'chao':              [r'^(xin chào|hello|hi|chào|hey)\b'],
        }
        for intent, kws in patterns.items():
            for kw in kws:
                if re.search(kw, msg):
                    return intent
        return 'general'

    # ── Rule-based responses ──────────────────────────────────────────────────
    def _rule_response(self, intent, msg):
        CV = self.env['cong_viec']
        DuAn = self.env['du_an']
        user = self.env.user
        nv = self.env['nhan_vien'].search([('user_id', '=', user.id)], limit=1)

        if intent == 'chao':
            return (f"👋 Xin chào **{user.name}**!\n\nTôi là AI Assistant của hệ thống Quản lý Dự Án.\n\n"
                    "Tôi có thể giúp bạn:\n• 📋 Xem công việc của bạn\n• 📊 Thống kê tiến độ dự án\n"
                    "• ⚠️ Cảnh báo công việc quá hạn\n• 🔴 Kiểm tra rủi ro\n\n❓ Bạn cần hỗ trợ gì?",
                    ['Công việc của tôi', 'Thống kê dự án', 'Công việc quá hạn'])

        if intent == 'cong_viec_cua_toi':
            if not nv:
                return ("ℹ️ Không tìm thấy thông tin nhân viên của bạn.", [])
            cvs = CV.search([('nhan_vien_ids', 'in', nv.id), ('trang_thai', 'not in', ['hoan_thanh', 'tu_choi'])], limit=8)
            if not cvs:
                return ("✅ Bạn không có công việc nào đang chờ xử lý.", ['Xem tất cả công việc'])
            lines = [f"📋 **Công việc của {nv.name}** ({len(cvs)} việc đang xử lý):\n"]
            status_icon = {'cho_xac_nhan': '⏳', 'dang_thuc_hien': '🔵', 'cho_phe_duyet': '🟡', 'tri_hoan': '🟠'}
            for cv in cvs:
                icon = status_icon.get(cv.trang_thai, '📌')
                han = cv.han_chot.strftime('%d/%m/%Y %H:%M') if cv.han_chot else 'Chưa có'
                lines.append(f"{icon} **{cv.ten_cong_viec}**\n   Dự án: {cv.du_an_id.ten_du_an} | Hạn: {han}")
            return ('\n'.join(lines), ['Công việc quá hạn', 'Thống kê dự án'])

        if intent == 'qua_han':
            qua_han = CV.search([('han_chot', '<', fields.Datetime.now()), ('trang_thai', 'not in', ['hoan_thanh', 'tu_choi'])])
            if not qua_han:
                return ("✅ Không có công việc nào quá hạn. Tốt lắm!", [])
            lines = [f"⏰ **{len(qua_han)} công việc đang quá hạn:**\n"]
            for cv in qua_han[:6]:
                lines.append(f"🔴 **{cv.ten_cong_viec}** | {cv.du_an_id.ten_du_an}")
            return ('\n'.join(lines), ['Xem chi tiết', 'Công việc của tôi'])

        if intent == 'du_an':
            du_ans = DuAn.search([('tien_do_du_an', '=', 'dang_thuc_hien')], limit=6)
            if not du_ans:
                return ("ℹ️ Hiện không có dự án nào đang thực hiện.", [])
            lines = [f"📊 **{len(du_ans)} dự án đang thực hiện:**\n"]
            for da in du_ans:
                lines.append(f"🔵 **{da.ten_du_an}** — {da.phan_tram_du_an:.0f}% hoàn thành")
            return ('\n'.join(lines), ['Thống kê tổng quan', 'Rủi ro dự án'])

        if intent == 'rui_ro':
            RuiRo = self.env['rui_ro']
            do = RuiRo.search([('muc_do_rui_ro', '=', 'do'), ('trang_thai', '!=', 'da_xu_ly')])
            vang = RuiRo.search([('muc_do_rui_ro', '=', 'vang'), ('trang_thai', '!=', 'da_xu_ly')])
            lines = [f"⚠️ **Tình trạng rủi ro:**\n",
                     f"🔴 Mức đỏ (≥17 điểm): **{len(do)}** rủi ro",
                     f"🟡 Mức vàng (10-16 điểm): **{len(vang)}** rủi ro"]
            if do:
                lines.append("\n**Rủi ro đỏ cần xử lý ngay:**")
                for r in do[:4]:
                    lines.append(f"  • {r.ten_rui_ro} | {r.du_an_id.ten_du_an} | Điểm: {r.diem_rui_ro}")
            return ('\n'.join(lines), ['Xem tất cả rủi ro', 'Thống kê dự án'])

        if intent == 'thong_ke':
            total_da = DuAn.search_count([])
            dang_th = DuAn.search_count([('tien_do_du_an', '=', 'dang_thuc_hien')])
            hoan_th = DuAn.search_count([('tien_do_du_an', '=', 'hoan_thanh')])
            total_cv = CV.search_count([])
            cv_done = CV.search_count([('trang_thai', '=', 'hoan_thanh')])
            cv_qh = CV.search_count([('han_chot', '<', fields.Datetime.now()), ('trang_thai', 'not in', ['hoan_thanh', 'tu_choi'])])
            return (
                f"📊 **Thống kê tổng quan:**\n\n"
                f"**Dự án:**\n• Tổng: {total_da} | Đang thực hiện: {dang_th} | Hoàn thành: {hoan_th}\n\n"
                f"**Công việc:**\n• Tổng: {total_cv} | Hoàn thành: {cv_done} | Quá hạn: {cv_qh}",
                ['Công việc của tôi', 'Rủi ro dự án']
            )

        if intent == 'huong_dan':
            return (
                "📚 **Hướng dẫn nhanh:**\n\n"
                "**Tạo công việc:**\nMenu Công Việc → Tạo → Điền thông tin → Lưu\n\n"
                "**Giao việc cho nhân viên:**\nMở công việc → Thêm nhân viên → Lưu → Nhân viên nhận thông báo\n\n"
                "**Phê duyệt công việc:**\nNhân viên nhấn 'Gửi duyệt' → Manager nhấn 'Phê duyệt'\n\n"
                "**Xem tiến độ dự án:**\nMenu Dự Án → Kanban view → Xem progress bar",
                ['Công việc của tôi', 'Thống kê dự án']
            )

        # general
        return (
            "🤔 Tôi chưa hiểu rõ câu hỏi của bạn.\n\nBạn có thể hỏi về:\n"
            "• Công việc của tôi\n• Tiến độ dự án\n• Công việc quá hạn\n• Rủi ro dự án\n• Thống kê tổng quan",
            ['Công việc của tôi', 'Thống kê dự án', 'Công việc quá hạn']
        )

    # ── Main entry point ──────────────────────────────────────────────────────
    @api.model
    def process_message(self, message, conversation_id=None):
        if conversation_id:
            conv = self.env['chatbot.conversation'].browse(conversation_id)
        else:
            conv = self.env['chatbot.conversation'].create({'user_id': self.env.user.id})

        self.env['chatbot.message'].create({'conversation_id': conv.id, 'content': message, 'is_user': True})

        intent = self._detect_intent(message)
        assistant = self.search([], limit=1)

        answer = None
        suggestions = []

        # Thử Gemini trước
        if assistant and assistant.use_gemini and assistant.gemini_api_key:
            context = self._get_context(intent)
            answer = assistant._call_gemini(message, context)

        # Fallback rule-based
        if not answer:
            answer, suggestions = self._rule_response(intent, message)

        self.env['chatbot.message'].create({'conversation_id': conv.id, 'content': answer, 'is_user': False, 'intent': intent})

        return {'conversation_id': conv.id, 'answer': answer, 'intent': intent, 'suggestions': suggestions}
