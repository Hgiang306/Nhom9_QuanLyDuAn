odoo.define('dashboard.modern_charts', function (require) {
    "use strict";

    var rpc = require('web.rpc');

    $(document).ready(function () {
        // Load all charts
        loadMonthlyChart();
        loadStatusPieChart();
        loadRecentProjectsTable();
    });

    function loadMonthlyChart() {
        // Sample data for monthly progress
        var monthlyData = [0, 0, 0, 0, 0, 0, 0, 0, 0, 8, 0, 0];
        var months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];

        var ctx = document.getElementById('monthly_chart');
        if (ctx) {
            var chartContext = ctx.getContext('2d');
            new Chart(chartContext, {
                type: 'line',
                data: {
                    labels: months,
                    datasets: [{
                        label: 'Số lượng dự án',
                        data: monthlyData,
                        borderColor: '#2196f3',
                        backgroundColor: 'rgba(33, 150, 243, 0.1)',
                        borderWidth: 2,
                        fill: true,
                        tension: 0.4,
                        pointBackgroundColor: '#2196f3',
                        pointBorderColor: '#fff',
                        pointBorderWidth: 2,
                        pointRadius: 5
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            display: false
                        }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 10,
                            grid: {
                                color: '#f0f0f0'
                            },
                            ticks: {
                                color: '#666'
                            }
                        },
                        x: {
                            grid: {
                                color: '#f0f0f0'
                            },
                            ticks: {
                                color: '#666'
                            }
                        }
                    }
                }
            });
        }
    }

    function loadStatusPieChart() {
        rpc.query({
            model: 'dashboard',
            method: 'search_read',
            fields: ['du_an_dang_thuc_hien', 'du_an_hoan_thanh', 'du_an_chua_bat_dau', 'du_an_tam_dung'],
            limit: 1
        }).then(function (result) {
            var data = result && result.length > 0 ? result[0] : {
                du_an_dang_thuc_hien: 0,
                du_an_hoan_thanh: 0,
                du_an_chua_bat_dau: 0,
                du_an_tam_dung: 0
            };

            var ctx = document.getElementById('status_pie_chart');
            if (ctx) {
                var chartContext = ctx.getContext('2d');
                new Chart(chartContext, {
                    type: 'pie',
                    data: {
                        labels: ['Đang Thực Hiện', 'Hoàn Thành', 'Chưa Bắt Đầu'],
                        datasets: [{
                            data: [
                                data.du_an_dang_thuc_hien,
                                data.du_an_hoan_thanh,
                                data.du_an_chua_bat_dau
                            ],
                            backgroundColor: [
                                '#2196f3',
                                '#4caf50',
                                '#9e9e9e'
                            ],
                            borderWidth: 2,
                            borderColor: '#fff'
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: {
                                display: false
                            }
                        }
                    }
                });
            }
        }).catch(function (error) {
            console.error("Lỗi khi tải dữ liệu trạng thái:", error);
        });
    }

    function loadRecentProjectsTable() {
        rpc.query({
            model: 'du_an',
            method: 'search_read',
            fields: ['ten_du_an', 'nguoi_phu_trach_id', 'tien_do_du_an', 'phan_tram_du_an', 'ngay_bat_dau'],
            limit: 5,
            order: 'create_date desc'
        }).then(function (projects) {
            var tableContainer = document.getElementById('recent_projects_table');
            if (!tableContainer) return;

            if (!projects || projects.length === 0) {
                tableContainer.innerHTML = '<p style="padding: 20px; text-align: center; color: #666;">Không có dữ liệu dự án</p>';
                return;
            }

            var tableHTML = `
                <table class="project-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            <th>Ngày Tạo</th>
                            <th>Mã Dự Án</th>
                            <th>Tên Dự Án</th>
                            <th>Trạng Thái</th>
                            <th>Tiến Độ</th>
                        </tr>
                    </thead>
                    <tbody>
            `;

            projects.forEach(function(project, index) {
                var statusText = getStatusText(project.tien_do_du_an);
                var progressPercent = project.phan_tram_du_an || 0;
                var projectCode = 'DA' + String(project.id).padStart(4, '0');
                var createDate = project.ngay_bat_dau ? formatDate(new Date(project.ngay_bat_dau)) : 'N/A';

                tableHTML += `
                    <tr>
                        <td>${index + 1}</td>
                        <td>${createDate}</td>
                        <td>${projectCode}</td>
                        <td>${project.ten_du_an}</td>
                        <td>${statusText}</td>
                        <td>${progressPercent.toFixed(1)}%</td>
                    </tr>
                `;
            });

            tableHTML += `
                    </tbody>
                </table>
            `;

            tableContainer.innerHTML = tableHTML;
        }).catch(function (error) {
            console.error("Lỗi khi tải dữ liệu dự án gần đây:", error);
        });
    }

    function getStatusText(status) {
        var statusMap = {
            'chua_bat_dau': 'Chưa Bắt Đầu',
            'dang_thuc_hien': 'Đang Thực Hiện',
            'hoan_thanh': 'Hoàn Thành',
            'tam_dung': 'Tạm Dừng'
        };
        return statusMap[status] || 'Không xác định';
    }

    function formatDate(date) {
        return date.toLocaleDateString('vi-VN');
    }
});