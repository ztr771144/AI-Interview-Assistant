<template>
  <div class="app-container">
    <!-- 全局隐藏的文件上传框，供所有 Tab 共用 -->
    <input type="file" ref="fileInput" @change="handleFileUpload" accept=".pdf" style="display: none;" />

    <!-- 顶部导航栏 -->
    <nav class="navbar">
      <div class="logo">🎯 AI 求职助手</div>
      <div class="tabs">
        <button :class="{ active: currentTab === 'interview' }" @click="currentTab = 'interview'">💼 模拟面试</button>
        <button :class="{ active: currentTab === 'resume' }" @click="currentTab = 'resume'">📝 简历诊断</button>
        <button :class="{ active: currentTab === 'jd' }" @click="currentTab = 'jd'">🎯 JD 匹配</button>
      </div>
    </nav>

    <div class="main-content">
      <!-- ================= 模块 C：模拟面试 ================= -->
      <div v-show="currentTab === 'interview'" class="tab-pane">
        <div v-if="chatHistory.length === 0" class="panel setup-section">
          <header>
            <h2>开启专属模拟面试</h2>
            <p>输入简历和 JD，AI 面试官将对你进行深度追问</p>
          </header>
          
          <div class="input-box">
            <div class="label-row">
              <label>你的简历：</label>
              <button class="upload-btn" @click="triggerUpload" :disabled="isUploading">
                {{ isUploading ? '⏳ 解析中...' : '📄 上传 PDF 简历' }}
              </button>
            </div>
            <textarea v-model="resumeText" placeholder="请粘贴简历内容，或点击右上角上传 PDF..."></textarea>
          </div>

          <div class="input-box">
            <label>目标岗位 JD：</label>
            <textarea v-model="jdText" placeholder="请粘贴岗位 JD..."></textarea>
          </div>
          
          <button class="action-btn" @click="startInterview" :disabled="isLoading || isUploading">
            {{ isLoading ? 'AI 正在准备面试...' : '开始模拟面试' }}
          </button>
        </div>

        <div v-else class="chat-section">
          <div class="chat-header">
            <h2>💼 面试进行中</h2>
            <button class="end-btn" @click="endInterview" :disabled="isGeneratingReport">
              {{ isGeneratingReport ? '报告生成中...' : '结束面试' }}
            </button>
          </div>

          <div class="chat-history" ref="chatContainer">
            <div v-for="(msg, index) in chatHistory" :key="index" :class="['message-bubble', msg.role === 'assistant' ? 'ai-msg' : 'user-msg']">
              <div class="avatar">{{ msg.role === 'assistant' ? '🤵' : '👨‍💻' }}</div>
              <div class="content">{{ msg.content }}</div>
            </div>
            <div v-if="isTyping" class="message-bubble ai-msg">
              <div class="avatar">🤵</div>
              <div class="content typing">面试官正在思考中...</div>
            </div>
          </div>

          <div class="input-area">
            <textarea v-model="currentAnswer" @keyup.enter="sendAnswer" placeholder="输入你的回答，按 Enter 发送..." :disabled="isLoading"></textarea>
            <button @click="sendAnswer" :disabled="isLoading || !currentAnswer.trim()">发送</button>
          </div>
        </div>

        <!-- 评分报告弹窗 -->
        <div v-if="reportData" class="report-overlay">
          <div class="report-card">
            <h2>📊 面试评估报告</h2>
            
            <div class="dimensions">
              <div v-for="dim in reportData.dimensions" :key="dim.dimension" class="dim-item">
                <h3>{{ dim.dimension }}：<span class="score">{{ dim.score }}</span> / 10</h3>
                <div class="evidence-box">
                  <strong>原话证据：</strong>
                  <ul><li v-for="(ev, i) in dim.evidence" :key="i">"{{ ev }}"</li></ul>
                </div>
              </div>
            </div>

            <div class="feedback-section"><h3>✨ 亮点</h3><ul><li v-for="(s, i) in reportData.strengths" :key="i">{{ s }}</li></ul></div>
            <div class="feedback-section"><h3>⚠️ 短板</h3><ul><li v-for="(w, i) in reportData.weaknesses" :key="i">{{ w }}</li></ul></div>
            <div class="feedback-section"><h3>💡 改进建议</h3><ul><li v-for="(sug, i) in reportData.suggestions" :key="i">{{ sug }}</li></ul></div>
            
            <!-- 交叉复核 -->
            <div class="feedback-section cross-section" v-if="reportData.cross_review">
              <h3>⚖️ 交叉复核意见</h3>
              <p>{{ reportData.cross_review }}</p>
            </div>
            
            <!-- 底部操作按钮 -->
            <div class="report-actions">
              <button class="export-btn" @click="exportMarkdown">📥 导出 Markdown 报告</button>
              <button class="action-btn close-report-btn" @click="resetInterview">开启新面试</button>
            </div>
          </div>
        </div>
      </div>

      <!-- ================= 模块 A：简历诊断 ================= -->
      <div v-show="currentTab === 'resume'" class="tab-pane">
        <div class="panel">
          <h2>📝 简历深度诊断</h2>
          <p class="desc">按 5 项 HR 检查清单挑毛病，并给出改写示范。</p>
          
          <div class="input-box">
            <div class="label-row">
              <label>简历内容：</label>
              <button class="upload-btn" @click="triggerUpload" :disabled="isUploading">
                {{ isUploading ? '⏳ 解析中...' : '📄 上传 PDF 简历' }}
              </button>
            </div>
            <textarea v-model="resumeText" placeholder="粘贴你的简历内容..." class="large-input"></textarea>
          </div>

          <button class="action-btn" @click="diagnoseResume" :disabled="isLoading || isUploading">
            {{ isLoading ? 'AI 正在挑刺...' : '开始诊断' }}
          </button>
        </div>

        <div v-if="diagnosisResult" class="result-panel">
          <h3>诊断报告</h3>
          <div v-for="(item, i) in diagnosisResult.issues" :key="i" class="issue-card">
            <div class="issue-header">
              <span class="priority" :class="item.priority === '高' ? 'p-high' : 'p-low'">{{ item.priority }}优先级</span>
              <span class="category">{{ item.category }}</span>
            </div>
            <div class="issue-body">
              <p class="original">🔴 原句：{{ item.original_text }}</p>
              <p class="rewritten">🟢 改写：{{ item.rewritten_text }}</p>
              <p class="suggestion">💡 建议：{{ item.suggestion }}</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ================= 模块 B：JD 匹配 ================= -->
      <div v-show="currentTab === 'jd'" class="tab-pane">
        <div class="panel">
          <h2>🎯 岗位 JD 匹配</h2>
          <p class="desc">分析你的简历与目标岗位的差距，并给出补齐计划。</p>
          
          <div class="two-col">
            <div class="input-box">
              <div class="label-row">
                <label>你的简历：</label>
                <button class="upload-btn" @click="triggerUpload" :disabled="isUploading">
                  {{ isUploading ? '⏳ 解析中...' : '📄 上传 PDF' }}
                </button>
              </div>
              <textarea v-model="resumeText" placeholder="简历内容..."></textarea>
            </div>
            <div class="input-box">
              <label>目标岗位 JD：</label>
              <textarea v-model="jdText" placeholder="目标岗位 JD..."></textarea>
            </div>
          </div>
          
          <button class="action-btn" @click="matchJD" :disabled="isLoading || isUploading">
            {{ isLoading ? '正在分析匹配度...' : '开始匹配' }}
          </button>
        </div>

        <div v-if="matchResult" class="result-panel">
          <h3>匹配度：<span class="score-text">{{ matchResult.match_score }}</span> / 100</h3>
          <div class="match-details">
            <div>
              <h4>✅ 已覆盖能力</h4>
              <ul><li v-for="(s, i) in matchResult.covered_skills" :key="i">{{ s }}</li></ul>
            </div>
            <div>
              <h4>❌ 能力差距</h4>
              <ul><li v-for="(s, i) in matchResult.gap_skills" :key="i">{{ s }}</li></ul>
            </div>
          </div>
          <div class="plan-section">
            <h4>🚀 补齐计划</h4>
            <ul><li v-for="(p, i) in matchResult.improvement_plan" :key="i">{{ p }}</li></ul>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'

