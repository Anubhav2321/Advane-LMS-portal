COUNT-UP ANIMATION                            //
    // ============================================= //
    
    function animateCount(el, target, duration) {
        let start = 0;
        const increment = target / (duration / 16);
        if (target === 0) return;
        const timer = setInterval(() => {
            start += increment;
            if (start >= target) {
                el.innerText = target;
                clearInterval(timer);
            } else {
                el.innerText = Math.floor(start);
            }
        }, 16);
    }

    document.querySelectorAll('.stat-number[data-count]').forEach(el => {
        const target = parseInt(el.dataset.count) || 0;
        animateCount(el, target, 1200);
    });

    // ============================================= //
    // CHART.JS INITIALIZATIONS                      //
    // ============================================= //

    const chartDefaults = {
        responsive: true,
        maintainAspectRatio: true,
        plugins: {
            legend: { display: false },
            tooltip: {
                backgroundColor: 'rgba(10, 10, 30, 0.9)',
                borderColor: 'rgba(108, 99, 255, 0.3)',
                borderWidth: 1,
                cornerRadius: 8,
                titleFont: { family: "'Inter', sans-serif", weight: 600 },
                bodyFont: { family: "'Inter', sans-serif" },
                padding: 12
            }
        }
    };

    // --- Daily Activity Line Chart ---
    const actCtx = document.getElementById('activityChart').getContext('2d');
    const actGrad = actCtx.createLinearGradient(0, 0, 0, 300);
    actGrad.addColorStop(0, 'rgba(108, 99, 255, 0.3)');
    actGrad.addColorStop(1, 'rgba(108, 99, 255, 0)');

    new Chart(actCtx, {
        type: 'line',
        data: {
            labels: ["15 Sep", "16 Sep"],
            datasets: [{
                label: 'Activities',
                data: [4, 9],
                borderColor: '#6C63FF',
                backgroundColor: actGrad,
                borderWidth: 2.5,
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointBackgroundColor: '#6C63FF',
                pointBorderColor: '#fff',
                pointBorderWidth: 1.5,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: '#fff',
                pointHoverBorderColor: '#6C63FF',
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            ...chartDefaults,
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
                    ticks: { color: '#5A5A7A', font: { size: 11 } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
                    ticks: { color: '#5A5A7A', font: { size: 11 } },
                    beginAtZero: true
                }
            },
            animation: {
                duration: 1500,
                easing: 'easeInOutQuart'
            }
        }
    });
    
    // --- Course Metrics Chart ---
    const cmCtx = document.getElementById('courseMetricsChart').getContext('2d');
    new Chart(cmCtx, {
        type: 'bar',
        data: {
            labels: ["Linux", "DSA", "Generative Ai", "Kotlin", "PostgreSQL", "TypeScript", "Git & GitHub", "Express Js", "AngularJS", "CSS 3", "DBMS", "Data Science", "Basic Dark web", "Advanced Excel", "Machine Learning"],
            datasets: [
                {
                    label: 'Avg Progress %',
                    data: [50.0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                    backgroundColor: 'rgba(0, 243, 255, 0.5)',
                    borderColor: 'rgba(0, 243, 255, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                },
                {
                    label: 'Completion Rate %',
                    data: [100.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    backgroundColor: 'rgba(0, 230, 118, 0.5)',
                    borderColor: 'rgba(0, 230, 118, 1)',
                    borderWidth: 1,
                    borderRadius: 4
                }
            ]
        },
        options: {
            ...chartDefaults,
            plugins: {
                legend: { display: true, labels: { color: '#A0A0B8' } },
                tooltip: chartDefaults.plugins.tooltip
            },
            scales: {
                x: { ticks: { color: '#5A5A7A', font: { size: 10 } } },
                y: { max: 100, ticks: { color: '#5A5A7A', callback: v => v + '%' } }
            }
        }
    });



    // --- Registration Bar Chart ---
    const regCtx = document.getElementById('registrationChart').getContext('2d');
    const regGrad = regCtx.createLinearGradient(0, 0, 0, 300);
    regGrad.addColorStop(0, 'rgba(0, 212, 255, 0.6)');
    regGrad.addColorStop(1, 'rgba(0, 212, 255, 0.05)');

    new Chart(regCtx, {
        type: 'bar',
        data: {
            labels: [],
            datasets: [{
                label: 'New Students',
                data: [],
                backgroundColor: regGrad,
                borderColor: 'rgba(0, 212, 255, 0.5)',
                borderWidth: 1,
                borderRadius: 6,
                borderSkipped: false,
                barThickness: 'flex',
                maxBarThickness: 30
            }]
        },
        options: {
            ...chartDefaults,
            scales: {
                x: {
                    grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
                    ticks: { color: '#5A5A7A', font: { size: 11 } }
                },
                y: {
                    grid: { color: 'rgba(255,255,255,0.03)', drawBorder: false },
                    ticks: { color: '#5A5A7A', font: { size: 11 }, stepSize: 1 },
                    beginAtZero: true
                }
            },
            animation: { duration: 1500, easing: 'easeInOutQuart' }
        }
    });

    // --- Breakdown Doughnut Chart ---
    const breakColors = [
        '#6C63FF', '#00D4FF', '#00E676', '#FF3366', '#FFB74D',
        '#A855F7', '#F472B6', '#34D399', '#60A5FA', '#FBBF24', '#FB923C', '#E879F9'
    ];

    new Chart(document.getElementById('breakdownChart'), {
        type: 'doughnut',
        data: {
            labels: ["Login", "Lesson Watched", "Course Enrolled"],
            datasets: [{
                data: [11, 1, 1],
                backgroundColor: breakColors,
                borderColor: 'rgba(10, 10, 30, 0.8)',
                borderWidth: 3,
                hoverOffset: 8
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            cutout: '65%',
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        color: '#A0A0B8',
                        font: { size: 11, family: "'Inter', sans-serif" },
                        padding: 12,
                        usePointStyle: true,
                        pointStyle: 'circle'
                    }
                },
                tooltip: chartDefaults.plugins.tooltip
            },
            animation: { 
                animateRotate: true,
                animateScale: true,
                duration: 1500, 
                easing: 'easeInOutQuart' 
            }
        }
    });

    // ============================================= //
    // AI QUIZ MODAL LOGIC                           //
    // ============================================= //

    let currentQuestions = [];
    let currentDocTitle = "";
    let currentCourseId = null;

    async function openQuizModal(docId, title, courseId) {
        const modal = document.getElementById('quizModal');
        const loader = document.getElementById('quizLoader');
        const content = document.getElementById('quizContent');
        const saveBtn = document.getElementById('saveQuizBtn');

        currentDocTitle = title;
        currentCourseId = courseId;
        currentQuestions = [];

        if (!currentCourseId) {
            alert("Warning: This document is not linked to any course.");
        }

        modal.style.display = 'flex';
        document.getElementById('modalDocTitle').innerText = title;
        content.innerHTML = '';
        loader.style.display = 'block';
        saveBtn.style.display = 'none';

        const formData = new FormData();
        formData.append('doc_id', docId);

        try {
            const response = await fetch("/quiz/generate/", {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': 'tYhoaIuWNXUQ5ReVAdhgWu1K0h7i6CVEg1j8yhdhX8TLGM19tZLyAj6YLL40GRup' }
            });
            const data = await response.json();
            loader.style.display = 'none';

            if (data.status === 'success') {
                currentQuestions = data.quiz;
                saveBtn.style.display = 'inline-block';
                renderQuestions(data.quiz);
            } else {
                content.innerHTML = `<p style="color:var(--accent-red); text-align:center;">Error: ${data.message}</p>`;
            }
        } catch (error) {
            loader.style.display = 'none';
            content.innerHTML = `<p style="color:var(--accent-red); text-align:center;">Network Error or Server Timeout.</p>`;
        }
    }

    function renderQuestions(questions) {
        const content = document.getElementById('quizContent');
        let html = '<div class="generated-quiz-list">';
        questions.forEach((q, idx) => {
            html += `
                <div class="q-item" style="background:rgba(0,0,0,0.3); padding:16px; margin-bottom:10px; border-radius:var(--radius-sm); border:1px solid var(--glass-border);">
                    <div class="q-text" style="margin-bottom:10px; font-weight:600;"><strong>Q${idx+1}:</strong> ${q.question_text}</div>
                    <div class="q-options" style="display:grid; grid-template-columns: 1fr 1fr; gap:8px;">
                        <div class="opt ${q.correct_option === 'A' ? 'correct' : ''}" style="padding:8px; border-radius:4px; ${q.correct_option === 'A' ? 'background:rgba(0,230,118,0.2); border:1px solid var(--accent-green);' : 'background:var(--glass-bg);'}">A) ${q.option_a}</div>
                        <div class="opt ${q.correct_option === 'B' ? 'correct' : ''}" style="padding:8px; border-radius:4px; ${q.correct_option === 'B' ? 'background:rgba(0,230,118,0.2); border:1px solid var(--accent-green);' : 'background:var(--glass-bg);'}">B) ${q.option_b}</div>
                        <div class="opt ${q.correct_option === 'C' ? 'correct' : ''}" style="padding:8px; border-radius:4px; ${q.correct_option === 'C' ? 'background:rgba(0,230,118,0.2); border:1px solid var(--accent-green);' : 'background:var(--glass-bg);'}">C) ${q.option_c}</div>
                        <div class="opt ${q.correct_option === 'D' ? 'correct' : ''}" style="padding:8px; border-radius:4px; ${q.correct_option === 'D' ? 'background:rgba(0,230,118,0.2); border:1px solid var(--accent-green);' : 'background:var(--glass-bg);'}">D) ${q.option_d}</div>
                    </div>
                </div>
            `;
        });
        html += '</div>';
        content.innerHTML = html;
    }

    async function saveQuizToDB() {
        if (currentQuestions.length === 0) return;
        
        const saveBtn = document.getElementById('saveQuizBtn');
        saveBtn.innerText = 'Saving...';
        saveBtn.disabled = true;

        const payload = {
            title: `AI Quiz: ${currentDocTitle}`,
            description: `Auto-generated quiz from document: ${currentDocTitle}`,
            course_id: currentCourseId,
            questions: currentQuestions
        };

        try {
            const response = await fetch("/quiz/save/", {
                method: 'POST',
                headers: { 
                    'Content-Type': 'application/json',
                    'X-CSRFToken': 'tYhoaIuWNXUQ5ReVAdhgWu1K0h7i6CVEg1j8yhdhX8TLGM19tZLyAj6YLL40GRup'
                },
                body: JSON.stringify(payload)
            });
            const data = await response.json();
            
            if (data.status === 'success') {
                document.getElementById('quizContent').innerHTML = `
                    <div style="text-align:center; padding: 40px;">
                        <i class="fas fa-check-circle" style="font-size: 50px; color: var(--accent-green); margin-bottom:15px;"></i>
                        <h3 style="color: #fff;">Quiz Saved Successfully!</h3>
                        <p style="color: var(--text-muted);">You can now link it to an exam module.</p>
                    </div>
                `;
                saveBtn.style.display = 'none';
            } else {
                alert("Error saving quiz: " + data.message);
                saveBtn.innerText = 'Save to Exams';
                saveBtn.disabled = false;
            }
        } catch (error) {
            alert("Network Error saving quiz.");
            saveBtn.innerText = 'Save to Exams';
            saveBtn.disabled = false;
        }
    }
    
    // ============================================= //
    // COURSE ACTIVITY TRACKER LOGIC                 //
    // ============================================= //
    
    let trackerDailyChartInst = null;
    let trackerTypeChartInst = null;
    let trackerQuizChartInst = null;
    
    // Pre-loaded student enrollments dictionary (generated via Django template)
    // To keep it simple, we will fetch the student's enrollments when selecting a student
    
    // Simulating student course list fetch (In a real app, make another AJAX call to get courses for student)
    // For this implementation, we will populate the course list dynamically or use a static list
    // We will just enable the course dropdown and assume the admin knows the course ID or we load all courses.
    const allCoursesList = [
        
        { id: "33", title: "Linux" },
        
        { id: "32", title: "DSA" },
        
        { id: "31", title: "Generative Ai" },
        
        { id: "30", title: "Kotlin" },
        
        { id: "29", title: "PostgreSQL" },
        
        { id: "28", title: "TypeScript" },
        
        { id: "27", title: "Git \u0026 GitHub" },
        
        { id: "26", title: "Express Js" },
        
        { id: "25", title: "AngularJS" },
        
        { id: "24", title: "CSS 3" },
        
        { id: "23", title: "DBMS" },
        
        { id: "22", title: "Data Science" },
        
        { id: "21", title: "Basic Dark web" },
        
        { id: "20", title: "Advanced Excel" },
        
        { id: "19", title: "Machine Learning" },
        
        { id: "18", title: "cloud computing (aws/azure)" },
        
        { id: "17", title: "Java Script" },
        
        { id: "16", title: "NumPy" },
        
        { id: "15", title: "Tailwind CSS" },
        
        { id: "14", title: "Full stack web development" },
        
        { id: "13", title: "HTML" },
        
        { id: "12", title: "PHP" },
        
        { id: "11", title: "Prompt Engineering" },
        
        { id: "10", title: "Node Js" },
        
        { id: "9", title: "mongo dB" },
        
        { id: "8", title: "MySQL" },
        
        { id: "7", title: "React js" },
        
        { id: "6", title: "E Commers And digital marketing" },
        
        { id: "5", title: "C++" },
        
        { id: "4", title: "Java" },
        
        { id: "3", title: "SSAD" },
        
        { id: "2", title: "Python" },
        
        { id: "1", title: "Cyber security" },
        
    ];
    
    function loadStudentCourses() {
        const studentId = document.getElementById('trackerStudent').value;
        const courseSelect = document.getElementById('trackerCourse');
        
        if (!studentId) {
            courseSelect.innerHTML = '<option value="">-- Select Student First --</option>';
            courseSelect.disabled = true;
            return;
        }
        
        // In a full implementation, you'd fetch the specific enrollments for this student.
        // Here, we'll populate all courses for simplicity, and the API will return 404 if not enrolled.
        courseSelect.innerHTML = '<option value="">-- Choose a Course --</option>';
        allCoursesList.forEach(c => {
            courseSelect.innerHTML += `<option value="${c.id}">${c.title}</option>`;
        });
        courseSelect.disabled = false;
    }
    
    async function fetchTrackerData() {
        const studentId = document.getElementById('trackerStudent').value;
        const courseId = document.getElementById('trackerCourse').value;
        
        if (!studentId || !courseId) return;
        
        const btn = document.getElementById('refreshTrackerBtn');
        const loader = document.getElementById('trackerLoader');
        const results = document.getElementById('trackerResults');
        
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        results.style.display = 'none';
        loader.style.display = 'block';
        
        try {
            const url = `/students/admin-panel/api/student-course-activity/${studentId}/${courseId}/`;
            const response = await fetch(url);
            
            if (!response.ok) {
                const errData = await response.json();
                alert(errData.error || "Failed to fetch data.");
                loader.style.display = 'none';
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-sync-alt"></i> Load Data';
                return;
            }
            
            const data = await response.json();
            
            // Populate Profile & Meta
            document.getElementById('tpName').innerText = data.student_name;
            document.getElementById('tpCourse').innerText = data.course_title;
            document.getElementById('tpEnrolled').innerText = data.enrolled_at;
            document.getElementById('tpLastAccess').innerText = data.last_accessed;
            
            // Populate Stats
            document.getElementById('tsProgress').innerText = data.progress_percent + '%';
            document.getElementById('tsLessons').innerText = `${data.completed_lessons} of ${data.total_lessons} Lessons`;
            
            document.getElementById('tsQuizAvg').innerText = data.avg_quiz_score + '%';
            document.getElementById('tsQuizzes').innerText = `${data.total_quizzes} Quizzes Taken`;
            
            document.getElementById('tsAssignmentAvg').innerText = data.avg_assignment_marks + '%';
            document.getElementById('tsAssignments').innerText = `${data.submitted_assignments} of ${data.total_assignments} Submitted`;
            
            // Render Daily Activity Chart
            if (trackerDailyChartInst) trackerDailyChartInst.destroy();
            const ctxDaily = document.getElementById('trackerDailyChart').getContext('2d');
            const actGrad = ctxDaily.createLinearGradient(0, 0, 0, 200);
            actGrad.addColorStop(0, 'rgba(0, 243, 255, 0.3)');
            actGrad.addColorStop(1, 'rgba(0, 243, 255, 0)');
            
            trackerDailyChartInst = new Chart(ctxDaily, {
                type: 'line',
                data: {
                    labels: data.daily_labels,
                    datasets: [{
                        label: 'Actions',
                        data: data.daily_data,
                        borderColor: '#00f3ff',
                        backgroundColor: actGrad,
                        fill: true, tension: 0.4,
                        pointBackgroundColor: '#00f3ff'
                    }]
                },
                options: { ...chartDefaults, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } }
            });
            
            // Render Type Breakdown Chart
            if (trackerTypeChartInst) trackerTypeChartInst.destroy();
            const ctxType = document.getElementById('trackerTypeChart').getContext('2d');
            trackerTypeChartInst = new Chart(ctxType, {
                type: 'doughnut',
                data: {
                    labels: data.type_labels,
                    datasets: [{
                        data: data.type_data,
                        backgroundColor: ['#00f3ff', '#bc13fe', '#00E676', '#FFB74D', '#FF3366'],
                        borderWidth: 0
                    }]
                },
                options: { ...chartDefaults, cutout: '70%', plugins: { legend: { display: true, position: 'right', labels: {color: '#fff', font: {size: 10}} } } }
            });
            
            // Render Quiz Trends
            const quizContainer = document.getElementById('quizTrendContainer');
            if (data.quiz_labels.length > 0) {
                quizContainer.style.display = 'block';
                if (trackerQuizChartInst) trackerQuizChartInst.destroy();
                const ctxQuiz = document.getElementById('trackerQuizChart').getContext('2d');
                trackerQuizChartInst = new Chart(ctxQuiz, {
                    type: 'line',
                    data: {
                        labels: data.quiz_labels,
                        datasets: [{
                            label: 'Score %',
                            data: data.quiz_scores,
                            borderColor: '#FFB74D',
                            backgroundColor: 'rgba(255, 183, 77, 0.1)',
                            fill: true, tension: 0.3, pointRadius: 4
                        }]
                    },
                    options: { ...chartDefaults, scales: { y: { max: 100, beginAtZero: true } } }
                });
            } else {
                quizContainer.style.display = 'none';
            }
            
            // Render Recent Activities List
            const recentList = document.getElementById('trackerRecentList');
            recentList.innerHTML = '';
            if (data.recent_activities.length === 0) {
                recentList.innerHTML = '<div style="color:#666; font-size:0.85rem;">No recent actions in this course.</div>';
            } else {
                data.recent_activities.forEach(act => {
                    recentList.innerHTML += `
                        <div style="padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.05); display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <div style="color: #fff; font-size: 0.9rem;">${act.description}</div>
                                <div style="color: #666; font-size: 0.75rem;">${act.time}</div>
                            </div>
                            <div style="color: var(--neon-blue); font-size: 0.8rem; padding: 2px 8px; background: rgba(0,243,255,0.1); border-radius: 10px;">${act.type}</div>
                        </div>
                    `;
                });
            }
            
            loader.style.display = 'none';
            results.style.display = 'block';
            
        } catch (error) {
            console.error(error);
            alert("Network error fetching tracker data.");
            loader.style.display = 'none';
        }
        
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync-alt"></i> Load Data';
    }

    // Activity items stagger animation
    document.querySelectorAll('.activity-item').forEach((item, i) => {
        item.style.animationDelay = `${i * 80}ms`;
    });
