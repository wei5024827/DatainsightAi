const API_BASE = 'http://localhost:8000';

let currentData = [];
let currentPage = 1;
const pageSize = 10;

const byId = (id) => document.getElementById(id);

function updateStatus(message, type = 'info') {
    const statusEl = byId('status');
    const statusColor = {
        error: '#dc3545',
        success: '#28a745',
        info: '#6c757d',
    };
    statusEl.textContent = message;
    statusEl.style.color = statusColor[type] || statusColor.info;
}

function setLoading(visible, message) {
    byId('loading').style.display = visible ? 'block' : 'none';
    if (message) {
        updateStatus(message);
    }
}

function fillExample(text) {
    byId('nl-input').value = text;
    updateStatus('已填充示例问题');
}

function clearInput() {
    byId('nl-input').value = '';
    updateStatus('输入已清空');
}

function clearSQL() {
    byId('sql-editor').value = '';
    updateStatus('SQL已清空');
}

function clearResults() {
    byId('sql-editor').value = '';
    byId('data-container').innerHTML = '';
    byId('pagination').style.display = 'none';
    updateStatus('结果已清空');
}

function copySQL() {
    const sql = byId('sql-editor').value.trim();
    if (!sql) {
        updateStatus('SQL为空，无法复制', 'error');
        return;
    }

    navigator.clipboard
        .writeText(sql)
        .then(() => updateStatus('SQL已复制到剪贴板', 'success'))
        .catch((err) => updateStatus(`复制失败: ${err}`, 'error'));
}

async function sendNL2SQL() {
    const input = byId('nl-input').value.trim();
    if (!input) {
        updateStatus('请输入问题内容', 'error');
        return;
    }

    setLoading(true, '正在生成SQL...');

    try {
        const response = await fetch(`${API_BASE}/nl2sql`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ text: input }),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || '请求失败');
        }

        byId('sql-editor').value = data.sql;
        updateStatus('SQL生成成功', 'success');
    } catch (error) {
        updateStatus(`生成失败: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

async function executeSQL() {
    const sql = byId('sql-editor').value.trim();
    if (!sql) {
        updateStatus('请输入SQL语句', 'error');
        return;
    }

    setLoading(true, '正在执行SQL...');

    try {
        const response = await fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ sql }),
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || 'SQL执行失败');
        }

        currentData = Array.isArray(data) ? data : [];
        currentPage = 1;
        displayData();
        updateStatus('SQL执行成功', 'success');
    } catch (error) {
        byId('data-container').innerHTML = `
            <div class="error">
                <strong>✗ SQL执行错误:</strong> ${error.message}
            </div>
        `;
        byId('pagination').style.display = 'none';
        updateStatus(`执行失败: ${error.message}`, 'error');
    } finally {
        setLoading(false);
    }
}

function displayData() {
    const container = byId('data-container');
    const pagination = byId('pagination');

    if (!currentData.length) {
        container.innerHTML = '<p style="color: #6c757d; text-align: center;">查询结果为空</p>';
        pagination.style.display = 'none';
        return;
    }

    const totalPages = Math.ceil(currentData.length / pageSize);
    const startIndex = (currentPage - 1) * pageSize;
    const pageData = currentData.slice(startIndex, startIndex + pageSize);
    const headers = Object.keys(pageData[0] || {});

    let tableHTML = `
        <div style="margin-bottom: 15px;">
            <strong>查询结果:</strong> 共 ${currentData.length} 条记录
        </div>
        <table class="data-table">
            <thead>
                <tr>${headers.map((header) => `<th>${header}</th>`).join('')}</tr>
            </thead>
            <tbody>
    `;

    pageData.forEach((row) => {
        tableHTML += '<tr>';
        headers.forEach((header) => {
            tableHTML += `<td>${row[header] ?? ''}</td>`;
        });
        tableHTML += '</tr>';
    });

    tableHTML += '</tbody></table>';
    container.innerHTML = tableHTML;

    byId('page-info').textContent = `第 ${currentPage} 页，共 ${totalPages} 页`;
    pagination.style.display = totalPages > 1 ? 'flex' : 'none';
}

function changePage(direction) {
    const totalPages = Math.ceil(currentData.length / pageSize);
    const nextPage = currentPage + direction;

    if (nextPage >= 1 && nextPage <= totalPages) {
        currentPage = nextPage;
        displayData();
    }
}

function initEventListeners() {
    byId('nl-input').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            sendNL2SQL();
        }
    });

    byId('sql-editor').addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
            executeSQL();
            e.preventDefault();
        }
    });

    window.addEventListener('load', () => {
        updateStatus('就绪，可以开始使用');
        byId('data-container').innerHTML = '';
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initEventListeners();
});