// ================= 全局状态 =================
const currentTab = ref('interview')
const isLoading = ref(false)
const resumeText = ref('') 
const jdText = ref('')

// ================= 全局 PDF 上传逻辑 =================
const fileInput = ref(null)
const isUploading = ref(false)

const triggerUpload = () => {
  fileInput.value.click()
}

const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  if (!file.name.toLowerCase().endsWith('.pdf')) return alert('目前仅支持 PDF 格式的简历哦！')
  
  isUploading.value = true
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    const response = await fetch('http://127.0.0.1:8000/api/interview/upload-resume', { method: 'POST', body: formData })
    if (!response.ok) throw new Error('解析失败')
    const data = await response.json()
    resumeText.value = data.text // 自动同步到所有 Tab
  } catch (error) {
    alert('简历解析失败，请检查后端是否启动')
  } finally {
    isUploading.value = false
    event.target.value = '' // 清空，允许重复上传
  }
}

// ================= 模块 C：模拟面试状态 =================
const isTyping = ref(false)
const currentAnswer = ref('')
const chatHistory = ref([])
const chatContainer = ref(null)
const isGeneratingReport = ref(false)
const reportData = ref(null)

const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) chatContainer.value.scrollTop = chatContainer.value.scrollHeight
}

const startInterview = async () => {
  if (!resumeText.value.trim() || !jdText.value.trim()) return alert("请填写简历和JD后再开始面试")
  isLoading.value = true
  try {
    const response = await fetch('http://127.0.0.1:8000/api/interview/opening', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_text: resumeText.value, jd_text: jdText.value })
    })
    const data = await response.json()
    chatHistory.value.push({ role: 'assistant', content: `你好，我是今天的面试官。我们开始吧。\n\n${data.opening_question}` })
    scrollToBottom()
  } catch (error) {
    alert('获取首问失败，请检查后端')
  } finally {
    isLoading.value = false
  }
}

