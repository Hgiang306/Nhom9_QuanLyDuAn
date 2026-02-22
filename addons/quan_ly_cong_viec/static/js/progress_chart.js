odoo.define('quan_ly_cong_viec.sync_project_charts', function (require) {
    "use strict";
    var rpc = require('web.rpc');

    $(document).ready(function () {
        function renderProgressChart() {
            var ctx = document.getElementById('monthlyAdmissionChart');
            if (!ctx) return;

            rpc.query({
                model: 'dashboard',
                method: 'get_project_progress_stats',
            }).then(function (result) {
                new Chart(ctx, {
                    type: 'bar', // Biểu đồ cột
                    data: {
                        labels: result.labels,
                        datasets: [{
                            label: 'Tiến độ dự án (%)',
                            data: result.progress,
                            backgroundColor: result.colors,
                            borderWidth: 1
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        scales: {
                            yAxes: [{
                                ticks: { beginAtZero: true, max: 100 }
                            }]
                        }
                    }
                });
            });
        }

        // Gọi hàm vẽ sau khi trang load xong
        setTimeout(renderProgressChart, 500);
    });
});