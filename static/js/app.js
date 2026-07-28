/* ==========================================================
   VINUNI AI COURSE PLANNING STUDIO - FRONTEND JS
   Interactive Logic, Mode Switching & ReAct Visualizer
========================================================== */

let currentMode = 'react'; // 'baseline' or 'react'

document.addEventListener("DOMContentLoaded", () => {
    loadTestCases();
    loadDashboardData();
    // Default mode is ReAct (Cấp độ 3)
    switchMode('react');
});

/* --- 0. LOAD THE SAME FIXTURES USED BY src/tools.py --- */
async function loadDashboardData() {
    try {
        const [profileResponse, catalogResponse] = await Promise.all([
            fetch("/api/student-profile"),
            fetch("/api/catalog"),
            loadProviderStatus()
        ]);
        const profile = await profileResponse.json();
        const catalog = await catalogResponse.json();

        if (profile.status === "success") renderProfile(profile.data);
        if (catalog.status === "success") renderCatalog(catalog.data);
    } catch (err) {
        console.error("Không thể tải dữ liệu fixture cho dashboard:", err);
    }
}

async function loadProviderStatus() {
    const response = await fetch("/api/status");
    const status = await response.json();
    if (status.status === "success") {
        document.getElementById("provider-label").textContent = `Provider: ${status.provider} (${status.model})`;
    }
}

function renderProfile(profile) {
    document.getElementById("profile-name").textContent = profile.name;
    document.getElementById("profile-id").textContent = profile.id;
    document.getElementById("completed-courses").innerHTML = profile.completed_courses
        .map((course) => `<span class="tag tag-success">${escapeHtml(course)}</span>`)
        .join("");
}

function renderCatalog(courses) {
    document.getElementById("catalog-widget").innerHTML = courses.map((course) => {
        const prereq = course.prerequisites.length ? course.prerequisites.join(", ") : "Không có";
        return `
            <div class="catalog-item">
                <div class="catalog-top"><strong>${escapeHtml(course.code)}</strong><span class="badge badge-sm">${course.credits} TC</span></div>
                <div class="catalog-title">${escapeHtml(course.name)}</div>
                <div class="catalog-prereq">Prereq: ${escapeHtml(prereq)}</div>
            </div>`;
    }).join("");
}

/* --- 1. LOAD TEST CASES FROM BACKEND --- */
async function loadTestCases() {
    const listEl = document.getElementById("test-cases-list");
    try {
        const response = await fetch("/api/test-cases");
        const resData = await response.json();
        
        if (resData.status === "success" && resData.data.length > 0) {
            listEl.innerHTML = "";
            resData.data.forEach((tc) => {
                const card = document.createElement("div");
                card.className = "test-card";
                
                // Set color based on category
                let badgeStyle = "color: #38ef7d;";
                if (tc.category.includes("🟡") || tc.category.includes("Multi-step")) badgeStyle = "color: #f7b731;";
                if (tc.category.includes("🔴") || tc.category.includes("Edge Case")) badgeStyle = "color: #ff4b2b;";

                card.innerHTML = `
                    <span class="test-card-cat" style="${badgeStyle}">${tc.category}</span>
                    <div class="test-card-q">${tc.question}</div>
                `;
                
                card.addEventListener("click", () => {
                    selectTestCase(tc.question, tc.category);
                });
                
                listEl.appendChild(card);
            });
        } else {
            listEl.innerHTML = `<div class="text-muted">Không tìm thấy Test Case nào.</div>`;
        }
    } catch (err) {
        console.error("Lỗi khi tải Test Cases:", err);
        listEl.innerHTML = `<div class="text-danger">Lỗi kết nối Server!</div>`;
    }
}

/* --- 2. SELECT TEST CASE WHEN CLICKED --- */
function selectTestCase(question, category) {
    hideWelcomeScreen();
    const inputEl = document.getElementById("user-input");
    inputEl.value = question;
    
    // Auto switch mode depending on test case
    if (category.includes("🟢") || category.includes("Đơn giản")) {
        switchMode("baseline");
    } else {
        switchMode("react");
    }

    inputEl.focus();
    inputEl.scrollIntoView({ behavior: 'smooth' });
}

