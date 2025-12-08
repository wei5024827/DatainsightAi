// 后端API地址
const API_BASE = 'http://localhost:8000';

// 全局变量
let currentData = [];
let currentPage = 1;
const pageSize = 10;

// 更新状态信息
function updateStatus(message, type = 'info') {
    const statusEl = document.getElementById('status');
    statusEl.textContent = message;
    statusEl.style.color = type === 'error' ? '#dc3545' : type === 'success' ? '#28a745' : '#6c757d';
}

// 移除标签页切换函数，因为现在是平铺显示

// 填充示例问题
function fillExample(text) {
    document.getElementById('nl-input').value = text;
    updateStatus('已填充示例问题');
}

// 清空输入
function clearInput() {
    document.getElementById('nl-input').value = '';
    updateStatus('输入已清空');
}

// 清空SQL编辑器
function clearSQL() {
    document.getElementById('sql-editor').value = '';
    updateStatus('SQL已清空');
}

// 清空结果
function clearResults() {
    document.getElementById('sql-editor').value = '';
    document.getElementById('data-container').innerHTML = ''; // 移除数据展示内容
    document.getElementById('pagination').style.display = 'none';
    updateStatus('结果已清空');
}

// 复制SQL到剪贴板
function copySQL() {
    const sql = document.getElementById('sql-editor').value;
    if (!sql.trim()) {
        updateStatus('SQL为空，无法复制', 'error');
        return;
    }
    navigator.clipboard.writeText(sql).then(() => {
        updateStatus('SQL已复制到剪贴板', 'success');
    }).catch(err => {
        updateStatus('复制失败: ' + err, 'error');
    });
}

// 发送自然语言转SQL请求
async function sendNL2SQL() {
    const input = document.getElementById('nl-input').value.trim();
    const loading = document.getElementById('loading');

    if (!input) {
        updateStatus('请输入问题内容', 'error');
        return;
    }

    // 显示加载状态
    loading.style.display = 'block';
    updateStatus('正在生成SQL...');

    try {
        const response = await fetch(`${API_BASE}/nl2sql`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: input })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || '请求失败');
        }

        // 将生成的SQL显示在编辑器中
        document.getElementById('sql-editor').value = data.sql;
        updateStatus('SQL生成成功', 'success');

    } catch (error) {
        updateStatus('生成失败: ' + error.message, 'error');
    } finally {
        loading.style.display = 'none';
    }
}

// 执行SQL查询
async function executeSQL() {
    const sql = document.getElementById('sql-editor').value.trim();
    const loading = document.getElementById('loading');

    console.log('执行SQL:', sql);

    if (!sql) {
        updateStatus('请输入SQL语句', 'error');
        return;
    }

    // 显示加载状态
    loading.style.display = 'block';
    updateStatus('正在执行SQL...');
    console.log('正在执行SQL');

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ sql: sql })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'SQL执行失败');
        }

        // 保存数据并显示
        currentData = Array.isArray(data) ? data : [];
        currentPage = 1;
        displayData();
        updateStatus('SQL执行成功', 'success');

        // 移除切换到数据标签页的代码，因为现在是平铺显示

    } catch (error) {
        document.getElementById('data-container').innerHTML = `
            <div class="error">
                <strong>✗ SQL执行错误:</strong> ${error.message}
            </div>
        `;
        document.getElementById('pagination').style.display = 'none';
        updateStatus('执行失败: ' + error.message, 'error');
    } finally {
        loading.style.display = 'none';
    }
}

// 显示数据表格
function displayData() {
    const container = document.getElementById('data-container');
    const pagination = document.getElementById('pagination');

    if (currentData.length === 0) {
        container.innerHTML = '<p style="color: #6c757d; text-align: center;">查询结果为空</p>';
        pagination.style.display = 'none';
        return;
    }

    // 计算分页
    const totalPages = Math.ceil(currentData.length / pageSize);
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = Math.min(startIndex + pageSize, currentData.length);
    const pageData = currentData.slice(startIndex, endIndex);

    // 获取表头
    const headers = Object.keys(pageData[0] || {});

    // 生成表格HTML
    let tableHTML = `
        <div style="margin-bottom: 15px;">
            <strong>查询结果:</strong> 共 ${currentData.length} 条记录
        </div>
        <table class="data-table">
            <thead>
                <tr>
                    ${headers.map(header => `<th>${header}</th>`).join('')}
                </tr>
            </thead>
            <tbody>
    `;

    // 添加数据行（斑马纹样式）
    pageData.forEach((row, index) => {
        tableHTML += `<tr>`;
        headers.forEach(header => {
            tableHTML += `<td>${row[header] || ''}</td>`;
        });
        tableHTML += `</tr>`;
    });

    tableHTML += `</tbody></table>`;

    container.innerHTML = tableHTML;

    // 更新分页信息
    document.getElementById('page-info').textContent = `第 ${currentPage} 页，共 ${totalPages} 页`;
    pagination.style.display = totalPages > 1 ? 'flex' : 'none';
}

// 切换页面
function changePage(direction) {
    const totalPages = Math.ceil(currentData.length / pageSize);
    const newPage = currentPage + direction;
    
    if (newPage >= 1 && newPage <= totalPages) {
        currentPage = newPage;
        displayData();
    }
}

// 初始化事件监听器
function initEventListeners() {
    // 回车键发送（Ctrl+Enter）
    document.getElementById('nl-input').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            sendNL2SQL();
        }
    });

    // SQL编辑器快捷键（Ctrl+Enter执行）
    document.getElementById('sql-editor').addEventListener('keypress', function(e) {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            executeSQL();
            e.preventDefault();
        }
    });

    // 页面加载完成后的初始化
    window.addEventListener('load', function() {
        updateStatus('就绪，可以开始使用');
        // 初始化时清空数据展示区域
        document.getElementById('data-container').innerHTML = '';
    });
}

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initEventListeners();
});