/**
 * AI 文档检测服务 - 前端交互逻辑
 */

const API_BASE = '/api/v1';

// 状态
let currentDocumentId = null;
let currentTaskId = null;
let pollInterval = null;

// DOM 元素
const elements = {
    uploadArea: document.getElementById('uploadArea'),
    fileInput: document.getElementById('fileInput'),
    fileInfo: document.getElementById('fileInfo'),
    fileName: document.getElementById('fileName'),
    fileSize: document.getElementById('fileSize'),
    removeFile: document.getElementById('removeFile'),
    startCheck: document.getElementById('startCheck'),
    customRules: document.getElementById('customRules'),
    progressSection: document.getElementById('progressSection'),
    progressFill: document.getElementById('progressFill'),
    progressText: document.getElementById('progressText'),
    progressStatus: document.getElementById('progressStatus'),
    resultSection: document.getElementById('resultSection'),
    scoreCircle: document.getElementById('scoreCircle'),
    scoreValue: document.getElementById('scoreValue'),
    errorCount: document.getElementById('errorCount'),
    warningCount: document.getElementById('warningCount'),
    infoCount: document.getElementById('infoCount'),
    resultSummary: document.getElementById('resultSummary'),
    resultDetails: document.getElementById('resultDetails'),
    viewHtmlReport: document.getElementById('viewHtmlReport'),
    downloadHtml: document.getElementById('downloadHtml'),
    downloadMd: document.getElementById('downloadMd'),
    newCheck: document.getElementById('newCheck'),
    toast: document.getElementById('toast')
};

// ============ 工具函数 ============

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function showToast(message, type = 'info') {
    elements.toast.textContent = message;
    elements.toast.className = 'toast show ' + type;
    setTimeout(() => {
        elements.toast.className = 'toast';
    }, 3000);
}

function getScoreClass(score) {
    if (score >= 90) return 'excellent';
    if (score >= 75) return 'good';
    if (score >= 60) return 'warning';
    return 'danger';
}

function getDimensionName(dimension) {
    const names = {
        'format': '📐 格式规范',
        'content': '📝 内容质量',
        'logic': '🔗 逻辑一致性',
        'sensitive': '🔒 敏感信息',
        'compliance': '✅ 合规检查'
    };
    return names[dimension] || dimension;
}

// ============ API 调用 ============

async function uploadDocument(file) {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE}/documents/upload`, {
        method: 'POST',
        body: formData
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '上传失败');
    }

    return response.json();
}

async function startCheckTask(documentId, dimensions, aiProvider, customRules) {
    const response = await fetch(`${API_BASE}/check/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            document_id: documentId,
            dimensions: dimensions,
            ai_provider: aiProvider,
            custom_rules: customRules || null
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '启动检测失败');
    }

    return response.json();
}