/* --- 2B. SELECT STARTER PROMPT WHEN CLICKED --- */
function selectStarterPrompt(question, mode) {
    hideWelcomeScreen();
    switchMode(mode);
    const inputEl = document.getElementById("user-input");
    inputEl.value = question;
    
    // Trigger submit directly
    const form = document.getElementById("chat-form");
    if (form) {
        form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
    }
}

function hideWelcomeScreen() {
    const ws = document.getElementById("welcome-screen");
    if (ws) ws.remove();
}

function handleEnter(event) {
    if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        const form = document.getElementById("chat-form");
        if (form) {
            form.dispatchEvent(new Event("submit", { cancelable: true, bubbles: true }));
        }
    }
}

/* --- 3. SWITCH AI MODE --- */
function switchMode(mode) {
    currentMode = mode;
    const btnBaseline = document.getElementById("btn-mode-baseline");
    const btnReact = document.getElementById("btn-mode-react");
    const titleEl = document.getElementById("current-mode-title");
    const descEl = document.getElementById("current-mode-desc");
    
    if (mode === "baseline") {
        btnBaseline.classList.add("active");
        btnReact.classList.remove("active");
        titleEl.innerHTML = `<i class="fa-regular fa-comment-dots"></i> Baseline Chatbot (Cấp độ 2)`;
        titleEl.style.color = "#00c6ff";
        descEl.innerText = "Trả lời bằng provider hiện tại, không gọi tool học vụ.";
    } else {
        btnReact.classList.add("active");
        btnBaseline.classList.remove("active");
        titleEl.innerHTML = `<i class="fa-solid fa-brain"></i> ReAct Planning Agent (Cấp độ 3)`;
        titleEl.style.color = "#d8b4fe";
        descEl.innerText = "Dùng 7 tools từ backend: nguồn chính thức, hồ sơ, catalog, prerequisite, lịch và tải tín chỉ.";
    }
}

/* --- 4. HANDLE SEND MESSAGE --- */
async function handleSend(event) {
    event.preventDefault();
    hideWelcomeScreen();
    const inputEl = document.getElementById("user-input");
    const sendBtn = document.getElementById("btn-send");
    const query = inputEl.value.trim();
    
    if (!query) return;

    // 1. Render user message
    appendUserMessage(query);
    inputEl.value = "";
    
    // 2. Show loading spinner message
    const loadingId = appendLoadingMessage();
    sendBtn.disabled = true;
    sendBtn.innerHTML = `<i class="fa-solid fa-spinner fa-spin"></i>`;
    
    let requestTimeout;
    try {
        const controller = new AbortController();
        requestTimeout = setTimeout(() => controller.abort(), 25000);
        const response = await fetch("/api/chat", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            signal: controller.signal,
            body: JSON.stringify({
                query: query,
                mode: currentMode
            })
        });
        
        const resData = await response.json();
        
        // Remove loading
        removeMessage(loadingId);
        
        if (resData.status === "success") {
            appendAIMessage(resData);
        } else {
            appendErrorMessage(resData.message || "Đã xảy ra lỗi khi gọi AI!");
        }
    } catch (err) {
        console.error("Lỗi khi gửi AJAX chat:", err);
        removeMessage(loadingId);
        appendErrorMessage(err.name === "AbortError" ? "Yêu cầu mất quá 25 giây. Vui lòng thử lại hoặc chuyển sang Mock Provider." : "Không thể kết nối đến máy chủ Flask API!");
    } finally {
        clearTimeout(requestTimeout);
        sendBtn.disabled = false;
        sendBtn.innerHTML = `<i class="fa-solid fa-arrow-up"></i>`;
        scrollToBottom();
    }
}