const sendAnswer = async () => {
  if (!currentAnswer.value.trim()) return
  const answer = currentAnswer.value
  currentAnswer.value = ''
  isLoading.value = true
  chatHistory.value.push({ role: 'user', content: answer })
  scrollToBottom()
  isTyping.value = true

  try {
    const history = chatHistory.value.slice(0, -1)
    const response = await fetch('http://127.0.0.1:8000/api/interview/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ history: history, current_answer: answer })
    })
    const data = await response.json()
    chatHistory.value.push({ role: 'assistant', content: data.reply })
    scrollToBottom()
  } catch (error) {
    alert('获取追问失败')
    chatHistory.value.pop()
    currentAnswer.value = answer
  } finally {
    isLoading.value = false
    isTyping.value = false
  }
}

const endInterview = async () => {
  if (chatHistory.value.length < 3) return alert("对话太少啦，至少聊两轮再结束吧！")
  isGeneratingReport.value = true
  try {
    const response = await fetch('http://127.0.0.1:8000/api/interview/report', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ history: chatHistory.value, current_answer: "" })
    })
    reportData.value = await response.json()
  } catch (error) {
    alert('报告生成失败')
  } finally {
    isGeneratingReport.value = false
  }
}

const resetInterview = () => {
  chatHistory.value = []
  currentAnswer.value = ''
  reportData.value = null
}

// 导出 Markdown 逻辑
const exportMarkdown = () => {
  if (!reportData.value) return
  
  const r = reportData.value
  let md = `# 📊 模拟面试评估报告\n\n`
  
  md += `## 🎯 维度评分\n\n`
  r.dimensions.forEach(d => {
    md += `### ${d.dimension}：${d.score} / 10\n`
    md += `**原话证据：**\n`
    d.evidence.forEach(e => { md += `- "${e}"\n` })
    md += `\n`
  })
  
  md += `## ✨ 亮点\n${r.strengths.map(s => `- ${s}`).join('\n')}\n\n`
  md += `## ⚠️ 短板\n${r.weaknesses.map(w => `- ${w}`).join('\n')}\n\n`
  md += `## 💡 改进建议\n${r.suggestions.map(s => `- ${s}`).join('\n')}\n\n`
  md += `## ⚖️ 交叉复核\n> ${r.cross_review}\n`
  
  // 触发下载
  const blob = new Blob([md], { type: 'text/markdown;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `面试复盘报告_${new Date().toLocaleDateString()}.md`
  link.click()
  URL.revokeObjectURL(url)
}

// ================= 模块 A：简历诊断状态 =================
const diagnosisResult = ref(null)
const diagnoseResume = async () => {
  if (!resumeText.value.trim()) return alert('请输入或上传简历')
  isLoading.value = true
  try {
    const res = await fetch('http://127.0.0.1:8000/api/resume/diagnose', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_text: resumeText.value })
    })
    diagnosisResult.value = await res.json()
  } catch (e) { alert('诊断失败') }
  finally { isLoading.value = false }
}