async function getTaskStatus(taskId) {
    const response = await fetch(`${API_BASE}/check/${taskId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '获取状态失败');
    }

    return response.json();
}

async function getReport(taskId) {
    const response = await fetch(`${API_BASE}/reports/${taskId}`);

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '获取报告失败');
    }

    return response.json();
}

// ============ 文件上传处理 ============

function handleFileSelect(file) {
    if (!file) return;

    // 验证文件类型
    const validExtensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.md'];
    const ext = '.' + file.name.split('.').pop().toLowerCase();

    if (!validExtensions.includes(ext)) {
        showToast('不支持的文件格式', 'error');
        return;
    }

    // 显示文件信息
    elements.fileName.textContent = file.name;
    elements.fileSize.textContent = formatFileSize(file.size);
    elements.fileInfo.style.display = 'flex';
    elements.uploadArea.style.display = 'none';

    // 上传文件
    uploadFile(file);
}

async function uploadFile(file) {
    try {
        elements.startCheck.disabled = true;
        elements.startCheck.innerHTML = '<span class="btn-icon">⏳</span> 上传中...';

        const result = await uploadDocument(file);
        currentDocumentId = result.id;

        elements.startCheck.disabled = false;
        elements.startCheck.innerHTML = '<span class="btn-icon">🚀</span> 开始检测';

        showToast('文档上传成功', 'success');
    } catch (error) {
        showToast(error.message, 'error');
        resetUpload();
    }
}

function resetUpload() {
    currentDocumentId = null;
    elements.fileInput.value = '';
    elements.fileInfo.style.display = 'none';
    elements.uploadArea.style.display = 'block';
    elements.startCheck.disabled = true;
    elements.startCheck.innerHTML = '<span class="btn-icon">🚀</span> 开始检测';
}

// ============ 检测流程 ============

async function startCheck() {
    if (!currentDocumentId) {
        showToast('请先上传文档', 'error');
        return;
    }

    // 获取配置
    const aiProvider = document.querySelector('input[name="aiProvider"]:checked').value;
    const customRules = elements.customRules.value.trim();

    // 获取检测模式
    const checkMode = document.querySelector('input[name="checkMode"]:checked')?.value || 'smart';

    let dimensions;
    if (checkMode === 'smart') {
        // 智能模式：使用所有维度
        dimensions = ['format', 'content', 'logic', 'sensitive', 'compliance'];
    } else {
        // 自定义模式：使用用户选择的维度
        dimensions = Array.from(document.querySelectorAll('input[name="dimensions"]:checked'))
            .map(el => el.value);

        if (dimensions.length === 0) {
            showToast('请至少选择一个检测维度', 'error');
            return;
        }
    }

    try {
        // 显示进度区域
        elements.progressSection.style.display = 'block';
        elements.resultSection.style.display = 'none';
        elements.startCheck.disabled = true;

        updateProgress(0, '正在启动检测任务...');

        // 启动检测
        const result = await startCheckTask(currentDocumentId, dimensions, aiProvider, customRules);
        currentTaskId = result.task_id;

        // 开始轮询状态
        startPolling();

    } catch (error) {
        showToast(error.message, 'error');
        elements.progressSection.style.display = 'none';
        elements.startCheck.disabled = false;
    }
}

function startPolling() {
    if (pollInterval) clearInterval(pollInterval);

    pollInterval = setInterval(async () => {
        try {
            const task = await getTaskStatus(currentTaskId);

            updateProgress(task.progress, getStatusText(task.status, task.progress));

            if (task.status === 'completed') {
                stopPolling();
                showResults(task);
            } else if (task.status === 'failed') {
                stopPolling();
                showToast('检测失败: ' + (task.summary || '未知错误'), 'error');
                elements.progressSection.style.display = 'none';
                elements.startCheck.disabled = false;
            }
        } catch (error) {
            console.error('轮询错误:', error);
        }
    }, 1000);
}

function stopPolling() {
    if (pollInterval) {
        clearInterval(pollInterval);
        pollInterval = null;
    }
}

function getStatusText(status, progress) {
    switch (status) {
        case 'pending': return '等待处理...';
        case 'processing':
            if (progress < 30) return 'AI 正在分析文档结构...';
            if (progress < 60) return 'AI 正在进行多维度检测...';
            if (progress < 90) return 'AI 正在生成检测结果...';
            return '正在生成报告...';
        case 'completed': return '检测完成！';
        case 'failed': return '检测失败';
        default: return '处理中...';
    }
}

function updateProgress(percent, text) {
    elements.progressFill.style.width = percent + '%';
    elements.progressText.textContent = text;
    elements.progressStatus.textContent = `进度: ${percent}%`;
}

// ============ 结果展示 ============

function showResults(task) {
    elements.progressSection.style.display = 'none';
    elements.resultSection.style.display = 'block';

    // 显示分数
    const score = Math.round(task.overall_score || 0);
    elements.scoreValue.textContent = score;
    elements.scoreCircle.className = 'score-circle ' + getScoreClass(score);

    // 统计问题数量
    let errorCount = 0, warningCount = 0, infoCount = 0;

    if (task.results) {
        task.results.forEach(result => {
            if (result.issues) {
                result.issues.forEach(issue => {
                    if (issue.severity === 'error') errorCount++;
                    else if (issue.severity === 'warning') warningCount++;
                    else infoCount++;
                });
            }
        });
    }

    elements.errorCount.textContent = errorCount;
    elements.warningCount.textContent = warningCount;
    elements.infoCount.textContent = infoCount;

    // 显示总结
    elements.resultSummary.textContent = task.summary || '检测完成';

    // 显示详细结果
    renderDetailedResults(task.results);

    showToast('检测完成！', 'success');
}

function renderDetailedResults(results) {
    if (!results || results.length === 0) {
        elements.resultDetails.innerHTML = '<p>无详细结果</p>';
        return;
    }

    let html = '';

    results.forEach((result, index) => {
        const scoreClass = getScoreClass(result.score);
        const hasIssues = result.issues && result.issues.length > 0;

        html += `
            <div class="dimension-result">
                <div class="dimension-header" onclick="toggleDimension(${index})">
                    <h4>${getDimensionName(result.dimension)}</h4>
                    <span class="dimension-score ${scoreClass}">${Math.round(result.score)} 分</span>
                </div>
                <div class="dimension-body" id="dimension-${index}">
                    <p class="dimension-summary">${result.summary || ''}</p>
                    ${hasIssues ? renderIssues(result.issues) : '<p style="color: var(--success-color);">✅ 未发现问题</p>'}
                </div>
            </div>
        `;
    });

    elements.resultDetails.innerHTML = html;

    // 默认展开第一个
    const firstBody = document.getElementById('dimension-0');
    if (firstBody) firstBody.classList.add('show');
}

function renderIssues(issues) {
    let html = '<ul class="issue-list">';

    issues.forEach(issue => {
        html += `
            <li class="issue ${issue.severity}">
                <span class="issue-badge">${issue.severity}</span>
                <div class="issue-desc">${issue.description}</div>
                <div class="issue-meta">
                    ${issue.location ? `<span>📍 ${issue.location}</span>` : ''}
                    ${issue.suggestion ? `<span>💡 ${issue.suggestion}</span>` : ''}
                </div>
            </li>
        `;
    });

    html += '</ul>';
    return html;
}

// 切换维度展开/收起
window.toggleDimension = function(index) {
    const body = document.getElementById(`dimension-${index}`);
    if (body) {
        body.classList.toggle('show');
    }
};

// ============ 事件绑定 ============

// 上传区域点击
elements.uploadArea.addEventListener('click', () => {
    elements.fileInput.click();
});

// 文件选择
elements.fileInput.addEventListener('change', (e) => {
    handleFileSelect(e.target.files[0]);
});

// 拖拽上传
elements.uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.add('dragover');
});

elements.uploadArea.addEventListener('dragleave', () => {
    elements.uploadArea.classList.remove('dragover');
});

elements.uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    elements.uploadArea.classList.remove('dragover');
    handleFileSelect(e.dataTransfer.files[0]);
});

// 移除文件
elements.removeFile.addEventListener('click', resetUpload);


// 查看 HTML 报告
elements.viewHtmlReport.addEventListener('click', () => {
    if (currentTaskId) {
        window.open(`${API_BASE}/reports/${currentTaskId}/html`, '_blank');
    }
});

// 下载 HTML
elements.downloadHtml.addEventListener('click', () => {
    if (currentTaskId) {
        window.location.href = `${API_BASE}/reports/${currentTaskId}/download?format=html`;
    }
});

// 下载 Markdown
elements.downloadMd.addEventListener('click', () => {
    if (currentTaskId) {
        window.location.href = `${API_BASE}/reports/${currentTaskId}/download?format=md`;
    }
});

// 新建检测
elements.newCheck.addEventListener('click', () => {
    resetUpload();
    currentTaskId = null;
    elements.resultSection.style.display = 'none';
    elements.startCheck.disabled = true;
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// ============ 选项卡切换 ============
let currentTab = 'doc-check';

function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    if (tabBtns.length === 0) {
        console.log('未找到选项卡按钮');
        return;
    }

    tabBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();

            // 更新按钮状态
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            currentTab = btn.dataset.tab;
            console.log('切换到选项卡:', currentTab);

            // 更新配置区域显示
            updateConfigVisibility();

            // 更新开始按钮文字
            updateStartButton();

            // 隐藏所有结果区域
            elements.resultSection.style.display = 'none';
            const reqResult = document.getElementById('reqAnalysisResult');
            const tcResult = document.getElementById('testCaseResult');
            if (reqResult) reqResult.style.display = 'none';
            if (tcResult) tcResult.style.display = 'none';
        });
    });

    // 初始化检测模式切换
    initCheckModeToggle();
}

// 根据当前选项卡更新配置区域显示
function updateConfigVisibility() {
    // 文档检测配置
    const docCheckConfigs = document.querySelectorAll('.doc-check-config');
    // 需求分析配置
    const reqAnalysisConfig = document.getElementById('reqAnalysisConfig');
    // 测试用例配置
    const testcaseGenConfig = document.getElementById('testcaseGenConfig');

    // 隐藏所有
    docCheckConfigs.forEach(el => el.style.display = 'none');
    if (reqAnalysisConfig) reqAnalysisConfig.style.display = 'none';
    if (testcaseGenConfig) testcaseGenConfig.style.display = 'none';

    // 根据选项卡显示对应配置
    if (currentTab === 'doc-check') {
        docCheckConfigs.forEach(el => el.style.display = 'block');
    } else if (currentTab === 'req-analysis') {
        if (reqAnalysisConfig) reqAnalysisConfig.style.display = 'block';
    } else if (currentTab === 'testcase-gen') {
        if (testcaseGenConfig) testcaseGenConfig.style.display = 'block';
    }
}

// 初始化检测模式切换（智能检测 vs 自定义维度）
function initCheckModeToggle() {
    const checkModeRadios = document.querySelectorAll('input[name="checkMode"]');
    const customDimensions = document.getElementById('customDimensions');

    checkModeRadios.forEach(radio => {
        radio.addEventListener('change', () => {
            if (radio.value === 'custom' && radio.checked) {
                customDimensions.style.display = 'flex';
            } else {
                customDimensions.style.display = 'none';
            }
        });
    });
}

function updateStartButton() {
    if (!currentDocumentId) {
        elements.startCheck.disabled = true;
    }
    const btnTexts = {
        'doc-check': '<span class="btn-icon">🚀</span> 开始检测',
        'req-analysis': '<span class="btn-icon">📋</span> 开始分析需求',
        'testcase-gen': '<span class="btn-icon">🧪</span> 生成测试用例'
    };
    elements.startCheck.innerHTML = btnTexts[currentTab] || btnTexts['doc-check'];
}

// 开始按钮点击处理
function handleStartClick() {
    if (!currentDocumentId) {
        showToast('请先上传文档', 'error');
        return;
    }

    console.log('当前模式:', currentTab);

    if (currentTab === 'doc-check') {
        startCheck();
    } else if (currentTab === 'req-analysis') {
        startRequirementAnalysis();
    } else if (currentTab === 'testcase-gen') {
        startTestCaseGeneration();
    }
}

// 绑定开始按钮事件
elements.startCheck.addEventListener('click', handleStartClick);

// ============ 需求分析 ============
async function analyzeRequirements(documentId, aiProvider) {
    const response = await fetch(`${API_BASE}/requirements/analyze`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            document_id: documentId,
            ai_provider: aiProvider
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '需求分析失败');
    }

    return response.json();
}

async function startRequirementAnalysis() {
    const aiProvider = document.querySelector('input[name="aiProvider"]:checked').value;

    try {
        elements.progressSection.style.display = 'block';
        elements.resultSection.style.display = 'none';
        document.getElementById('reqAnalysisResult').style.display = 'none';
        document.getElementById('testCaseResult').style.display = 'none';
        elements.startCheck.disabled = true;

        updateProgress(30, 'AI 正在分析需求文档...');

        const result = await analyzeRequirements(currentDocumentId, aiProvider);

        updateProgress(100, '分析完成！');

        setTimeout(() => {
            elements.progressSection.style.display = 'none';
            showRequirementAnalysisResult(result);
        }, 500);

    } catch (error) {
        showToast('分析失败: ' + error.message, 'error');
        elements.progressSection.style.display = 'none';
    } finally {
        elements.startCheck.disabled = false;
    }
}

function showRequirementAnalysisResult(result) {
    const section = document.getElementById('reqAnalysisResult');
    section.style.display = 'block';

    // 更新评分
    document.getElementById('completenessScore').textContent = Math.round(result.completeness_score);
    document.getElementById('scenarioScore').textContent = Math.round(result.scenario_coverage_score);
    document.getElementById('descriptionScore').textContent = Math.round(result.description_quality_score);
    document.getElementById('testabilityScore').textContent = Math.round(result.testability_score);

    // 更新总结
    document.getElementById('reqSummary').textContent = result.summary;

    // 渲染需求列表
    const reqList = document.getElementById('reqList');
    reqList.innerHTML = result.analyzed_requirements.map((req, idx) => `
        <div class="req-item">
            <div class="req-item-header" onclick="toggleReqItem(${idx})">
                <h4>
                    <span class="req-id">${req.req_id}</span>
                    ${req.title}
                    ${req.issues.length > 0 ? `<span class="issue-badge">${req.issues.length} 个问题</span>` : '<span class="ok-badge">✓ 完整</span>'}
                </h4>
                <span class="req-priority ${(req.priority || '').toLowerCase().replace('高', 'high').replace('中', 'medium').replace('低', 'low')}">${req.priority || '未定义'}</span>
            </div>
            <div class="req-item-body ${idx === 0 ? 'show' : ''}" id="req-${idx}">
                <p class="req-desc">${req.description}</p>
                ${req.issues.length > 0 ? `
                    <div class="req-issues">
                        <h5>🔴 发现的问题 (${req.issues.length})</h5>
                        <ul>${req.issues.map(i => `<li>${formatIssue(i)}</li>`).join('')}</ul>
                    </div>
                ` : ''}
                ${req.suggestions.length > 0 ? `
                    <div class="req-suggestions">
                        <h5>💡 改进建议 (${req.suggestions.length})</h5>
                        <ul>${req.suggestions.map(s => `<li>${s}</li>`).join('')}</ul>
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');

    // 渲染改进建议
    const suggestions = document.getElementById('improvementSuggestions');
    if (result.improvement_suggestions.length > 0) {
        suggestions.innerHTML = `
            <h4>📌 整体改进建议</h4>
            <ul>${result.improvement_suggestions.map(s => `<li>${formatSuggestionPriority(s)}</li>`).join('')}</ul>
        `;
        suggestions.style.display = 'block';
    } else {
        suggestions.style.display = 'none';
    }

    showToast('需求分析完成！', 'success');
}

// 格式化问题文本，提取并高亮问题类型
function formatIssue(issue) {
    // 匹配 [问题类型] 格式
    const match = issue.match(/^\[([^\]]+)\]\s*(.*)$/);
    if (match) {
        const typeColors = {
            // 业务视角问题类型
            '业务流程断点': '#dc2626',
            '规则不明确': '#ea580c',
            '状态定义不清': '#d97706',
            '并发场景遗漏': '#0891b2',
            '逆向流程缺失': '#7c3aed',
            '运营能力缺失': '#2563eb',
            '通知机制缺失': '#0d9488',
            '异常处理缺失': '#be185d',
            '边界场景遗漏': '#4f46e5',
            // 兼容旧的技术视角类型
            '输入缺失': '#dc2626',
            '输出缺失': '#ea580c',
            '规则缺失': '#d97706',
            '异常未覆盖': '#0891b2',
            '模糊表述': '#7c3aed',
            '依赖缺失': '#2563eb',
            '安全要求缺失': '#be185d',
            '性能要求缺失': '#059669',
            '边界未定义': '#4f46e5'
        };
        const color = typeColors[match[1]] || '#6b7280';
        return `<span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:600;margin-right:6px;background:${color};color:white;">${match[1]}</span>${match[2]}`;
    }
    return issue;
}

// 格式化建议优先级
function formatSuggestionPriority(suggestion) {
    // 匹配 [优先级] 格式
    const match = suggestion.match(/^\[([^\]]+)\]\s*(.*)$/);
    if (match) {
        const priorityColors = {
            '高优先级': '#dc2626',
            '中优先级': '#d97706',
            '低优先级': '#059669',
            '建议': '#6b7280'
        };
        const color = priorityColors[match[1]] || '#6b7280';
        return `<span style="display:inline-block;padding:2px 6px;border-radius:4px;font-size:11px;font-weight:600;margin-right:6px;background:${color};color:white;">${match[1]}</span>${match[2]}`;
    }
    return suggestion;
}

