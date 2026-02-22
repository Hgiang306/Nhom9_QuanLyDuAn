odoo.define('quan_ly_cong_viec.bieu_do_cong_viec', function (require) {
    'use strict';

    const FormRenderer = require('web.FormRenderer');

    function resolveChartType(loai) {
        switch (loai) {
            case 'tien_do': return 'bar';
            case 'ngan_sach': return 'doughnut';
            case 'nhan_luc': return 'bar';
            case 'thoi_gian': return 'bar';
            default: return 'bar';
        }
    }

    function buildOptions(state) {
        const showLegend = state.data.hien_thi_chu_thich;
        const showValue = state.data.hien_thi_gia_tri;
        return {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: !!showLegend },
                tooltip: { enabled: true },
                datalabels: showValue ? {
                    color: '#333',
                    anchor: 'end',
                    align: 'top',
                    formatter: function(v) { return (v || v === 0) ? v : ''; },
                } : undefined,
            },
            scales: {
                x: { ticks: { autoSkip: true, maxRotation: 0 } },
                y: { beginAtZero: true }
            }
        };
    }

    const RendererPatch = FormRenderer.prototype._updateView;
    FormRenderer.prototype._updateView = function () {
        const res = RendererPatch.apply(this, arguments);
        setTimeout(() => {
            this._renderProjectChart && this._renderProjectChart();
        }, 0);
        return res;
    };
    FormRenderer.prototype._renderProjectChart = function () {
        try {
            if (!this.state || this.state.model !== 'bieu_do_cong_viec') return;

            const canvas = this.el.querySelector('#myChartDA');
            if (!canvas) return;

            let chartData;
            try {
                chartData = JSON.parse(this.state.data.du_lieu_bieu_do || '{}');
            } catch (e) {
                return;
            }

            if (!chartData || !chartData.labels || !chartData.datasets) return;

            const ctx = canvas.getContext('2d');

            if (this._projectChart && this._projectChart.destroy) {
                this._projectChart.destroy();
            }

            const type = resolveChartType(this.state.data.loai_bieu_do);
            const options = buildOptions(this.state);

            this._projectChart = new Chart(ctx, {
                type: type,
                data: chartData,
                options: options,
            });

        } catch (e) {
            console.error('Chart render error:', e);
        }
    };
});