// ================= 模块 B：JD 匹配状态 =================
const matchResult = ref(null)
const matchJD = async () => {
  if (!resumeText.value.trim() || !jdText.value.trim()) return alert('请填写或上传简历和JD')
  isLoading.value = true
  try {
    const res = await fetch('http://127.0.0.1:8000/api/jd/match', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_text: resumeText.value, jd_text: jdText.value })
    })
    matchResult.value = await res.json()
  } catch (e) { alert('匹配失败') }
  finally { isLoading.value = false }
}
</script>

<style scoped>
/* ================= 全局布局 ================= */
.app-container { font-family: sans-serif; background: #f0f2f5; min-height: 100vh; padding-bottom: 50px; }
.navbar { background: #fff; padding: 15px 30px; display: flex; justify-content: space-between; align-items: center; box-shadow: 0 2px 8px rgba(0,0,0,0.05); margin-bottom: 20px; position: sticky; top: 0; z-index: 100;}
.logo { font-size: 20px; font-weight: bold; color: #333; }
.tabs button { background: none; border: none; padding: 10px 20px; font-size: 16px; cursor: pointer; border-radius: 6px; color: #555; transition: 0.3s; font-weight: bold; }
.tabs button:hover { background: #f0f0f0; }
.tabs button.active { background: #e6f7ff; color: #1890ff; }
.main-content { max-width: 900px; margin: 0 auto; }

/* ================= 通用面板 ================= */
.panel { background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); margin-bottom: 20px; }
.panel h2 { margin-top: 0; color: #333;}
.desc { color: #666; margin-bottom: 15px; font-size: 14px; }
.input-box { display: flex; flex-direction: column; margin-bottom: 15px; }
.label-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 5px; }
textarea { width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 6px; font-family: inherit; box-sizing: border-box; resize: vertical; outline: none; transition: 0.2s;}
textarea:focus { border-color: #1890ff; box-shadow: 0 0 0 2px rgba(24,144,255,0.2); }
.large-input { height: 200px; }
.two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
.two-col textarea { height: 150px; }

/* ================= 按钮 ================= */
.action-btn { width: 100%; padding: 12px; background: #1890ff; color: #fff; border: none; border-radius: 6px; font-size: 16px; cursor: pointer; transition: 0.3s;}
.action-btn:hover { background: #40a9ff; }
.action-btn:disabled { background: #ccc; cursor: not-allowed; }
.upload-btn { width: auto; padding: 6px 12px; font-size: 13px; background: #52c41a; color: white; border: none; border-radius: 4px; cursor: pointer; transition: 0.2s; display: flex; align-items: center; gap: 5px;}
.upload-btn:hover { background: #73d13d; }
.upload-btn:disabled { background: #ccc; cursor: not-allowed; }

/* ================= 模块 C：聊天室 ================= */
.chat-section { display: flex; flex-direction: column; height: 75vh; background: #f5f7fa; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); overflow: hidden; }
.chat-header { display: flex; justify-content: space-between; align-items: center; padding: 15px 20px; background: #fff; border-bottom: 1px solid #eee; }
.chat-header h2 { margin: 0; font-size: 18px; color: #333; }
.end-btn { width: auto; padding: 8px 16px; background: #ff4d4f; font-size: 14px; border: none; border-radius: 4px; color: white; cursor: pointer; }
.end-btn:hover { background: #ff7875; }

.chat-history { flex: 1; padding: 20px; overflow-y: auto; display: flex; flex-direction: column; gap: 15px; }
.message-bubble { display: flex; gap: 10px; max-width: 80%; }
.message-bubble .avatar { width: 36px; height: 36px; border-radius: 50%; display: flex; justify-content: center; align-items: center; background: #fff; font-size: 20px; flex-shrink: 0; box-shadow: 0 2px 4px rgba(0,0,0,0.1);}
.message-bubble .content { padding: 12px 16px; border-radius: 8px; line-height: 1.5; white-space: pre-wrap; word-break: break-word; font-size: 15px;}
.ai-msg { align-self: flex-start; }
.ai-msg .content { background: #fff; color: #333; border: 1px solid #e0e0e0; border-top-left-radius: 0; }
.user-msg { align-self: flex-end; flex-direction: row-reverse; }
.user-msg .content { background: #1890ff; color: #fff; border-top-right-radius: 0; }
.typing { color: #888; font-style: italic; }
.input-area { display: flex; gap: 10px; padding: 15px; background: #fff; border-top: 1px solid #eee; }
.input-area textarea { height: 50px; resize: none; border-radius: 8px; flex: 1; margin-bottom: 0;}
.input-area button { width: 80px; border-radius: 8px; padding: 0; border: none; background: #1890ff; color: white; font-size: 16px; cursor: pointer;}
.input-area button:disabled { background: #ccc; }

/* ================= 弹窗报告 ================= */
.report-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.6); display: flex; justify-content: center; align-items: center; z-index: 1000; }
.report-card { background: #fff; width: 90%; max-width: 600px; max-height: 90vh; overflow-y: auto; border-radius: 12px; padding: 24px; box-shadow: 0 10px 30px rgba(0,0,0,0.2); }
.report-card h2 { text-align: center; margin-top: 0; color: #333; }
.dimensions { display: flex; flex-direction: column; gap: 15px; margin-bottom: 20px; }
.dim-item { background: #f8f9fa; padding: 15px; border-radius: 8px; border-left: 4px solid #1890ff; }
.dim-item h3 { margin: 0 0 10px 0; font-size: 16px; }
.dim-item .score { color: #ff4d4f; font-size: 20px; font-weight: bold; }
.evidence-box { font-size: 14px; color: #666; }
.evidence-box ul { margin: 5px 0 0 0; padding-left: 20px; }
.feedback-section { margin-bottom: 15px; }
.feedback-section h3 { font-size: 16px; margin-bottom: 8px; }
.feedback-section ul { margin: 0; padding-left: 20px; font-size: 14px; color: #444; line-height: 1.6; }
.cross-section { background: #fffbe6; padding: 15px; border-radius: 6px; border: 1px solid #ffe58f; margin-top: 15px;}
.cross-section p { margin: 0; font-size: 14px; line-height: 1.6; color: #555;}

.report-actions { display: flex; gap: 10px; margin-top: 20px; }
.export-btn { flex: 1; padding: 12px; background: #52c41a; color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 16px; transition: 0.3s;}
.export-btn:hover { background: #73d13d; }
.report-actions .action-btn { flex: 1; margin-top: 0; }

/* ================= 模块 A & B 结果 ================= */
.result-panel { background: #fff; padding: 24px; border-radius: 8px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.issue-card { border: 1px solid #ffe58f; background: #fffbe6; border-radius: 6px; margin-bottom: 15px; overflow: hidden; }
.issue-header { padding: 10px 15px; background: #fff1b8; border-bottom: 1px solid #ffe58f; display: flex; gap: 10px; align-items: center; }
.priority { font-size: 12px; padding: 2px 8px; border-radius: 4px; color: #fff; }
.p-high { background: #ff4d4f; }
.p-low { background: #faad14; }
.issue-body { padding: 15px; font-size: 14px; line-height: 1.6; }
.original { color: #cf1322; text-decoration: line-through; }
.rewritten { color: #389e0d; font-weight: bold; }

.score-text { color: #1890ff; font-size: 28px; }
.match-details { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0; border-bottom: 1px dashed #eee; padding-bottom: 20px; }
.plan-section h4 { color: #d46b08; }
</style>