window.toggleReqItem = function(idx) {
    const body = document.getElementById(`req-${idx}`);
    if (body) {
        body.classList.toggle('show');
    }
};

// ============ 测试用例生成 ============
async function generateTestCases(documentId, aiProvider) {
    const response = await fetch(`${API_BASE}/requirements/generate-testcases`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            document_id: documentId,
            ai_provider: aiProvider
        })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '测试用例生成失败');
    }

    return response.json();
}

async function startTestCaseGeneration() {
    const aiProvider = document.querySelector('input[name="aiProvider"]:checked').value;

    try {
        elements.progressSection.style.display = 'block';
        elements.resultSection.style.display = 'none';
        document.getElementById('reqAnalysisResult').style.display = 'none';
        document.getElementById('testCaseResult').style.display = 'none';
        elements.startCheck.disabled = true;

        updateProgress(30, 'AI 正在分析需求并生成测试用例...');

        const result = await generateTestCases(currentDocumentId, aiProvider);

        updateProgress(100, '生成完成！');

        setTimeout(() => {
            elements.progressSection.style.display = 'none';
            showTestCaseResult(result);
        }, 500);

    } catch (error) {
        showToast('生成失败: ' + error.message, 'error');
        elements.progressSection.style.display = 'none';
    } finally {
        elements.startCheck.disabled = false;
    }
}

