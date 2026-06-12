import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = window.location.port === '5173'
  ? 'http://localhost:8000/api'
  : (import.meta.env.VITE_API_URL || '/api');

const getInspiringWord = (pct) => {
  if (pct >= 90) return { title: "Outstanding! 🌟", text: "You have mastered this level with exceptional performance." };
  if (pct >= 80) return { title: "Excellent! 👏", text: "Fantastic result! You have a very strong grasp of the material." };
  if (pct >= 60) return { title: "Good Job! 👍", text: "Well done! You've successfully demonstrated your proficiency." };
  if (pct >= 33) return { title: "Passed! ✔", text: "You've met the requirements. Keep up the effort to improve further." };
  return { title: "Keep Trying! 💪", text: "Don't give up! Consistent practice will help you improve and pass next time." };
};

function App() {
  const [token, setToken] = useState(localStorage.getItem('exam_token') || '');
  const [user, setUser] = useState(null);
  const [loginRole, setLoginRole] = useState('student'); // 'student' or 'admin'
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [authError, setAuthError] = useState('');

  // Routing navigation
  const [adminTab, setAdminTab] = useState('dashboard'); // 'dashboard', 'exams', 'students', 'questions', 'ai_hub', 'reports', 'import'
  const [studentTab, setStudentTab] = useState('dashboard'); // 'dashboard', 'instructions', 'exam', 'result'

  // Dashboard & Lookup Data
  const [stats, setStats] = useState({ exams_count: 0, students_count: 0, questions_count: 0, active_students_count: 0 });
  const [examLookup, setExamLookup] = useState([]);
  const [sectionLookup, setSectionLookup] = useState([]);

  // CRUD Data State
  const [exams, setExams] = useState([]);
  const [students, setStudents] = useState([]);
  const [questions, setQuestions] = useState([]);
  const [selectedExamId, setSelectedExamId] = useState('');
  const [questionFilters, setQuestionFilters] = useState({ query: '', difficulty: '' });

  // Reporting State
  const [studentResults, setStudentResults] = useState([]);
  const [examSummaries, setExamSummaries] = useState([]);

  // AI generation states
  const [aiGenLevel, setAiGenLevel] = useState('Intermediate');
  const [aiGenCount, setAiGenCount] = useState(5);
  const [aiLogs, setAiLogs] = useState([]);
  const [aiLoading, setAiLoading] = useState(false);

  // Modals / Forms / Creating State
  const [showExamModal, setShowExamModal] = useState(false);
  const [editingExam, setEditingExam] = useState(null);
  const [examForm, setExamForm] = useState({ code: '', title: '', description: '', subject: 'English', time_limit_minutes: 30, min_questions: 20, max_questions: 20, passing_score: 0.0 });

  const [showStudentModal, setShowStudentModal] = useState(false);
  const [editingStudent, setEditingStudent] = useState(null);
  const [studentForm, setStudentForm] = useState({ student_code: '', full_name: '', password: '', email: '', phone: '', is_active: true });

  const [showQuestionModal, setShowQuestionModal] = useState(false);
  const [editingQuestion, setEditingQuestion] = useState(null);
  const [questionForm, setQuestionForm] = useState({
    exam_id: '',
    section_id: '',
    stem_text: '',
    category_name: 'Grammar',
    difficulty_level: 1,
    explanation_text: '',
    marks: 1.0,
    is_active: true,
    options: [
      { key: 'A', text: '', is_correct: true },
      { key: 'B', text: '', is_correct: false },
      { key: 'C', text: '', is_correct: false },
      { key: 'D', text: '', is_correct: false }
    ]
  });

  // Import State
  const [importFile, setImportFile] = useState(null);
  const [importExamId, setImportExamId] = useState('');
  const [importSectionId, setImportSectionId] = useState('');
  const [importPreview, setImportPreview] = useState(null);
  const [importSuccessMsg, setImportSuccessMsg] = useState('');
  const [importLoading, setImportLoading] = useState(false);

  // Student Exam State
  const [availableExams, setAvailableExams] = useState([]);
  const [activeInstructions, setActiveInstructions] = useState(null);
  const [examSession, setExamSession] = useState(null);
  const [selectedOptionId, setSelectedOptionId] = useState(null);
  const [timer, setTimer] = useState(0);
  const [examScorecard, setExamScorecard] = useState(null);
  const [examStartLoading, setExamStartLoading] = useState(false);

  // Custom public student states
  const [studentLookup, setStudentLookup] = useState([]);
  const [attemptsHistory, setAttemptsHistory] = useState([]);
  const [showStudentSelectModal, setShowStudentSelectModal] = useState(false);
  const [targetExamId, setTargetExamId] = useState('');
  const [studentNameInput, setStudentNameInput] = useState('');
  const [activeCandidate, setActiveCandidate] = useState(null);
  const [showAdminLogin, setShowAdminLogin] = useState(false);

  // Helper fetch wrapper
  const fetchAPI = async (endpoint, options = {}) => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers,
    });
    if (!response.ok) {
      let err;
      try {
        err = await response.json();
      } catch (e) {
        throw new Error(`API request failed with status ${response.status}`);
      }
      
      let errorMsg = 'API request failed';
      if (err && err.detail) {
        if (typeof err.detail === 'string') {
          errorMsg = err.detail;
        } else if (Array.isArray(err.detail)) {
          errorMsg = err.detail.map(d => {
            const path = d.loc ? d.loc.join('.') : '';
            return `${path ? path + ': ' : ''}${d.msg || JSON.stringify(d)}`;
          }).join('\n');
        } else {
          errorMsg = JSON.stringify(err.detail);
        }
      }
      throw new Error(errorMsg);
    }
    return response.json();
  };

  // Auth Effects
  useEffect(() => {
    if (token) {
      fetchAPI('/auth/me')
        .then(data => {
          setUser(data);
          if (data.role === 'admin') {
            setAdminTab('dashboard');
            loadAdminDashboard();
          }
        })
        .catch(err => {
          handleLogout();
        });
    }
  }, [token]);

  // Load public student portal data
  useEffect(() => {
    if (!user || user.role !== 'admin') {
      loadStudentDashboard();
    }
  }, [user]);

  // Timer Countdown Effect
  useEffect(() => {
    if (examSession && timer > 0 && !examSession.is_complete) {
      const interval = setInterval(() => {
        setTimer(prev => {
          if (prev <= 1) {
            clearInterval(interval);
            handleFinishExam(examSession.attempt_id);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
      return () => clearInterval(interval);
    }
  }, [examSession, timer]);

  // Auth Operations
  const handleLogin = async (e) => {
    e.preventDefault();
    setAuthError('');
    try {
      const data = await fetchAPI('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ username, password, role: 'admin' }),
      });
      localStorage.setItem('exam_token', data.session_id);
      setToken(data.session_id);
      setUser({
        id: data.principal_id,
        role: data.principal_type,
        username: data.username,
        display_name: data.display_name,
      });
      setUsername('');
      setPassword('');
      setShowAdminLogin(false);
    } catch (err) {
      setAuthError(err.message);
    }
  };

  const handleLogout = () => {
    if (token) {
      fetchAPI('/auth/logout', { method: 'POST' }).catch(() => {});
    }
    localStorage.removeItem('exam_token');
    setToken('');
    setUser(null);
    setExamSession(null);
    setExamScorecard(null);
  };

  // Loaders
  const loadAdminDashboard = async () => {
    try {
      const statsData = await fetchAPI('/admin/dashboard');
      setStats(statsData);
    } catch (err) {
      console.error(err);
    }
  };

  const loadExams = async () => {
    try {
      const data = await fetchAPI('/admin/exams');
      setExams(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadStudents = async () => {
    try {
      const data = await fetchAPI('/admin/students');
      setStudents(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadQuestions = async (examId) => {
    if (!examId) return;
    try {
      let url = `/admin/questions?exam_id=${examId}`;
      if (questionFilters.query) url += `&query=${encodeURIComponent(questionFilters.query)}`;
      if (questionFilters.difficulty) url += `&difficulty_level=${questionFilters.difficulty}`;
      const data = await fetchAPI(url);
      setQuestions(data);
    } catch (err) {
      console.error(err);
    }
  };

  const loadReports = async () => {
    try {
      const rData = await fetchAPI('/admin/reports/student-results');
      setStudentResults(rData);
      const sData = await fetchAPI('/admin/reports/exam-summaries');
      setExamSummaries(sData);
    } catch (err) {
      console.error(err);
    }
  };

  const loadLookups = async () => {
    try {
      const data = await fetchAPI('/admin/exams/lookup');
      setExamLookup(data);
      if (data.length > 0) {
        setImportExamId(data[0].id);
        loadSectionLookup(data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadSectionLookup = async (examId) => {
    if (!examId) return;
    try {
      const data = await fetchAPI(`/admin/exams/${examId}/sections/lookup`);
      setSectionLookup(data);
      if (data.length > 0) {
        setImportSectionId(data[0].id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadStudentDashboard = async () => {
    try {
      const examsData = await fetchAPI('/student/exams');
      setAvailableExams(examsData);
      
      const lookupData = await fetchAPI('/student/lookup');
      setStudentLookup(lookupData);
      
      const historyData = await fetchAPI('/student/attempts/history');
      setAttemptsHistory(historyData);
    } catch (err) {
      console.error(err);
    }
  };

  // Switch Admin Tabs
  const handleAdminTabChange = (tab) => {
    setAdminTab(tab);
    if (tab === 'dashboard') loadAdminDashboard();
    if (tab === 'exams') loadExams();
    if (tab === 'students') loadStudents();
    if (tab === 'questions') {
      loadLookups();
      setQuestions([]);
      setSelectedExamId('');
    }
    if (tab === 'import') {
      loadLookups();
      setImportPreview(null);
      setImportSuccessMsg('');
    }
    if (tab === 'reports') loadReports();
  };

  // Exam CRUD operations
  const handleOpenExamCreate = () => {
    setEditingExam(null);
    setExamForm({ code: '', title: '', description: '', subject: 'English', time_limit_minutes: 30, min_questions: 20, max_questions: 20, passing_score: 0.0 });
    setShowExamModal(true);
  };

  const handleOpenExamEdit = (exam) => {
    setEditingExam(exam);
    setExamForm({
      code: exam.code,
      title: exam.title,
      description: exam.description || '',
      subject: exam.subject,
      time_limit_minutes: exam.time_limit_minutes,
      min_questions: exam.min_questions,
      max_questions: exam.max_questions,
      passing_score: exam.passing_score
    });
    setShowExamModal(true);
  };

  const handleSaveExam = async (e) => {
    e.preventDefault();
    try {
      if (editingExam) {
        await fetchAPI(`/admin/exams/${editingExam.exam_id}`, {
          method: 'PUT',
          body: JSON.stringify(examForm),
        });
      } else {
        await fetchAPI('/admin/exams', {
          method: 'POST',
          body: JSON.stringify(examForm),
        });
      }
      setShowExamModal(false);
      loadExams();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteExam = async (examId) => {
    if (!window.confirm("Are you sure you want to delete this exam?")) return;
    try {
      await fetchAPI(`/admin/exams/${examId}`, { method: 'DELETE' });
      loadExams();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleActivateExam = async (exam, status) => {
    try {
      await fetchAPI(`/admin/exams/${exam.exam_id}`, {
        method: 'PUT',
        body: JSON.stringify({ status }),
      });
      loadExams();
    } catch (err) {
      alert(err.message);
    }
  };

  // Student CRUD operations
  const handleOpenStudentCreate = () => {
    setEditingStudent(null);
    setStudentForm({ student_code: '', full_name: '', password: '', email: '', phone: '', is_active: true });
    setShowStudentModal(true);
  };

  const handleOpenStudentEdit = (student) => {
    setEditingStudent(student);
    setStudentForm({
      student_code: student.student_code,
      full_name: student.full_name,
      password: '',
      email: student.email || '',
      phone: student.phone || '',
      is_active: student.is_active
    });
    setShowStudentModal(true);
  };

  const handleSaveStudent = async (e) => {
    e.preventDefault();
    try {
      if (editingStudent) {
        await fetchAPI(`/admin/students/${editingStudent.student_id}`, {
          method: 'PUT',
          body: JSON.stringify(studentForm),
        });
      } else {
        await fetchAPI('/admin/students', {
          method: 'POST',
          body: JSON.stringify(studentForm),
        });
      }
      setShowStudentModal(false);
      loadStudents();
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteStudent = async (studentId) => {
    if (!window.confirm("Are you sure you want to delete this student?")) return;
    try {
      await fetchAPI(`/admin/students/${studentId}`, { method: 'DELETE' });
      loadStudents();
    } catch (err) {
      alert(err.message);
    }
  };

  // Question CRUD operations
  const handleOpenQuestionCreate = async () => {
    if (!selectedExamId) {
      alert("Please select an exam first.");
      return;
    }
    const sections = await fetchAPI(`/admin/exams/${selectedExamId}/sections/lookup`);
    if (sections.length === 0) {
      alert("This exam has no sections to add questions to.");
      return;
    }
    setEditingQuestion(null);
    setQuestionForm({
      exam_id: selectedExamId,
      section_id: sections[0].id,
      stem_text: '',
      category_name: 'Grammar',
      difficulty_level: 1,
      explanation_text: '',
      marks: 1.0,
      is_active: true,
      options: [
        { key: 'A', text: '', is_correct: true },
        { key: 'B', text: '', is_correct: false },
        { key: 'C', text: '', is_correct: false },
        { key: 'D', text: '', is_correct: false }
      ]
    });
    setShowQuestionModal(true);
  };

  const handleOpenQuestionEdit = async (q) => {
    setEditingQuestion(q);
    setQuestionForm({
      exam_id: q.exam_id,
      section_id: q.section_id,
      stem_text: q.stem_text,
      category_name: q.category_name || 'Grammar',
      difficulty_level: q.difficulty_level,
      explanation_text: q.explanation_text || '',
      marks: q.marks,
      is_active: q.is_active,
      options: q.options.map(opt => ({
        key: opt.key,
        text: opt.text,
        is_correct: opt.is_correct
      }))
    });
    setShowQuestionModal(true);
  };

  const handleSaveQuestion = async (e) => {
    e.preventDefault();
    try {
      if (editingQuestion) {
        await fetchAPI(`/admin/questions/${editingQuestion.question_id}`, {
          method: 'PUT',
          body: JSON.stringify(questionForm),
        });
      } else {
        await fetchAPI('/admin/questions', {
          method: 'POST',
          body: JSON.stringify(questionForm),
        });
      }
      setShowQuestionModal(false);
      loadQuestions(selectedExamId);
    } catch (err) {
      alert(err.message);
    }
  };

  const handleDeleteQuestion = async (questionId) => {
    if (!window.confirm("Are you sure you want to delete this question?")) return;
    try {
      await fetchAPI(`/admin/questions/${questionId}`, { method: 'DELETE' });
      loadQuestions(selectedExamId);
    } catch (err) {
      alert(err.message);
    }
  };

  // AI generation operations
  const handleAIGenerate = async (e) => {
    e.preventDefault();
    if (!selectedExamId) {
      alert("Please select a target CEFR Level first.");
      return;
    }
    let targetSectionId = '';
    try {
      const sections = await fetchAPI(`/admin/exams/${selectedExamId}/sections/lookup`);
      if (sections.length === 0) {
        alert("Selected exam has no active sections.");
        return;
      }
      targetSectionId = sections[0].id;
    } catch (err) {
      alert("Error finding section lookup: " + err.message);
      return;
    }

    setAiLoading(true);
    setAiLogs(prev => [...prev, `[INIT] Triggering AI generation run for CEFR level: ${aiGenLevel} (Qty: ${aiGenCount})...`]);
    try {
      const data = await fetchAPI('/admin/ai/generate', {
        method: 'POST',
        body: JSON.stringify({
          exam_id: selectedExamId,
          section_id: targetSectionId,
          level_name: aiGenLevel,
          count: parseInt(aiGenCount) || 5
        })
      });
      setAiLogs(prev => [
        ...prev,
        `[SUCCESS] Mode: ${data.mode}`,
        `[SUCCESS] Ingested verified questions: ${data.imported_count}`,
        ...data.logs.map(l => `[LOG] ${l}`),
        ...data.issues.map(i => `[WARNING] ${i}`),
        `[FINISH] Batch ingestion sequence complete.`
      ]);
      loadAdminDashboard();
    } catch (err) {
      setAiLogs(prev => [...prev, `[ERROR] Fail: ${err.message}`]);
    } finally {
      setAiLoading(false);
    }
  };

  // Question Import operations
  const handleImportFileChange = (e) => {
    setImportFile(e.target.files[0]);
  };

  const handleImportPreview = async (e) => {
    e.preventDefault();
    if (!importFile) {
      alert("Please choose a file first.");
      return;
    }
    setImportLoading(true);
    setImportSuccessMsg('');
    setImportPreview(null);
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE}/admin/questions/import/preview`, {
        method: 'POST',
        headers,
        body: formData,
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Preview import failed');
      }
      const report = await response.json();
      setImportPreview(report);
    } catch (err) {
      alert(err.message);
    } finally {
      setImportLoading(false);
    }
  };

  const handleImportCommit = async () => {
    if (!importFile || !importExamId || !importSectionId) {
      alert("Missing file or target exam/section parameters.");
      return;
    }
    setImportLoading(true);
    setImportSuccessMsg('');
    try {
      const formData = new FormData();
      formData.append('file', importFile);
      formData.append('exam_id', importExamId);
      formData.append('section_id', importSectionId);
      const headers = {};
      if (token) {
        headers['Authorization'] = `Bearer ${token}`;
      }
      const response = await fetch(`${API_BASE}/admin/questions/import/commit`, {
        method: 'POST',
        headers,
        body: formData,
      });
      if (!response.ok) {
        const err = await response.json();
        throw new Error(err.detail || 'Commit import failed');
      }
      const data = await response.json();
      setImportSuccessMsg(`Import successful: Added ${data.imported_count} questions.`);
      setImportPreview(null);
      setImportFile(null);
    } catch (err) {
      alert(err.message);
    } finally {
      setImportLoading(false);
    }
  };

  // Student Exam Operations
  const handleRequestExamInstructions = async (examId) => {
    try {
      const data = await fetchAPI(`/student/exams/${examId}/instructions`);
      setActiveInstructions(data);
      setStudentTab('instructions');
    } catch (err) {
      alert(err.message);
    }
  };

  const handleStartExam = async (examId) => {
    if (!studentNameInput.trim()) {
      alert("Please enter your name to proceed.");
      return;
    }
    setExamStartLoading(true);
    try {
      const data = await fetchAPI(`/student/exams/${examId}/start`, {
        method: 'POST',
        body: JSON.stringify({ student_name: studentNameInput.trim() })
      });
      setExamSession(data);
      setTimer(activeInstructions.time_limit_minutes * 60);
      setSelectedOptionId(null);
      setActiveCandidate({
        student_id: data.student_id,
        full_name: data.student_name,
        student_code: data.student_code
      });
      setStudentTab('exam');
    } catch (err) {
      alert(err.message);
    } finally {
      setExamStartLoading(false);
    }
  };

  const handleExamClick = (examId) => {
    setTargetExamId(examId);
    setStudentNameInput('');
    setShowStudentSelectModal(true);
  };

  const handleStudentSelectProceed = () => {
    if (!studentNameInput.trim()) {
      alert("Please enter your name.");
      return;
    }
    setShowStudentSelectModal(false);
    handleRequestExamInstructions(targetExamId);
  };

  const handleSubmitAnswerAndNext = async () => {
    if (!selectedOptionId) {
      alert("Please select an option before moving to the next question.");
      return;
    }
    try {
      const data = await fetchAPI(`/student/attempts/${examSession.attempt_id}/submit-answer`, {
        method: 'POST',
        body: JSON.stringify({
          question_id: examSession.current_question.question_id,
          selected_option_id: selectedOptionId
        })
      });
      setExamSession(data);
      setSelectedOptionId(null);
      if (data.is_complete || !data.current_question) {
        handleFinishExam(data.attempt_id);
      }
    } catch (err) {
      alert(err.message);
    }
  };

  const handleFinishExam = async (attemptId) => {
    try {
      const data = await fetchAPI(`/student/attempts/${attemptId}/finish`, { method: 'POST' });
      setExamScorecard(data);
      setExamSession(null);
      setStudentTab('result');
      loadStudentDashboard();
    } catch (err) {
      alert(err.message);
    }
  };

  // Render Functions
  if (user && user.role === 'admin') {
    return (
      <div className="app-container">
        <div className="sidebar">
          <div className="sidebar-brand">Lead The Way</div>
          <div className="sidebar-nav">
            <button className={`nav-item ${adminTab === 'dashboard' ? 'active' : ''}`} onClick={() => handleAdminTabChange('dashboard')}>
              Dashboard
            </button>
            <button className={`nav-item ${adminTab === 'exams' ? 'active' : ''}`} onClick={() => handleAdminTabChange('exams')}>
              Exam Settings
            </button>
            <button className={`nav-item ${adminTab === 'students' ? 'active' : ''}`} onClick={() => handleAdminTabChange('students')}>
              Students List
            </button>
            <button className={`nav-item ${adminTab === 'questions' ? 'active' : ''}`} onClick={() => handleAdminTabChange('questions')}>
              Question Bank
            </button>
            <button className={`nav-item ${adminTab === 'import' ? 'active' : ''}`} onClick={() => handleAdminTabChange('import')}>
              DOCX Import Wizard
            </button>
            <button className={`nav-item ${adminTab === 'reports' ? 'active' : ''}`} onClick={() => handleAdminTabChange('reports')}>
              Reports & Logs
            </button>
          </div>
          <div className="sidebar-footer">
            <div className="user-badge">
              Logged in as:
              <strong>{user.display_name}</strong>
              <span style={{ fontSize: '0.8rem', color: 'var(--primary)' }}>({user.role.toUpperCase()})</span>
            </div>
            <button className="btn btn-secondary" style={{ padding: '8px' }} onClick={handleLogout}>Sign Out</button>
          </div>
        </div>

        <div className="main-content">
          {adminTab === 'dashboard' && (
            <div>
              <div className="screen-header">
                <div>
                  <h2>Administrator Dashboard</h2>
                  <p>Overview stats for active CEFR English levels</p>
                </div>
              </div>

              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">Active CEFR Levels</div>
                  <div className="metric-value">{stats.exams_count}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Registered Students</div>
                  <div className="metric-value">{stats.students_count}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Active Candidates</div>
                  <div className="metric-value">{stats.active_students_count}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Total Questions Pool</div>
                  <div className="metric-value">{stats.questions_count}</div>
                </div>
              </div>

              <div className="card">
                <h3>Welcome back, Administrator</h3>
                <p style={{ marginTop: '12px', color: 'var(--text-secondary)' }}>
                  Use the navigation panel on the left to set up exam constraints, register new candidates, audit the question databanks, parse new examinations via word doc files, or download student score report listings.
                </p>
              </div>
            </div>
          )}



          {adminTab === 'exams' && (
            <div>
              <div className="screen-header">
                <div>
                  <h2>Exam Configuration</h2>
                  <p>Configure parameters, duration, and thresholds for English assessment levels</p>
                </div>
                <button className="btn btn-primary" onClick={handleOpenExamCreate}>+ Create Level</button>
              </div>

              <div className="card table-container">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Code</th>
                      <th>Title</th>
                      <th>Subject</th>
                      <th>Time Limit</th>
                      <th>Questions Range</th>
                      <th>Passing Score</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {exams.map((ex) => (
                      <tr key={ex.exam_id}>
                        <td><strong>{ex.code}</strong></td>
                        <td>{ex.title}</td>
                        <td>{ex.subject}</td>
                        <td>{ex.time_limit_minutes} mins</td>
                        <td>{ex.min_questions} - {ex.max_questions} items</td>
                        <td>{ex.passing_score} %</td>
                        <td>
                          <span className={`badge ${ex.status === 'active' ? 'badge-active' : 'badge-draft'}`}>
                            {ex.status}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => handleOpenExamEdit(ex)}>Edit</button>
                            {ex.status === 'draft' ? (
                              <button className="btn btn-primary" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => handleActivateExam(ex, 'active')}>Activate</button>
                            ) : (
                              <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => handleActivateExam(ex, 'draft')}>Draft</button>
                            )}
                            <button className="btn btn-danger" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => handleDeleteExam(ex.exam_id)}>Delete</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {showExamModal && (
                <div className="modal-overlay">
                  <div className="modal-content">
                    <h3>{editingExam ? 'Edit Exam Setting' : 'Create New Exam'}</h3>
                    <form onSubmit={handleSaveExam} style={{ marginTop: '20px' }}>
                      <div className="form-row">
                        <div className="form-group">
                          <label>Exam Code</label>
                          <input
                            className="form-control"
                            type="text"
                            placeholder="e.g. EX-101"
                            value={examForm.code}
                            onChange={(e) => setExamForm({ ...examForm, code: e.target.value })}
                            required
                            disabled={!!editingExam}
                          />
                        </div>
                        <div className="form-group">
                          <label>Subject</label>
                          <input
                            className="form-control"
                            type="text"
                            placeholder="e.g. English"
                            value={examForm.subject}
                            onChange={(e) => setExamForm({ ...examForm, subject: e.target.value })}
                            required
                          />
                        </div>
                      </div>

                      <div className="form-group">
                        <label>Title</label>
                        <input
                          className="form-control"
                          type="text"
                          placeholder="e.g. Level B2 Advanced English Grammar"
                          value={examForm.title}
                          onChange={(e) => setExamForm({ ...examForm, title: e.target.value })}
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label>Description</label>
                        <textarea
                          className="form-control"
                          rows="3"
                          placeholder="Optional explanation..."
                          value={examForm.description}
                          onChange={(e) => setExamForm({ ...examForm, description: e.target.value })}
                        />
                      </div>

                      <div className="form-row">
                        <div className="form-group">
                          <label>Duration (Minutes)</label>
                          <input
                            className="form-control"
                            type="number"
                            value={examForm.time_limit_minutes}
                            onChange={(e) => setExamForm({ ...examForm, time_limit_minutes: parseInt(e.target.value) || 30 })}
                            min="1"
                            required
                          />
                        </div>
                        <div className="form-group">
                          <label>Passing Score (%)</label>
                          <input
                            className="form-control"
                            type="number"
                            value={examForm.passing_score}
                            onChange={(e) => setExamForm({ ...examForm, passing_score: parseFloat(e.target.value) || 0.0 })}
                            min="0"
                            max="100"
                            required
                          />
                        </div>
                      </div>

                      <div className="form-row">
                        <div className="form-group">
                          <label>Min Questions</label>
                          <input
                            className="form-control"
                            type="number"
                            value={examForm.min_questions}
                            onChange={(e) => setExamForm({ ...examForm, min_questions: parseInt(e.target.value) || 20 })}
                            min="20"
                            required
                          />
                        </div>
                        <div className="form-group">
                          <label>Max Questions</label>
                          <input
                            className="form-control"
                            type="number"
                            value={examForm.max_questions}
                            onChange={(e) => setExamForm({ ...examForm, max_questions: parseInt(e.target.value) || 20 })}
                            min="20"
                            required
                          />
                        </div>
                      </div>

                      <div className="modal-actions">
                        <button type="button" className="btn btn-secondary" onClick={() => setShowExamModal(false)}>Cancel</button>
                        <button type="submit" className="btn btn-primary">Save Settings</button>
                      </div>
                    </form>
                  </div>
                </div>
              )}
            </div>
          )}

          {adminTab === 'students' && (
            <div>
              <div className="screen-header">
                <div>
                  <h2>Student Management</h2>
                  <p>Register, update, and manage student credentials</p>
                </div>
                <button className="btn btn-primary" onClick={handleOpenStudentCreate}>+ Add Student</button>
              </div>

              <div className="card table-container">
                <table className="custom-table">
                  <thead>
                    <tr>
                      <th>Student Code</th>
                      <th>Full Name</th>
                      <th>Email Address</th>
                      <th>Phone</th>
                      <th>Status</th>
                      <th>Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {students.map((st) => (
                      <tr key={st.student_id}>
                        <td><strong>{st.student_code}</strong></td>
                        <td>{st.full_name}</td>
                        <td>{st.email || 'N/A'}</td>
                        <td>{st.phone || 'N/A'}</td>
                        <td>
                          <span className={`badge ${st.is_active ? 'badge-active' : 'badge-danger'}`}>
                            {st.is_active ? 'active' : 'inactive'}
                          </span>
                        </td>
                        <td>
                          <div style={{ display: 'flex', gap: '8px' }}>
                            <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => handleOpenStudentEdit(st)}>Edit</button>
                            <button className="btn btn-danger" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => handleDeleteStudent(st.student_id)}>Delete</button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {showStudentModal && (
                <div className="modal-overlay">
                  <div className="modal-content">
                    <h3>{editingStudent ? 'Edit Student Details' : 'Register New Student'}</h3>
                    <form onSubmit={handleSaveStudent} style={{ marginTop: '20px' }}>
                      <div className="form-group">
                        <label>Student Code (ID)</label>
                        <input
                          className="form-control"
                          type="text"
                          placeholder="e.g. student1"
                          value={studentForm.student_code}
                          onChange={(e) => setStudentForm({ ...studentForm, student_code: e.target.value })}
                          required
                          disabled={!!editingStudent}
                        />
                      </div>

                      <div className="form-group">
                        <label>Full Name</label>
                        <input
                          className="form-control"
                          type="text"
                          placeholder="e.g. Sample Student"
                          value={studentForm.full_name}
                          onChange={(e) => setStudentForm({ ...studentForm, full_name: e.target.value })}
                          required
                        />
                      </div>

                      <div className="form-group">
                        <label>Password {editingStudent ? '(Leave blank to keep current)' : ''}</label>
                        <input
                          className="form-control"
                          type="password"
                          placeholder="••••••••"
                          value={studentForm.password}
                          onChange={(e) => setStudentForm({ ...studentForm, password: e.target.value })}
                          required={!editingStudent}
                        />
                      </div>

                      <div className="form-group">
                        <label>Email Address</label>
                        <input
                          className="form-control"
                          type="email"
                          placeholder="e.g. user@local.exam"
                          value={studentForm.email}
                          onChange={(e) => setStudentForm({ ...studentForm, email: e.target.value })}
                        />
                      </div>

                      <div className="form-group">
                        <label>Phone Number</label>
                        <input
                          className="form-control"
                          type="text"
                          placeholder="Optional phone..."
                          value={studentForm.phone}
                          onChange={(e) => setStudentForm({ ...studentForm, phone: e.target.value })}
                        />
                      </div>

                      <div className="form-group" style={{ flexDirection: 'row', alignItems: 'center', gap: '8px' }}>
                        <input
                          type="checkbox"
                          id="is_active"
                          checked={studentForm.is_active}
                          onChange={(e) => setStudentForm({ ...studentForm, is_active: e.target.checked })}
                        />
                        <label htmlFor="is_active">Account is active</label>
                      </div>

                      <div className="modal-actions">
                        <button type="button" className="btn btn-secondary" onClick={() => setShowStudentModal(false)}>Cancel</button>
                        <button type="submit" className="btn btn-primary">Save Student</button>
                      </div>
                    </form>
                  </div>
                </div>
              )}
            </div>
          )}

          {adminTab === 'questions' && (
            <div>
              <div className="screen-header">
                <div>
                  <h2>Question Bank Manager</h2>
                  <p>Create and edit questions, select difficulty, and map options</p>
                </div>
                <button className="btn btn-primary" onClick={handleOpenQuestionCreate}>+ Add Question</button>
              </div>

              <div className="card" style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'center' }}>
                <div style={{ flex: 1, minWidth: '240px' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Select Exam</label>
                  <select
                    className="form-control"
                    value={selectedExamId}
                    onChange={(e) => {
                      setSelectedExamId(e.target.value);
                      loadQuestions(e.target.value);
                    }}
                  >
                    <option value="">-- Choose Exam --</option>
                    {examLookup.map((e) => (
                      <option key={e.id} value={e.id}>{e.label}</option>
                    ))}
                  </select>
                </div>

                <div style={{ width: '180px' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Difficulty</label>
                  <select
                    className="form-control"
                    value={questionFilters.difficulty}
                    onChange={(e) => setQuestionFilters({ ...questionFilters, difficulty: e.target.value })}
                  >
                    <option value="">All</option>
                    <option value="1">Easy (Level 1)</option>
                    <option value="2">Medium (Level 2)</option>
                    <option value="3">Hard (Level 3)</option>
                  </select>
                </div>

                <div style={{ flex: 2, minWidth: '280px' }}>
                  <label style={{ fontSize: '0.85rem', color: 'var(--text-secondary)', display: 'block', marginBottom: '6px' }}>Search Text</label>
                  <input
                    className="form-control"
                    type="text"
                    placeholder="Search question text..."
                    value={questionFilters.query}
                    onChange={(e) => setQuestionFilters({ ...questionFilters, query: e.target.value })}
                  />
                </div>

                <div style={{ alignSelf: 'flex-end' }}>
                  <button className="btn btn-secondary" onClick={() => loadQuestions(selectedExamId)}>Search</button>
                </div>
              </div>

              {selectedExamId ? (
                <div className="card table-container">
                  {questions.length === 0 ? (
                    <p style={{ textAlign: 'center', color: 'var(--text-muted)' }}>No questions found.</p>
                  ) : (
                    <table className="custom-table">
                      <thead>
                        <tr>
                          <th>Ref</th>
                          <th>Question stem</th>
                          <th>Category</th>
                          <th>Difficulty</th>
                          <th>Options (Correct)</th>
                          <th>Marks</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {questions.map((q) => (
                          <tr key={q.question_id}>
                            <td><span style={{ fontSize: '0.85rem', fontFamily: 'monospace' }}>{q.external_ref}</span></td>
                            <td style={{ maxWidth: '350px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{q.stem_text}</td>
                            <td>{q.category_name || 'N/A'}</td>
                            <td>
                              <span style={{ fontWeight: 600 }}>
                                {q.difficulty_level === 1 ? '🟢 Easy (1)' : q.difficulty_level === 2 ? '🟡 Medium (2)' : '🔴 Hard (3)'}
                              </span>
                            </td>
                            <td>
                              {q.options.map(opt => (
                                <div key={opt.key} style={{ fontSize: '0.85rem', color: opt.is_correct ? 'var(--success)' : 'var(--text-muted)' }}>
                                  <strong>{opt.key}:</strong> {opt.text} {opt.is_correct && '✓'}
                                </div>
                              ))}
                            </td>
                            <td>{q.marks} pts</td>
                            <td>
                              <div style={{ display: 'flex', gap: '8px' }}>
                                <button className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => handleOpenQuestionEdit(q)}>Edit</button>
                                <button className="btn btn-danger" style={{ padding: '6px 12px', fontSize: '0.85rem' }} onClick={() => handleDeleteQuestion(q.question_id)}>Delete</button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  )}
                </div>
              ) : (
                <div className="card" style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '40px' }}>
                  Please select an exam to view and manage its question bank.
                </div>
              )}

              {showQuestionModal && (
                <div className="modal-overlay">
                  <div className="modal-content" style={{ maxWidth: '750px' }}>
                    <h3>{editingQuestion ? 'Edit Question' : 'Create New Question'}</h3>
                    <form onSubmit={handleSaveQuestion} style={{ marginTop: '20px' }}>
                      
                      <div className="form-row">
                        <div className="form-group">
                          <label>Target Section</label>
                          <select
                            className="form-control"
                            value={questionForm.section_id}
                            onChange={(e) => setQuestionForm({ ...questionForm, section_id: e.target.value })}
                            required
                          >
                            {sectionLookup.map(s => (
                              <option key={s.id} value={s.id}>{s.label}</option>
                            ))}
                          </select>
                        </div>
                        <div className="form-group">
                          <label>Category (Topic)</label>
                          <select
                            className="form-control"
                            value={questionForm.category_name}
                            onChange={(e) => setQuestionForm({ ...questionForm, category_name: e.target.value })}
                            required
                          >
                            <option value="Grammar">Grammar</option>
                            <option value="Vocabulary">Vocabulary</option>
                            <option value="Reading">Reading</option>
                          </select>
                        </div>
                      </div>

                      <div className="form-group">
                        <label>Question Text (Stem)</label>
                        <textarea
                          className="form-control"
                          rows="4"
                          placeholder="Type the question query..."
                          value={questionForm.stem_text}
                          onChange={(e) => setQuestionForm({ ...questionForm, stem_text: e.target.value })}
                          required
                        />
                      </div>

                      <div className="form-row">
                        <div className="form-group">
                          <label>Difficulty</label>
                          <select
                            className="form-control"
                            value={questionForm.difficulty_level}
                            onChange={(e) => setQuestionForm({ ...questionForm, difficulty_level: parseInt(e.target.value) || 1 })}
                          >
                            <option value="1">Easy (Level 1)</option>
                            <option value="2">Medium (Level 2)</option>
                            <option value="3">Hard (Level 3)</option>
                          </select>
                        </div>
                        <div className="form-group">
                          <label>Awarded Marks (Weight)</label>
                          <input
                            className="form-control"
                            type="number"
                            step="0.5"
                            value={questionForm.marks}
                            onChange={(e) => setQuestionForm({ ...questionForm, marks: parseFloat(e.target.value) || 1.0 })}
                            min="0.5"
                            required
                          />
                        </div>
                      </div>

                      <div className="form-group">
                        <label style={{ fontWeight: '600' }}>Question Multiple-Choice Options</label>
                        {questionForm.options.map((opt, idx) => (
                          <div key={opt.key} className="option-edit-row">
                            <span style={{ fontWeight: '700', width: '20px' }}>{opt.key}</span>
                            <input
                              className="form-control"
                              type="text"
                              placeholder={`Option text for ${opt.key}`}
                              value={opt.text}
                              onChange={(e) => {
                                const newOpts = [...questionForm.options];
                                newOpts[idx].text = e.target.value;
                                setQuestionForm({ ...questionForm, options: newOpts });
                              }}
                              required
                            />
                            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', whiteSpace: 'nowrap' }}>
                              <input
                                type="radio"
                                name="correct-opt-grp"
                                id={`is-correct-radio-${opt.key}`}
                                checked={opt.is_correct}
                                onChange={() => {
                                  const newOpts = questionForm.options.map((o, i) => ({
                                    ...o,
                                    is_correct: i === idx
                                  }));
                                  setQuestionForm({ ...questionForm, options: newOpts });
                                }}
                              />
                              <label htmlFor={`is-correct-radio-${opt.key}`} style={{ fontSize: '0.8rem' }}>Correct</label>
                            </div>
                          </div>
                        ))}
                      </div>

                      <div className="form-group">
                        <label>Explanation Text</label>
                        <textarea
                          className="form-control"
                          rows="2"
                          placeholder="Optional explanation shown on feedback review..."
                          value={questionForm.explanation_text}
                          onChange={(e) => setQuestionForm({ ...questionForm, explanation_text: e.target.value })}
                        />
                      </div>

                      <div className="modal-actions">
                        <button type="button" className="btn btn-secondary" onClick={() => setShowQuestionModal(false)}>Cancel</button>
                        <button type="submit" className="btn btn-primary">Save Question</button>
                      </div>
                    </form>
                  </div>
                </div>
              )}
            </div>
          )}

          {adminTab === 'import' && (
            <div>
              <div className="screen-header">
                <div>
                  <h2>DOCX Import Wizard</h2>
                  <p>Bulk import structured questions from Microsoft Word files</p>
                </div>
              </div>

              <div className="card" style={{ maxWidth: '680px' }}>
                <form onSubmit={handleImportPreview}>
                  <div className="form-group">
                    <label>Select Word DOCX Document</label>
                    <input
                      className="form-control"
                      type="file"
                      accept=".docx"
                      onChange={handleImportFileChange}
                      required
                    />
                  </div>

                  <div className="form-row">
                    <div className="form-group">
                      <label>Target Exam</label>
                      <select
                        className="form-control"
                        value={importExamId}
                        onChange={(e) => {
                          setImportExamId(e.target.value);
                          loadSectionLookup(e.target.value);
                        }}
                        required
                      >
                        {examLookup.map((e) => (
                          <option key={e.id} value={e.id}>{e.label}</option>
                        ))}
                      </select>
                    </div>

                    <div className="form-group">
                      <label>Target Section</label>
                      <select
                        className="form-control"
                        value={importSectionId}
                        onChange={(e) => setImportSectionId(e.target.value)}
                        required
                      >
                        {sectionLookup.map((s) => (
                          <option key={s.id} value={s.id}>{s.label}</option>
                        ))}
                      </select>
                    </div>
                  </div>

                  <div style={{ marginTop: '24px', display: 'flex', gap: '12px' }}>
                    <button type="submit" className="btn btn-secondary" disabled={importLoading}>
                      {importLoading ? 'Analyzing...' : 'Analyze & Preview'}
                    </button>
                    {importPreview && (
                      <button type="button" className="btn btn-primary" onClick={handleImportCommit} disabled={importLoading}>
                        {importLoading ? 'Importing...' : 'Commit Import'}
                      </button>
                    )}
                  </div>
                </form>

                {importSuccessMsg && (
                  <div style={{ marginTop: '24px', padding: '16px', background: 'var(--success-glow)', color: 'var(--success)', border: '1px solid var(--success)', borderRadius: 'var(--radius-sm)' }}>
                    {importSuccessMsg}
                  </div>
                )}
              </div>

              {importPreview && (
                <div>
                  <div className="card">
                    <h3>Import File Inspection</h3>
                    <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>
                      Questions parsed: <strong>{importPreview.parsed_questions.length}</strong> | Duplicate blocks: <strong>{importPreview.duplicates.length}</strong> | Structural issues: <strong>{importPreview.issues.length}</strong>
                    </p>

                    {importPreview.issues.length > 0 && (
                      <div className="issues-log">
                        <div style={{ fontWeight: 'bold', borderBottom: '1px solid var(--border)', paddingBottom: '6px', marginBottom: '8px' }}>Parsing Warnings / Validation Reports</div>
                        {importPreview.issues.map((issue, idx) => (
                          <div key={idx} className={issue.severity === 'ERROR' ? 'issue-error' : 'issue-warning'}>
                            [Item {issue.sequence_number || 'Global'}] {issue.message}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <div className="card table-container">
                    <h3>Parsed Questions Preview</h3>
                    <table className="custom-table" style={{ marginTop: '16px' }}>
                      <thead>
                        <tr>
                          <th>Sequence</th>
                          <th>Category</th>
                          <th>Question Stem</th>
                          <th>Difficulty</th>
                          <th>Options</th>
                        </tr>
                      </thead>
                      <tbody>
                        {importPreview.parsed_questions.map((pq) => (
                          <tr key={pq.sequence_number}>
                            <td>#{pq.sequence_number}</td>
                            <td>{pq.category || 'General'}</td>
                            <td>{pq.question_text}</td>
                            <td>{pq.difficulty || 'Medium'}</td>
                            <td>
                              {Object.entries(pq.options).map(([key, text]) => (
                                <div key={key} style={{ fontSize: '0.8rem', color: key === pq.correct_answer ? 'var(--success)' : 'var(--text-muted)' }}>
                                  <strong>{key}:</strong> {text} {key === pq.correct_answer && '✓'}
                                </div>
                              ))}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>
          )}

          {adminTab === 'reports' && (
            <div>
              <div className="screen-header">
                <div>
                  <h2>Reports & Analytics</h2>
                  <p>Check student performance lists and aggregated exam summaries</p>
                </div>
              </div>

              <div className="card table-container">
                <h3>Individual Student Attempts</h3>
                <div style={{ marginTop: '16px' }}>
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Student ID</th>
                        <th>Student Name</th>
                        <th>Exam Title</th>
                        <th>Score</th>
                        <th>Percentage</th>
                        <th>Completed Time</th>
                        <th>Result Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {studentResults.map((r) => (
                        <tr key={r.attempt_id}>
                          <td><strong>{r.student_code}</strong></td>
                          <td>{r.student_name}</td>
                          <td>{r.exam_title}</td>
                          <td>{r.score} / {r.total_questions} pts</td>
                          <td>{r.percentage.toFixed(2)} %</td>
                          <td>{r.completed_at_iso ? new Date(r.completed_at_iso).toLocaleString() : 'In Progress'}</td>
                          <td>
                            <span className={`badge ${r.status === 'passed' ? 'badge-active' : 'badge-danger'}`}>
                              {r.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="card table-container" style={{ marginTop: '32px' }}>
                <h3>Aggregated Exam Summaries</h3>
                <div style={{ marginTop: '16px' }}>
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Exam Code</th>
                        <th>Exam Title</th>
                        <th>Total Attempts</th>
                        <th>Completed</th>
                        <th>Average Score</th>
                        <th>Highest Score</th>
                        <th>Lowest Score</th>
                      </tr>
                    </thead>
                    <tbody>
                      {examSummaries.map((s) => (
                        <tr key={s.exam_id}>
                          <td><strong>{s.exam_code}</strong></td>
                          <td>{s.exam_title}</td>
                          <td>{s.total_attempts} attempts</td>
                          <td>{s.completed_attempts}</td>
                          <td>{s.average_score.toFixed(2)} pts ({s.average_percentage.toFixed(2)}%)</td>
                          <td>{s.highest_score} pts</td>
                          <td>{s.lowest_score} pts</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  // STUDENT VIEW RENDER
  return (
    <div className="app-container" style={{ display: 'block' }}>
      <nav style={{ background: 'hsla(230, 25%, 6%, 0.65)', borderBottom: '1px solid var(--border)', backdropFilter: 'blur(10px)', padding: '16px 40px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', position: 'sticky', top: 0, zIndex: 100 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '24px' }}>
          <span className="sidebar-brand" style={{ margin: 0, padding: 0 }}>Lead The Way</span>
          {studentTab !== 'exam' && (
            <button className="btn btn-secondary" style={{ padding: '6px 16px' }} onClick={() => { setStudentTab('dashboard'); setStudentNameInput(''); setActiveCandidate(null); }}>
              My Dashboard
            </button>
          )}
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginLeft: 'auto' }}>
          {activeCandidate ? (
            <div className="user-badge" style={{ textAlign: 'right' }}>
              Candidate: <strong>{activeCandidate.full_name}</strong>
              <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>ID: {activeCandidate.student_code}</span>
            </div>
          ) : (
            <div className="user-badge" style={{ textAlign: 'right' }}>
              <strong>Public Guest Portal</strong>
            </div>
          )}
          {studentTab !== 'exam' && (
            <button className="btn btn-secondary" style={{ padding: '8px 16px' }} onClick={() => setShowAdminLogin(true)}>Admin Login</button>
          )}
        </div>
      </nav>

      <div className="student-view-container">
        {studentTab === 'dashboard' && (
          <div>
            <div className="screen-header">
              <div>
                <h2>Student Assessment Portal</h2>
                <p>Select your English proficiency level from the CEFR categories below to begin your evaluation</p>
              </div>
            </div>

            <div className="dashboard-split-grid" style={{ marginTop: '24px' }}>
              {/* Left Column: Exams Cards */}
              <div>
                <div className="level-grid" style={{ marginTop: 0 }}>
                  {availableExams.map((e) => (
                    <div key={e.exam_id} className="level-card" onClick={() => handleExamClick(e.exam_id)}>
                      <div>
                        <span className="badge level-badge-cefr">{e.code}</span>
                        <h3 style={{ fontSize: '1.4rem', marginBottom: '10px' }}>{e.title}</h3>
                        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginBottom: '20px' }}>
                          {e.description || 'Evaluate your proficiency and grammar skills.'}
                        </p>
                      </div>
                      <div style={{ borderTop: '1px solid var(--border)', paddingTop: '16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                          ⏱ {e.time_limit_minutes} mins | 📑 {e.question_count} items
                        </span>
                        <span style={{ color: 'var(--primary)', fontWeight: 'bold', fontSize: '0.9rem' }}>
                          Start →
                        </span>
                      </div>
                    </div>
                  ))}
                </div>

                {availableExams.length === 0 && (
                  <div className="card" style={{ padding: '60px 20px', textAlign: 'center', color: 'var(--text-muted)' }}>
                    No active examinations are allocated currently. Please consult your administrator.
                  </div>
                )}
              </div>

              {/* Right Column: Highest Scorers Leaderboard */}
              <div className="card" style={{ margin: 0 }}>
                <h3 style={{ marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                  🏆 Highest Scorers Leaderboard
                </h3>
                {(() => {
                  const completedAttempts = attemptsHistory.filter(
                    (att) => att.status === 'passed' || att.status === 'failed'
                  );
                  const sortedScorers = [...completedAttempts].sort((a, b) => {
                    if (b.percentage !== a.percentage) {
                      return b.percentage - a.percentage;
                    }
                    return b.score - a.score;
                  });
                  const topAttempts = sortedScorers.slice(0, 5);

                  if (topAttempts.length === 0) {
                    return <p style={{ color: 'var(--text-muted)' }}>No completed attempts recorded yet.</p>;
                  }

                  return (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                      {topAttempts.map((att, index) => {
                        const rankColors = [
                          { bg: 'linear-gradient(135deg, #ffd700, #ffa500)', text: '#000', icon: '🥇' },
                          { bg: 'linear-gradient(135deg, #c0c0c0, #808080)', text: '#000', icon: '🥈' },
                          { bg: 'linear-gradient(135deg, #cd7f32, #8b4513)', text: '#fff', icon: '🥉' },
                          { bg: 'var(--border)', text: 'var(--text-secondary)', icon: '4' },
                          { bg: 'var(--border)', text: 'var(--text-secondary)', icon: '5' }
                        ];
                        const rankStyle = rankColors[index] || rankColors[4];

                        return (
                          <div
                            key={att.attempt_id}
                            style={{
                              display: 'flex',
                              alignItems: 'center',
                              justifyContent: 'space-between',
                              background: 'hsla(230, 25%, 10%, 0.4)',
                              border: '1px solid var(--border)',
                              borderRadius: 'var(--radius-sm)',
                              padding: '12px 16px',
                              transition: 'var(--transition)',
                            }}
                            className="leaderboard-item"
                          >
                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                              <div
                                style={{
                                  width: '32px',
                                  height: '32px',
                                  borderRadius: '50%',
                                  background: rankStyle.bg,
                                  color: rankStyle.text,
                                  display: 'flex',
                                  alignItems: 'center',
                                  justifyContent: 'center',
                                  fontWeight: 'bold',
                                  fontSize: '0.9rem',
                                  boxShadow: index < 3 ? '0 0 10px rgba(255,255,255,0.1)' : 'none'
                                }}
                              >
                                {rankStyle.icon}
                              </div>
                              <div>
                                <div style={{ fontWeight: 'bold', color: 'var(--text-primary)' }}>
                                  {att.student_name}
                                </div>
                                <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                  {att.exam_title}
                                </div>
                              </div>
                            </div>
                            <div style={{ textAlign: 'right' }}>
                              <div style={{ fontWeight: 'bold', color: 'var(--primary)', fontSize: '1.1rem' }}>
                                {att.percentage.toFixed(1)}%
                              </div>
                              <div style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>
                                {att.score} / {att.total_questions} pts
                              </div>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  );
                })()}
              </div>
            </div>

            {/* Attempts History Panel */}
            <div className="card" style={{ marginTop: '40px' }}>
              <h3 style={{ marginBottom: '16px' }}>Recent Exam Attempts</h3>
              {attemptsHistory.length === 0 ? (
                <p style={{ color: 'var(--text-muted)' }}>No exam attempts recorded yet.</p>
              ) : (
                <div className="table-container">
                  <table className="custom-table">
                    <thead>
                      <tr>
                        <th>Candidate Name</th>
                        <th>Exam Level</th>
                        <th>Score</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {attemptsHistory.slice(0, 10).map((att) => (
                        <tr key={att.attempt_id}>
                          <td><strong>{att.student_name}</strong></td>
                          <td>{att.exam_title || 'N/A'}</td>
                          <td>{att.score} / {att.total_questions} ({att.percentage.toFixed(0)}%)</td>
                          <td>
                            <span className={`badge ${att.status === 'passed' ? 'badge-active' : att.status === 'failed' ? 'badge-danger' : 'badge-draft'}`}>
                              {att.status.toUpperCase()}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {studentTab === 'instructions' && activeInstructions && (
          <div className="card" style={{ maxWidth: '750px', margin: '0 auto' }}>
            {examStartLoading ? (
              <div className="ai-loader-container">
                <div className="ai-spinner"></div>
                <h3 style={{ fontSize: '1.4rem', marginBottom: '8px' }}>Preparing Your Adaptive Exam</h3>
                <p style={{ color: 'var(--text-secondary)' }}>Our AI Agent is generating and validating unique questions for your attempt. Please wait a moment...</p>
              </div>
            ) : (
              <>
                <h2 style={{ fontSize: '1.8rem', borderBottom: '1px solid var(--border)', paddingBottom: '16px', marginBottom: '20px' }}>
                  Exam Instructions & Terms
                </h2>

                <div style={{ marginBottom: '24px' }}>
                  <h3>{activeInstructions.title}</h3>
                  <p style={{ color: 'var(--text-secondary)', marginTop: '8px' }}>{activeInstructions.description}</p>
                </div>

                <div style={{ background: 'hsla(230, 25%, 6%, 0.4)', border: '1px solid var(--border)', borderRadius: 'var(--radius-sm)', padding: '20px', marginBottom: '24px' }}>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '16px' }}>
                    <div>Subject: <strong>{activeInstructions.subject}</strong></div>
                    <div>Time Duration: <strong>{activeInstructions.time_limit_minutes} minutes</strong></div>
                    <div>Maximum Items: <strong>{activeInstructions.question_count} questions</strong></div>
                    <div>Format: <strong>Adaptive Progression</strong></div>
                  </div>
                </div>

                <div style={{ marginBottom: '32px' }}>
                  <h4 style={{ marginBottom: '12px' }}>Test Policy:</h4>
                  <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    {activeInstructions.instructions.map((inst, idx) => (
                      <li key={idx}>{inst}</li>
                    ))}
                  </ul>
                </div>

                <div style={{ display: 'flex', gap: '16px', justifyContent: 'flex-end' }}>
                  <button className="btn btn-secondary" onClick={() => { setStudentTab('dashboard'); setStudentNameInput(''); setActiveCandidate(null); }}>Back</button>
                  <button className="btn btn-primary" onClick={() => handleStartExam(activeInstructions.exam_id)}>
                    Start Examination
                  </button>
                </div>
              </>
            )}
          </div>
        )}

        {studentTab === 'exam' && examSession && examSession.current_question && (
          <div>
            <div className="exam-header">
              <div>
                <h2>{activeInstructions?.title}</h2>
                <p style={{ color: 'var(--text-muted)' }}>Category: {examSession.current_question.category_name || 'General'}</p>
              </div>
              <div className="timer-box">
                {Math.floor(timer / 60)}:{(timer % 60).toString().padStart(2, '0')}
              </div>
            </div>

            {/* Question numbers indicator list 1 to 20 */}
            <div className="question-navigation" style={{ display: 'flex', gap: '8px', flexWrap: 'wrap', marginBottom: '20px', justifyContent: 'center' }}>
              {Array.from({ length: examSession.current_question.total_questions }, (_, i) => {
                const qNum = i + 1;
                const isCurrent = qNum === examSession.current_question.sequence_number;
                const isAnswered = qNum < examSession.current_question.sequence_number;
                
                let bg = 'var(--bg-card)';
                let border = '1px solid var(--border)';
                let color = 'var(--text-secondary)';
                
                if (isCurrent) {
                  bg = 'var(--primary)';
                  border = '1px solid var(--primary)';
                  color = 'var(--bg-app)';
                } else if (isAnswered) {
                  bg = 'rgba(46, 213, 115, 0.15)';
                  border = '1px solid var(--success)';
                  color = 'var(--success)';
                }
                
                return (
                  <div
                    key={qNum}
                    style={{
                      width: '32px',
                      height: '32px',
                      borderRadius: '50%',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      fontWeight: 'bold',
                      fontSize: '0.85rem',
                      background: bg,
                      border: border,
                      color: color,
                      transition: 'all 0.2s ease',
                      boxShadow: isCurrent ? '0 0 10px var(--primary)' : 'none'
                    }}
                  >
                    {qNum}
                  </div>
                );
              })}
            </div>

            <div className="progress-header">
              <span>Question {examSession.current_question.sequence_number} of {examSession.current_question.total_questions}</span>
            </div>
            <div className="progress-bar-container">
              <div
                className="progress-bar-fill"
                style={{ width: `${(examSession.answered_questions / examSession.current_question.total_questions) * 100}%` }}
              ></div>
            </div>

            <div className="card">
              <div className="question-stem">{examSession.current_question.stem_text}</div>

              <div className="options-list">
                {examSession.current_question.options.map((option) => (
                  <button
                    key={option.option_id}
                    className={`option-btn ${selectedOptionId === option.option_id ? 'selected' : ''}`}
                    onClick={() => setSelectedOptionId(option.option_id)}
                  >
                    <div className="option-key-badge">{option.key}</div>
                    <div>{option.text}</div>
                  </button>
                ))}
              </div>

              <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '32px' }}>
                <button
                  className="btn btn-danger"
                  style={{ opacity: 0.6 }}
                  onClick={() => {
                    if (window.confirm("Submit exam now? Remaining questions will be marked as unanswered.")) {
                      handleFinishExam(examSession.attempt_id);
                    }
                  }}
                >
                  End Exam Early
                </button>
                <button className="btn btn-primary" onClick={handleSubmitAnswerAndNext}>
                  {examSession.current_question.sequence_number === examSession.current_question.total_questions
                    ? 'Submit & Finish'
                    : 'Submit & Next Question'}
                </button>
              </div>
            </div>
          </div>
        )}

        {studentTab === 'result' && examScorecard && (
          <div className="card" style={{ maxWidth: '640px', margin: '0 auto' }}>
            <div className="result-container">
              <div className={`result-badge ${examScorecard.percentage >= 33.0 ? 'passed' : 'failed'}`}>
                {examScorecard.percentage >= 33.0 ? 'PASSED' : 'FAILED'}
              </div>

              <h2 style={{ fontSize: '1.8rem', marginBottom: '8px' }}>Test Result Summary</h2>
              <p style={{ color: 'var(--text-muted)' }}>Exam: {examScorecard.exam_title}</p>

              {(() => {
                const inspiring = getInspiringWord(examScorecard.percentage);
                return (
                  <div className="inspiring-box" style={{ marginTop: '20px', padding: '16px', borderRadius: 'var(--radius-sm)', background: 'rgba(99, 102, 241, 0.08)', border: '1px dashed var(--primary)', textAlign: 'center' }}>
                    <h3 style={{ fontSize: '1.3rem', color: 'var(--primary)', marginBottom: '4px' }}>{inspiring.title}</h3>
                    <p style={{ color: 'var(--text-secondary)', fontSize: '0.95rem' }}>{inspiring.text}</p>
                  </div>
                );
              })()}

              <div className="result-score-grid">
                <div className="result-score-item">
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Total Questions</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 'bold' }}>{examScorecard.total_questions}</div>
                </div>
                <div className="result-score-item">
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Answered Correctly</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: 'var(--success)' }}>
                    {examScorecard.correct_answers} / {examScorecard.answered_questions}
                  </div>
                </div>
                <div className="result-score-item">
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Final Score</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 'bold' }}>{examScorecard.score.toFixed(1)} pts</div>
                </div>
                <div className="result-score-item">
                  <div style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Percentage Score</div>
                  <div style={{ fontSize: '1.6rem', fontWeight: 'bold', color: 'var(--primary)' }}>
                    {examScorecard.percentage.toFixed(1)} %
                  </div>
                </div>
              </div>

              {examScorecard.skills_breakdown && (
                <div className="skills-radar-box">
                  <div className="skills-radar-title">Diagnostic Sub-Skills Assessment</div>
                  {Object.entries(examScorecard.skills_breakdown).map(([skill, val]) => (
                    <div key={skill} className="skill-bar-row">
                      <div className="skill-bar-label">
                        <span>{skill}</span>
                        <span>{val}%</span>
                      </div>
                      <div className="skill-bar-outer">
                        <div className="skill-bar-inner" style={{ width: `${val}%` }}></div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <div style={{ marginTop: '40px' }}>
                <button className="btn btn-primary" onClick={() => { setStudentTab('dashboard'); setStudentNameInput(''); setActiveCandidate(null); }}>
                  Return to Dashboard
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Student Selection Modal */}
      {showStudentSelectModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3>Candidate Identification</h3>
            <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem', marginTop: '8px', marginBottom: '20px' }}>
              Please enter your full name to proceed to the examination instructions.
            </p>
            <div className="form-group">
              <label>Your Full Name</label>
              <input
                className="form-control"
                type="text"
                placeholder="e.g. John Doe"
                value={studentNameInput}
                onChange={(e) => setStudentNameInput(e.target.value)}
                required
              />
            </div>
            <div className="modal-actions" style={{ marginTop: '24px' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowStudentSelectModal(false)}>
                Cancel
              </button>
              <button type="button" className="btn btn-primary" onClick={handleStudentSelectProceed}>
                Proceed to Exam
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Admin Login Modal */}
      {showAdminLogin && (
        <div className="modal-overlay">
          <div className="modal-content" style={{ maxWidth: '400px' }}>
            <h3>Administrator Login</h3>
            {authError && (
              <div style={{ background: 'rgba(255, 71, 87, 0.1)', border: '1px solid var(--danger)', color: 'var(--danger)', padding: '12px', borderRadius: 'var(--radius-sm)', fontSize: '0.85rem', marginTop: '12px' }}>
                {authError}
              </div>
            )}
            <form onSubmit={handleLogin} style={{ marginTop: '20px' }}>
              <div className="form-group">
                <label>Username</label>
                <input
                  className="form-control"
                  type="text"
                  placeholder="Admin username"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  required
                />
              </div>
              <div className="form-group" style={{ marginTop: '16px' }}>
                <label>Password</label>
                <input
                  className="form-control"
                  type="password"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
              <div className="modal-actions" style={{ marginTop: '24px' }}>
                <button type="button" className="btn btn-secondary" onClick={() => {
                  setShowAdminLogin(false);
                  setAuthError('');
                }}>
                  Cancel
                </button>
                <button type="submit" className="btn btn-primary">
                  Sign In
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
