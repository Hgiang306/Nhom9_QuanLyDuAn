odoo.define('quan_ly_cong_viec.gantt_chart', function (require) {
    'use strict';

    const { Component } = owl;
    const { onMounted, useRef, useState } = owl.hooks;
    const registry = require('@web/core/registry').registry;

    class GanttChartView extends Component {
        setup() {
            this.rpc = this.env.services.rpc;
            this.canvasRef = useRef('ganttCanvas');
            this.state = useState({ loading: true, error: null });
            onMounted(() => this._loadAndRender());
        }

        async _loadAndRender() {
            try {
                const tasks = await this.rpc('/web/dataset/call_kw', {
                    model: 'cong_viec',
                    method: 'get_gantt_data',
                    args: [],
                    kwargs: {},
                });
                this.state.loading = false;
                this._renderGantt(tasks);
            } catch (e) {
                this.state.loading = false;
                this.state.error = 'Không thể tải dữ liệu Gantt.';
            }
        }

        _renderGantt(tasks) {
            const canvas = this.canvasRef.el;
            if (!canvas) return;

            if (!tasks || tasks.length === 0) {
                const ctx = canvas.getContext('2d');
                canvas.width = canvas.parentElement.offsetWidth || 800;
                canvas.height = 120;
                ctx.fillStyle = '#f8f9fb';
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.fillStyle = '#94a3b8';
                ctx.font = '14px Arial';
                ctx.textAlign = 'center';
                ctx.fillText('Không có công việc nào có ngày bắt đầu và hạn chót.', canvas.width / 2, 60);
                return;
            }

            const dates = [];
            tasks.forEach(t => { dates.push(new Date(t.start)); dates.push(new Date(t.end)); });
            const minDate = new Date(Math.min(...dates)); minDate.setDate(minDate.getDate() - 1);
            const maxDate = new Date(Math.max(...dates)); maxDate.setDate(maxDate.getDate() + 2);
            const totalDays = Math.ceil((maxDate - minDate) / 86400000);

            const labelW = 210, rowH = 46, headerH = 52;
            const containerW = canvas.parentElement.offsetWidth || 900;
            const dayW = Math.max(26, Math.floor((containerW - labelW) / totalDays));
            const canvasW = labelW + totalDays * dayW;
            const canvasH = headerH + tasks.length * rowH + 20;

            canvas.width = canvasW; canvas.height = canvasH;
            const ctx = canvas.getContext('2d');

            ctx.fillStyle = '#f8f9fb'; ctx.fillRect(0, 0, canvasW, canvasH);
            ctx.fillStyle = '#1e293b'; ctx.fillRect(0, 0, canvasW, headerH);
            ctx.fillStyle = '#94a3b8'; ctx.font = 'bold 12px Arial';
            ctx.textAlign = 'left'; ctx.fillText('Công việc', 10, headerH / 2 + 5);

            for (let d = 0; d < totalDays; d++) {
                const day = new Date(minDate); day.setDate(day.getDate() + d);
                const x = labelW + d * dayW;
                const isWeekend = day.getDay() === 0 || day.getDay() === 6;
                if (isWeekend) { ctx.fillStyle = 'rgba(255,255,255,0.05)'; ctx.fillRect(x, 0, dayW, canvasH); }
                ctx.fillStyle = isWeekend ? '#64748b' : '#e2e8f0';
                ctx.font = 'bold 11px Arial'; ctx.textAlign = 'center';
                ctx.fillText(day.getDate(), x + dayW / 2, 22);
                if (day.getDate() === 1 || d === 0) {
                    ctx.fillStyle = '#fbbf24'; ctx.font = 'bold 10px Arial';
                    ctx.fillText(day.toLocaleString('vi-VN', { month: 'short', year: 'numeric' }), x + dayW / 2, 42);
                }
                ctx.strokeStyle = 'rgba(255,255,255,0.08)';
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, canvasH); ctx.stroke();
            }

            const colorMap = {
                cho_xac_nhan: '#94a3b8', dang_thuc_hien: '#3b82f6',
                cho_phe_duyet: '#f59e0b', hoan_thanh: '#22c55e',
                tu_choi: '#ef4444', tri_hoan: '#a855f7',
            };

            tasks.forEach((task, i) => {
                const y = headerH + i * rowH;
                const startD = Math.max(0, Math.ceil((new Date(task.start) - minDate) / 86400000));
                const endD = Math.ceil((new Date(task.end) - minDate) / 86400000);
                const barW = Math.max((endD - startD) * dayW, dayW * 0.8);
                const barX = labelW + startD * dayW, barY = y + 10, barH = rowH - 20;

                ctx.fillStyle = i % 2 === 0 ? '#ffffff' : '#f1f5f9';
                ctx.fillRect(0, y, canvasW, rowH);
                ctx.strokeStyle = '#e2e8f0';
                ctx.beginPath(); ctx.moveTo(0, y + rowH); ctx.lineTo(canvasW, y + rowH); ctx.stroke();

                ctx.fillStyle = '#334155'; ctx.font = '12px Arial'; ctx.textAlign = 'left';
                const label = task.name.length > 25 ? task.name.substring(0, 25) + '…' : task.name;
                ctx.fillText(label, 8, y + rowH / 2 + 4);
                if (task.du_an) { ctx.fillStyle = '#94a3b8'; ctx.font = '10px Arial'; ctx.fillText(task.du_an, 8, y + rowH / 2 + 16); }

                const color = colorMap[task.status] || '#3b82f6';
                ctx.shadowColor = 'rgba(0,0,0,0.12)'; ctx.shadowBlur = 4; ctx.shadowOffsetY = 2;
                ctx.fillStyle = color + '33';
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(barX + 2, barY, barW - 4, barH, 5);
                else ctx.rect(barX + 2, barY, barW - 4, barH);
                ctx.fill();

                ctx.shadowBlur = 0; ctx.shadowOffsetY = 0;
                const progressW = Math.max((barW - 4) * (task.progress / 100), 4);
                ctx.fillStyle = color;
                ctx.beginPath();
                if (ctx.roundRect) ctx.roundRect(barX + 2, barY, progressW, barH, 5);
                else ctx.rect(barX + 2, barY, progressW, barH);
                ctx.fill();

                if (barW > 40) {
                    ctx.fillStyle = '#fff'; ctx.font = 'bold 10px Arial'; ctx.textAlign = 'center';
                    ctx.fillText(task.progress + '%', barX + barW / 2, barY + barH / 2 + 4);
                }
            });

            const today = new Date();
            const todayD = Math.ceil((today - minDate) / 86400000);
            if (todayD >= 0 && todayD <= totalDays) {
                ctx.strokeStyle = '#ef4444'; ctx.lineWidth = 2; ctx.setLineDash([6, 3]);
                ctx.beginPath();
                ctx.moveTo(labelW + todayD * dayW, headerH);
                ctx.lineTo(labelW + todayD * dayW, canvasH);
                ctx.stroke();
                ctx.setLineDash([]); ctx.lineWidth = 1;
                ctx.fillStyle = '#ef4444'; ctx.font = 'bold 10px Arial'; ctx.textAlign = 'center';
                ctx.fillText('Hôm nay', labelW + todayD * dayW, headerH - 4);
            }
        }
    }

    GanttChartView.template = 'quan_ly_cong_viec.GanttChartTemplate';
    GanttChartView.props = ['*'];

    registry.category('actions').add('gantt_cong_viec', GanttChartView);
});
