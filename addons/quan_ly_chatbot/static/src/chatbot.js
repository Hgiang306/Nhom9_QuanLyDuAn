/**
 * Chatbot Widget - Quản Lý Dự Án & Công Việc
 * Không dùng @odoo-module, dùng odoo.define legacy
 */
odoo.define('quan_ly_chatbot.chatbot', function (require) {
    'use strict';

    var core = require('web.core');
    var Widget = require('web.Widget');
    var session = require('web.session');

    var ChatbotWidget = Widget.extend({
        template: null,
        conversationId: null,
        isOpen: false,
        isTyping: false,

        start: function () {
            this._super.apply(this, arguments);
            this._renderUI();
            this._bindEvents();
            // Hiện welcome sau 1.5s
            setTimeout(() => this._showWelcome(), 1500);
        },

        _renderUI: function () {
            var html = `
            <button class="chatbot-fab" id="chatbot-fab" title="AI Assistant">
                🤖
                <span class="chatbot-badge" id="chatbot-badge">1</span>
            </button>
            <div class="chatbot-window" id="chatbot-window">
                <div class="chatbot-header">
                    <div class="chatbot-header-avatar">🤖</div>
                    <div class="chatbot-header-info">
                        <div class="chatbot-header-name">AI Assistant</div>
                        <div class="chatbot-header-status">Đang hoạt động</div>
                    </div>
                    <button class="chatbot-fullscreen" id="chatbot-fullscreen" title="Toàn màn hình">⛶</button>
                    <button class="chatbot-close" id="chatbot-close" title="Đóng">✕</button>
                </div>
                <div class="chatbot-messages" id="chatbot-messages">
                    <div class="chatbot-welcome" id="chatbot-welcome">
                        <div class="chatbot-welcome-icon">🤖</div>
                        <h3>Xin chào! Tôi là AI Assistant</h3>
                        <p>Tôi có thể giúp bạn tra cứu công việc, tiến độ dự án, cảnh báo rủi ro và nhiều hơn nữa.</p>
                    </div>
                </div>
                <div class="chatbot-suggestions" id="chatbot-suggestions">
                    <button class="chatbot-suggestion-btn" data-msg="Công việc của tôi">📋 Việc của tôi</button>
                    <button class="chatbot-suggestion-btn" data-msg="Thống kê dự án">📊 Thống kê</button>
                    <button class="chatbot-suggestion-btn" data-msg="Công việc quá hạn">⏰ Quá hạn</button>
                    <button class="chatbot-suggestion-btn" data-msg="Rủi ro dự án">⚠️ Rủi ro</button>
                </div>
                <div class="chatbot-input-area">
                    <textarea class="chatbot-input" id="chatbot-input"
                        placeholder="Nhập câu hỏi..." rows="1"></textarea>
                    <button class="chatbot-send" id="chatbot-send" title="Gửi">➤</button>
                </div>
            </div>`;

            var container = document.createElement('div');
            container.innerHTML = html;
            document.body.appendChild(container);
        },

        _bindEvents: function () {
            var self = this;

            document.getElementById('chatbot-fab').addEventListener('click', function () {
                self._toggleWindow();
            });

            document.getElementById('chatbot-close').addEventListener('click', function () {
                self._closeWindow();
            });

            document.getElementById('chatbot-fullscreen').addEventListener('click', function () {
                self._toggleFullscreen();
            });

            document.getElementById('chatbot-send').addEventListener('click', function () {
                self._sendMessage();
            });

            var input = document.getElementById('chatbot-input');
            input.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    self._sendMessage();
                }
            });
            input.addEventListener('input', function () {
                this.style.height = 'auto';
                this.style.height = Math.min(this.scrollHeight, 100) + 'px';
            });

            // Suggestion buttons (event delegation)
            document.getElementById('chatbot-suggestions').addEventListener('click', function (e) {
                var btn = e.target.closest('.chatbot-suggestion-btn');
                if (btn) {
                    var msg = btn.getAttribute('data-msg');
                    if (msg) self._sendMessageText(msg);
                }
            });
        },

        _toggleWindow: function () {
            if (this.isOpen) {
                this._closeWindow();
            } else {
                this._openWindow();
            }
        },

        _openWindow: function () {
            this.isOpen = true;
            document.getElementById('chatbot-window').classList.add('open');
            document.getElementById('chatbot-fab').style.background = 'linear-gradient(135deg,#4f46e5,#7c3aed)';
            document.getElementById('chatbot-badge').style.display = 'none';
            setTimeout(() => document.getElementById('chatbot-input').focus(), 300);
        },

        _closeWindow: function () {
            this.isOpen = false;
            document.getElementById('chatbot-window').classList.remove('open', 'fullscreen');
            document.getElementById('chatbot-fab').style.background = '';
            document.getElementById('chatbot-fullscreen').textContent = '⛶';
        },

        _toggleFullscreen: function () {
            var win = document.getElementById('chatbot-window');
            var btn = document.getElementById('chatbot-fullscreen');
            if (win.classList.contains('fullscreen')) {
                win.classList.remove('fullscreen');
                btn.textContent = '⛶';
                btn.title = 'Toàn màn hình';
            } else {
                win.classList.add('fullscreen');
                btn.textContent = '❐';
                btn.title = 'Thu nhỏ';
            }
        },

        _showWelcome: function () {
            // Hiện badge sau 1.5s để thu hút chú ý
            var badge = document.getElementById('chatbot-badge');
            if (badge) badge.style.display = 'flex';
        },

        _sendMessage: function () {
            var input = document.getElementById('chatbot-input');
            var text = input.value.trim();
            if (!text || this.isTyping) return;
            input.value = '';
            input.style.height = 'auto';
            this._sendMessageText(text);
        },

        _sendMessageText: function (text) {
            var self = this;
            if (!text || this.isTyping) return;

            // Ẩn welcome
            var welcome = document.getElementById('chatbot-welcome');
            if (welcome) welcome.style.display = 'none';

            // Hiện message user
            this._appendMessage(text, true);

            // Hiện typing
            this.isTyping = true;
            document.getElementById('chatbot-send').disabled = true;
            var typingId = this._appendTyping();

            // Cập nhật suggestions
            this._setSuggestions([]);

            // Gọi API
            session.rpc('/chatbot/message', {
                message: text,
                conversation_id: self.conversationId || false,
            }).then(function (result) {
                self._removeTyping(typingId);
                self.isTyping = false;
                document.getElementById('chatbot-send').disabled = false;

                if (result && result.answer) {
                    self.conversationId = result.conversation_id;
                    self._appendMessage(result.answer, false);
                    if (result.suggestions && result.suggestions.length) {
                        self._setSuggestions(result.suggestions);
                    }
                }
            }).catch(function (err) {
                self._removeTyping(typingId);
                self.isTyping = false;
                document.getElementById('chatbot-send').disabled = false;
                self._appendMessage('❌ Có lỗi xảy ra. Vui lòng thử lại.', false);
                console.error('Chatbot error:', err);
            });
        },

        _appendMessage: function (text, isUser) {
            var msgs = document.getElementById('chatbot-messages');
            var now = new Date().toLocaleTimeString('vi-VN', {hour: '2-digit', minute: '2-digit'});
            var avatar = isUser ? '👤' : '🤖';
            var cls = isUser ? 'user' : 'bot';

            // Format markdown đơn giản
            var formatted = this._formatText(text);

            var div = document.createElement('div');
            div.className = `chatbot-msg ${cls}`;
            div.innerHTML = `
                <div class="chatbot-msg-avatar">${avatar}</div>
                <div>
                    <div class="chatbot-msg-bubble">${formatted}</div>
                    <div class="chatbot-msg-time">${now}</div>
                </div>`;
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
            return div;
        },

        _formatText: function (text) {
            // Escape HTML
            text = text.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
            // **bold**
            text = text.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
            // newline
            text = text.replace(/\n/g, '<br>');
            return text;
        },

        _appendTyping: function () {
            var msgs = document.getElementById('chatbot-messages');
            var id = 'typing-' + Date.now();
            var div = document.createElement('div');
            div.className = 'chatbot-msg bot chatbot-typing';
            div.id = id;
            div.innerHTML = `
                <div class="chatbot-msg-avatar">🤖</div>
                <div class="chatbot-msg-bubble">
                    <div class="chatbot-typing-dots">
                        <span></span><span></span><span></span>
                    </div>
                </div>`;
            msgs.appendChild(div);
            msgs.scrollTop = msgs.scrollHeight;
            return id;
        },

        _removeTyping: function (id) {
            var el = document.getElementById(id);
            if (el) el.remove();
        },

        _setSuggestions: function (suggestions) {
            var container = document.getElementById('chatbot-suggestions');
            if (!suggestions || !suggestions.length) {
                container.innerHTML = '';
                return;
            }
            var html = suggestions.map(function (s) {
                return `<button class="chatbot-suggestion-btn" data-msg="${s}">${s}</button>`;
            }).join('');
            container.innerHTML = html;
        },
    });

    // Mount widget khi DOM ready
    core.action_registry.add('quan_ly_chatbot.chatbot_widget', ChatbotWidget);

    // Auto-mount vào body sau khi Odoo load xong
    $(document).ready(function () {
        setTimeout(function () {
            var widget = new ChatbotWidget(null);
            widget.appendTo($('body'));
        }, 2000);
    });

    return ChatbotWidget;
});