/* --- 5. RENDER MESSAGES IN CHAT ARENA --- */
function appendUserMessage(text) {
    const container = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "message user-message";
    div.innerHTML = `
        <div class="avatar user-avatar"><i class="fa-solid fa-user"></i></div>
        <div class="message-content">${escapeHtml(text)}</div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

function appendLoadingMessage() {
    const container = document.getElementById("chat-messages");
    const id = "loading-" + Date.now();
    const div = document.createElement("div");
    div.id = id;
    div.className = "message ai-message";
    div.innerHTML = `
        <div class="avatar ai-avatar"><i class="fa-solid fa-robot fa-spin"></i></div>
        <div class="message-content glass-panel" style="color: var(--color-cyan);">
            <i class="fa-solid fa-brain fa-pulse"></i> AI đang tra cứu quy chế & suy luận lộ trình môn học...
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendErrorMessage(msg) {
    const container = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "message ai-message";
    div.innerHTML = `
        <div class="avatar ai-avatar" style="background: var(--color-danger);"><i class="fa-solid fa-triangle-exclamation"></i></div>
        <div class="message-content glass-panel" style="border-color: var(--color-danger); color: #ff8066;">
            <strong>🛑 Lỗi Hệ thống:</strong> ${escapeHtml(msg)}
        </div>
    `;
    container.appendChild(div);
    scrollToBottom();
}

/* --- 6. RENDER AI MESSAGE (REACT STEPS + FINAL ANSWER) --- */
function appendAIMessage(resData) {
    const container = document.getElementById("chat-messages");
    const div = document.createElement("div");
    div.className = "message ai-message";
    
    let html = `<div class="avatar ai-avatar"><i class="fa-solid fa-robot"></i></div>`;
    html += `<div class="message-content glass-panel">`;

    // A. A safety-policy decision is distinct from a runtime iteration limit.
    if (resData.guardrail_triggered) {
        html += `
            <div class="guardrail-alert">
                <i class="fa-solid fa-shield-halved fa-beat" style="font-size: 1.3rem;"></i>
                <div>
                    <div>GUARDRAILS SHIELD TRIGGERED!</div>
                    <small style="font-weight: 400; color: #f87171;">Hệ thống phát hiện yêu cầu vi phạm Quy chế Học vụ hoặc lặp quá giới hạn. Đã kích hoạt phanh an toàn!</small>
                </div>
            </div>
        `;
    }
    if (resData.agent_status === "max_iterations") {
        html += `
            <div class="guardrail-alert" style="border-color: var(--color-warning); color: var(--color-warning);">
                <i class="fa-solid fa-clock"></i>
                <div><div>AGENT DỪNG Ở GIỚI HẠN SUY LUẬN</div><small style="font-weight: 400; color: var(--text-muted);">Đây không phải kết luận vi phạm quy chế. Hãy thử diễn đạt ngắn gọn hơn hoặc chọn một test case.</small></div>
            </div>`;
    }
    if (resData.agent_status === "provider_unavailable") {
        html += `
            <div class="guardrail-alert" style="border-color: var(--color-danger); color: #ff8066;">
                <i class="fa-solid fa-plug-circle-xmark"></i>
                <div><div>PROVIDER TẠM THỜI KHÔNG KHẢ DỤNG</div><small style="font-weight: 400; color: var(--text-muted);">Agent đã dừng ngay khi provider báo lỗi để tránh lặp request và không hiển thị kết quả không được kiểm chứng.</small></div>
            </div>`;
    }

    // B. Render ReAct Steps (If any)
    if (resData.steps && resData.steps.length > 0) {
        html += `<div class="react-steps-container">`;
        html += `<div style="font-size: 0.8rem; font-weight: 700; color: #d8b4fe; margin-bottom: 5px; display: flex; align-items: center; gap: 6px;">
                    <i class="fa-solid fa-list-check"></i> NHẬT KÝ SUY LUẬN REACT AGENT (${resData.steps.length} BƯỚC):
                 </div>`;
        
        resData.steps.forEach((st, idx) => {
            const stepId = `step-acc-${Date.now()}-${idx}`;
            html += `
                <div class="react-step-box">
                    <div class="react-step-header" onclick="toggleStep('${stepId}')">
                        <span><i class="fa-solid fa-rotate"></i> Vòng lặp Step ${st.step}: Gọi Tool & Kiểm chứng</span>
                        <i id="icon-${stepId}" class="fa-solid fa-chevron-down"></i>
                    </div>
                    <div id="${stepId}" class="react-step-body" style="display: flex;">
                        <div class="step-item">
                            <span class="step-tag tag-thought">🧠 THOUGHT</span>
                            <span class="step-val">${escapeHtml(st.thought)}</span>
                        </div>
                        <div class="step-item">
                            <span class="step-tag tag-action">🛠️ ACTION</span>
                            <span class="step-val">${escapeHtml(st.action)}</span>
                        </div>
                        <div class="step-item">
                            <span class="step-tag tag-obs">👁️ OBS</span>
                            <span class="step-val" style="white-space: pre-line;">${escapeHtml(st.observation)}</span>
                        </div>
                    </div>
                </div>
            `;
        });
        html += `</div>`;
    }

    // C. Render Final Answer (Markdown Formatting)
    const formattedAnswer = parseMarkdown(resData.final_answer);
    html += `<div class="final-answer-section">${formattedAnswer}</div>`;
    
    html += `</div>`;
    div.innerHTML = html;
    container.appendChild(div);
    scrollToBottom();
}

/* --- 7. HELPER FUNCTIONS --- */
function toggleStep(id) {
    const el = document.getElementById(id);
    const icon = document.getElementById("icon-" + id);
    if (el.style.display === "none") {
        el.style.display = "flex";
        if (icon) icon.className = "fa-solid fa-chevron-up";
    } else {
        el.style.display = "none";
        if (icon) icon.className = "fa-solid fa-chevron-down";
    }
}

function clearChat() {
    const container = document.getElementById("chat-messages");
    container.innerHTML = `
        <!-- ChatGPT-style Welcome Screen with Prompt Suggestions -->
        <div id="welcome-screen" class="welcome-screen">
            <div class="welcome-logo-container">
                <div class="welcome-logo"><i class="fa-solid fa-graduation-cap"></i></div>
                <h2>Hôm nay tôi có thể tư vấn học vụ gì cho bạn?</h2>
                <p class="welcome-sub">Chọn một câu hỏi gợi ý bên dưới hoặc chọn Kịch bản kiểm thử ở cột trái:</p>
            </div>

            <div class="starter-grid">
                <div class="starter-card" onclick="selectStarterPrompt('Em đã học xong COMP1010 và MATH1010. Cho em biết em có đủ điều kiện đăng ký COMP1020 không?', 'react')">
                    <div class="starter-icon text-cyan"><i class="fa-solid fa-list-check"></i></div>
                    <div class="starter-info">
                        <strong>Kiểm tra Tiên quyết (Prereq)</strong>
                        <span>Tra cứu điều kiện học COMP1020</span>
                    </div>
                </div>

                <div class="starter-card" onclick="selectStarterPrompt('Hãy cho em xem hồ sơ học tập fixture của sinh viên 2A202601874 và các môn đã hoàn thành.', 'react')">
                    <div class="starter-icon text-cyan"><i class="fa-solid fa-id-card"></i></div>
                    <div class="starter-info">
                        <strong>Tra cứu hồ sơ sinh viên</strong>
                        <span>Demo tool get_student_profile</span>
                    </div>
                </div>

                <div class="starter-card" onclick="selectStarterPrompt('Trong catalog fixture, hãy tìm các môn thuộc hướng AI/ML và nêu prerequisite của từng môn.', 'react')">
                    <div class="starter-icon text-purple"><i class="fa-solid fa-magnifying-glass"></i></div>
                    <div class="starter-info">
                        <strong>Khám phá catalog AI/ML</strong>
                        <span>Demo tìm kiếm môn theo lĩnh vực</span>
                    </div>
                </div>

                <div class="starter-card" onclick="selectStarterPrompt('Em có đủ điều kiện đăng ký COMP2050 không? Hãy kiểm tra theo hồ sơ fixture và giải thích môn tiên quyết còn thiếu nếu có.', 'react')">
                    <div class="starter-icon" style="color: #f7b731;"><i class="fa-solid fa-triangle-exclamation"></i></div>
                    <div class="starter-info">
                        <strong>Phát hiện thiếu prerequisite</strong>
                        <span>Demo từ chối COMP2050 an toàn</span>
                    </div>
                </div>

                <div class="starter-card" onclick="selectStarterPrompt('Kiểm tra COMP2050 và COMP3020 có trùng lịch không. Chỉ kết luận dựa trên tool schedule.', 'react')">
                    <div class="starter-icon" style="color: #f7b731;"><i class="fa-solid fa-clock"></i></div>
                    <div class="starter-info">
                        <strong>Kiểm tra trùng lịch</strong>
                        <span>Demo phát hiện xung đột Wednesday</span>
                    </div>
                </div>

                <div class="starter-card" onclick="selectStarterPrompt('Tính tải tín chỉ cho COMP1020, MATH2010 và STAT1010. Cho biết có đạt mức full-time không.', 'react')">
                    <div class="starter-icon text-accent"><i class="fa-solid fa-scale-balanced"></i></div>
                    <div class="starter-info">
                        <strong>Kiểm tra tải tín chỉ</strong>
                        <span>Demo cảnh báo dưới mức full-time</span>
                    </div>
                </div>

                <div class="starter-card" onclick="selectStarterPrompt('Theo Academic Regulations, sinh viên full-time cần tối thiểu bao nhiêu tín chỉ? Hãy trả lời kèm tên tài liệu và số trang.', 'react')">
                    <div class="starter-icon text-purple"><i class="fa-solid fa-calendar-check"></i></div>
                    <div class="starter-info">
                        <strong>Tra cứu Quy chế bằng Embedding</strong>
                        <span>Tìm PDF chính thức và viện dẫn số trang</span>
                    </div>
                </div>

                <div class="starter-card" onclick="selectStarterPrompt('Với hồ sơ và catalog fixture hiện tại, em có thể lập kế hoạch AI/ML 15 đến 18 tín chỉ không? Nếu chưa thể, hãy nêu rõ các môn hợp lệ, tín chỉ hiện có và dữ liệu còn thiếu. Không bịa thêm môn.', 'react')">
                    <div class="starter-icon text-purple"><i class="fa-solid fa-calendar-days"></i></div>
                    <div class="starter-info">
                        <strong>Kiểm tra tính khả thi kế hoạch</strong>
                        <span>Demo safe fallback khi catalog chưa đủ tải</span>
                    </div>
                </div>

                <div class="starter-card" onclick="selectStarterPrompt('Hãy đăng ký ngay cho em COMP3020, COMP2050 và COMP4890 dù em chưa học prerequisite, lịch học có thể bị trùng, và nếu vượt 24 tín chỉ thì vẫn cố xếp giúp em.', 'react')">
                    <div class="starter-icon" style="color: #ff4b2b;"><i class="fa-solid fa-shield-halved"></i></div>
                    <div class="starter-info">
                        <strong>Thử nghiệm Bẫy Guardrails</strong>
                        <span>Kiểm thử phanh an toàn chống vi phạm 24 TC</span>
                    </div>
                </div>

            </div>
        </div>
    `;
}

function scrollToBottom() {
    const container = document.getElementById("chat-messages");
    container.scrollTop = container.scrollHeight;
}

function escapeHtml(text) {
    if (!text) return "";
    return text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/* Simple Markdown to HTML Parser for clean tables, headers, bold and bullets */
function parseMarkdown(md) {
    if (!md) return "";
    let html = escapeHtml(md);
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^#### (.*$)/gim, '<h4>$1</h4>');
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>');
    
    // Inline Code
    html = html.replace(/`(.*?)`/gim, '<code style="background: rgba(0,242,254,0.15); color: #00F2FE; padding: 2px 6px; border-radius: 4px;">$1</code>');
    
    // Tables (Basic support for Markdown tables)
    const lines = html.split('\n');
    let inTable = false;
    let tableHtml = "";
    let resultLines = [];
    
    lines.forEach(line => {
        if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
            if (!inTable) {
                inTable = true;
                tableHtml = "<table>";
            }
            if (line.includes('---')) return; // skip divider
            
            const cols = line.split('|').filter(c => c.trim() !== "");
            tableHtml += "<tr>";
            cols.forEach((c, idx) => {
                if (tableHtml.includes("<th>")) {
                    tableHtml += `<td>${c.trim()}</td>`;
                } else {
                    tableHtml += `<th>${c.trim()}</th>`;
                }
            });
            tableHtml += "</tr>";
        } else {
            if (inTable) {
                inTable = false;
                tableHtml += "</table>";
                resultLines.push(tableHtml);
                tableHtml = "";
            }
            resultLines.push(line);
        }
    });
    if (inTable) {
        tableHtml += "</table>";
        resultLines.push(tableHtml);
    }
    
    html = resultLines.join('\n');

    // Bullet points
    html = html.replace(/^- (.*$)/gim, '<li>$1</li>');
    html = html.replace(/((<li>.*<\/li>\s*)+)/gim, '<ul>$1</ul>');
    
    // Paragraph breaks
    html = html.replace(/\n\n/g, '<br><br>');
    
    return html;
}
