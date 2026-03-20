/**
 * Dashboard Charts - doughnut + bar
 * Odoo 15 legacy JS
 */
odoo.define('quan_ly_cong_viec.dashboard_pie', function (require) {
    'use strict';

    var rpc = require('web.rpc');
    var ajax = require('web.ajax');

    // ── Vẽ doughnut chart ────────────────────────────────────────────────────
    function drawPieChart(pieData) {
        var canvas = document.getElementById('myPieChart');
        if (!canvas) return;

        if (window._dashPie) { window._dashPie.destroy(); window._dashPie = null; }

        var hasData = pieData && pieData.data && pieData.data.some(function(v) { return v > 0; });
        if (!hasData) {
            var ctx2 = canvas.getContext('2d');
            ctx2.clearRect(0, 0, canvas.width, canvas.height);
            ctx2.font = '13px Arial';
            ctx2.fillStyle = '#94a3b8';
            ctx2.textAlign = 'center';
            ctx2.fillText('Chưa có dữ liệu', canvas.width / 2, canvas.height / 2);
            return;
        }

        window._dashPie = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: pieData.labels,
                datasets: [{
                    data: pieData.data,
                    backgroundColor: pieData.colors,
                    borderWidth: 3,
                    borderColor: '#fff',
                    hoverOffset: 8,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: { font: { size: 11 }, padding: 10, usePointStyle: true }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(ctx) {
                                var total = ctx.dataset.data.reduce(function(a, b) { return a + b; }, 0);
                                var pct = total > 0 ? Math.round(ctx.parsed / total * 100) : 0;
                                return ' ' + ctx.label + ': ' + ctx.parsed + ' (' + pct + '%)';
                            }
                        }
                    }
                }
            }
        });
    }

    // ── Vẽ bar chart tiến độ dự án ───────────────────────────────────────────
    function drawBarChart(result) {
        var canvas = document.getElementById('monthlyAdmissionChart');
        if (!canvas) return;

        if (window._dashBar) { window._dashBar.destroy(); window._dashBar = null; }

        if (!result || !result.labels || result.labels.length === 0) return;

        window._dashBar = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: result.labels,
                datasets: [{
                    label: 'Tiến độ (%)',
                    data: result.progress,
                    backgroundColor: result.colors,
                    borderRadius: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100,
                        ticks: { callback: function(v) { return v + '%'; } }
                    }
                },
                plugins: { legend: { display: false } }
            }
        });
    }

    // ── Load dữ liệu qua RPC ─────────────────────────────────────────────────
    function loadDashboardCharts() {
        // Chỉ chạy khi đang ở trang dashboard
        if (!document.getElementById('myPieChart') && !document.getElementById('monthlyAdmissionChart')) {
            return;
        }

        // 1. Lấy dashboard record id, rồi đọc pie_chart_data
        rpc.query({
            model: 'dashboard',
            method: 'get_dashboard_data',
            args: [],
        }).then(function(dashId) {
            if (!dashId) return;
            return rpc.query({
                model: 'dashboard',
                method: 'read',
                args: [[dashId], ['pie_chart_data']],
            });
        }).then(function(records) {
            if (!records || !records.length) return;
            var raw = records[0].pie_chart_data;
            if (raw && raw !== 'false' && raw !== '{}') {
                try { drawPieChart(JSON.parse(raw)); } catch(e) { console.warn('pie parse:', e); }
            }
        }).catch(function(e) { console.warn('pie rpc error:', e); });

        // 2. Bar chart
        rpc.query({
            model: 'dashboard',
            method: 'get_project_progress_stats',
            args: [],
        }).then(function(result) {
            drawBarChart(result);
        }).catch(function(e) { console.warn('bar rpc error:', e); });
    }

    // ── Trigger ──────────────────────────────────────────────────────────────
    function tryDraw() {
        if (typeof Chart === 'undefined') {
            setTimeout(tryDraw, 500);
            return;
        }
        loadDashboardCharts();
    }

    $(document).ready(function() {
        setTimeout(tryDraw, 1000);
        setTimeout(tryDraw, 2500);
    });

    // Hook navigation
    $(document).on('click', '.o_menu_sections a, .o_nav_entry, .o_app, .o_menu_brand', function() {
        setTimeout(tryDraw, 1200);
    });

    return { loadDashboardCharts: loadDashboardCharts };
});