function showTestCaseResult(result) {
    const section = document.getElementById('testCaseResult');
    section.style.display = 'block';

    // 统计各优先级数量
    const counts = { P0: 0, P1: 0, P2: 0, P3: 0 };
    result.test_cases.forEach(tc => {
        counts[tc.priority] = (counts[tc.priority] || 0) + 1;
    });

    document.getElementById('totalCases').textContent = result.total_cases;
    document.getElementById('p0Count').textContent = counts.P0;
    document.getElementById('p1Count').textContent = counts.P1;
    document.getElementById('p2Count').textContent = counts.P2;

    // 覆盖情况
    document.getElementById('coverageSummary').textContent = result.coverage_summary;

    // 渲染测试用例列表
    const list = document.getElementById('testCaseList');
    list.innerHTML = result.test_cases.map((tc, idx) => `
        <div class="testcase-item">
            <div class="testcase-header" onclick="toggleTestCase(${idx})">
                <h4>
                    <span class="testcase-id">${tc.case_id}</span>
                    ${tc.title}
                </h4>
                <div>
                    <span class="testcase-priority ${tc.priority}">${tc.priority}</span>
                    <span class="testcase-type">${tc.case_type}</span>
                </div>
            </div>
            <div class="testcase-body" id="tc-${idx}">
                <div class="testcase-meta">
                    ${tc.requirement_id ? `<span>📋 关联需求: ${tc.requirement_id}</span>` : ''}
                    ${tc.precondition ? `<span>⚡ 前置条件: ${tc.precondition}</span>` : ''}
                </div>
                ${tc.test_data ? `<p><strong>测试数据:</strong> ${tc.test_data}</p>` : ''}
                <div class="testcase-steps">
                    <h5>测试步骤</h5>
                    <table>
                        <thead>
                            <tr><th>步骤</th><th>操作</th><th>预期结果</th></tr>
                        </thead>
                        <tbody>
                            ${tc.steps.map(s => `
                                <tr>
                                    <td>${s.step_number}</td>
                                    <td>${s.action}</td>
                                    <td>${s.expected_result}</td>
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>
                ${tc.tags.length > 0 ? `
                    <div class="testcase-tags">
                        ${tc.tags.map(t => `<span class="testcase-tag">${t}</span>`).join('')}
                    </div>
                ` : ''}
            </div>
        </div>
    `).join('');

    showToast('测试用例生成完成！', 'success');
}

window.toggleTestCase = function(idx) {
    const body = document.getElementById(`tc-${idx}`);
    if (body) {
        body.classList.toggle('show');
    }
};

// 导出功能
document.getElementById('exportMarkdown')?.addEventListener('click', () => {
    if (currentDocumentId) {
        const aiProvider = document.querySelector('input[name="aiProvider"]:checked').value;
        window.open(`${API_BASE}/requirements/generate-testcases/export?document_id=${currentDocumentId}&ai_provider=${aiProvider}&format=markdown`, '_blank');
    }
});

document.getElementById('exportCsv')?.addEventListener('click', () => {
    if (currentDocumentId) {
        const aiProvider = document.querySelector('input[name="aiProvider"]:checked').value;
        window.open(`${API_BASE}/requirements/generate-testcases/export?document_id=${currentDocumentId}&ai_provider=${aiProvider}&format=csv`, '_blank');
    }
});

// 导出需求分析结果
document.getElementById('exportAnalysisMarkdown')?.addEventListener('click', () => {
    if (currentDocumentId) {
        const aiProvider = document.querySelector('input[name="aiProvider"]:checked').value;
        window.open(`${API_BASE}/requirements/analyze/export?document_id=${currentDocumentId}&ai_provider=${aiProvider}&format=markdown`, '_blank');
    }
});

// 从分析结果生成测试用例
document.getElementById('generateTestCasesFromAnalysis')?.addEventListener('click', () => {
    document.querySelector('[data-tab="testcase-gen"]').click();
    startTestCaseGeneration();
});

// 新建分析
document.getElementById('newAnalysis')?.addEventListener('click', () => {
    document.getElementById('reqAnalysisResult').style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// 重新生成测试用例
document.getElementById('newTestCase')?.addEventListener('click', () => {
    document.getElementById('testCaseResult').style.display = 'none';
    window.scrollTo({ top: 0, behavior: 'smooth' });
});

// 页面加载完成
document.addEventListener('DOMContentLoaded', () => {
    console.log('AI 文档检测服务已就绪');
    initTabs();  // 初始化选项卡
    updateStartButton();
    updateConfigVisibility();  // 初始化配置区域显示
});
