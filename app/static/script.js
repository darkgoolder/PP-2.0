// DOM элементы
const uploadArea = document.getElementById('uploadArea');
const fileInput = document.getElementById('fileInput');
const selectFileBtn = document.getElementById('selectFileBtn');
const previewArea = document.getElementById('previewArea');
const previewImg = document.getElementById('previewImg');
const removeImageBtn = document.getElementById('removeImageBtn');
const predictBtn = document.getElementById('predictBtn');
const resultsArea = document.getElementById('resultsArea');
const loading = document.getElementById('loading');
const errorMessage = document.getElementById('errorMessage');

let currentFile = null;

// API базовый URL
const API_URL = window.location.origin + '/api/v1';

// Обработчики событий
selectFileBtn.addEventListener('click', () => fileInput.click());
removeImageBtn.addEventListener('click', clearImage);
predictBtn.addEventListener('click', predictImage);
fileInput.addEventListener('change', handleFileSelect);

// Drag & Drop
uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('drag-over');
});

uploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadArea.classList.remove('drag-over');
    const file = e.dataTransfer.files[0];
    if (file && file.type.startsWith('image/')) {
        handleFile(file);
    } else {
        showError('Пожалуйста, загрузите изображение');
    }
});

uploadArea.addEventListener('click', () => fileInput.click());

function handleFileSelect(e) {
    const file = e.target.files[0];
    if (file) {
        handleFile(file);
    }
}

function handleFile(file) {
    // Проверка размера (10 MB)
    if (file.size > 10 * 1024 * 1024) {
        showError('Файл слишком большой. Максимум 10 MB');
        return;
    }
    
    currentFile = file;
    
    // Предпросмотр
    const reader = new FileReader();
    reader.onload = (e) => {
        previewImg.src = e.target.result;
        uploadArea.style.display = 'none';
        previewArea.style.display = 'block';
        resultsArea.style.display = 'none';
        hideError();
    };
    reader.readAsDataURL(file);
}

function clearImage() {
    currentFile = null;
    fileInput.value = '';
    previewArea.style.display = 'none';
    uploadArea.style.display = 'block';
    resultsArea.style.display = 'none';
    hideError();
}

async function predictImage() {
    if (!currentFile) {
        showError('Сначала выберите изображение');
        return;
    }
    
    // Показываем загрузку
    loading.style.display = 'block';
    resultsArea.style.display = 'none';
    hideError();
    
    // Создаем FormData
    const formData = new FormData();
    formData.append('file', currentFile);
    
    try {
        // Отправляем запрос
        const response = await fetch(`${API_URL}/predict`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error?.message || 'Ошибка при обработке');
        }
        
        // Отображаем результаты
        displayResults(data.data);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Ошибка при отправке запроса');
    } finally {
        loading.style.display = 'none';
    }
}

function displayResults(data) {
    const resultClass = document.getElementById('resultClass');
    const resultConfidence = document.getElementById('resultConfidence');
    const probabilitiesDiv = document.getElementById('probabilities');
    
    // Определяем эмодзи для класса
    let emoji = '';
    if (data.class === 'pered') emoji = '🚂 Передняя часть';
    else if (data.class === 'zad') emoji = '🚂 Задняя часть';
    else emoji = '⭕ Вагон не обнаружен';
    
    // Отображаем основной результат
    resultClass.innerHTML = `${emoji}<br>${data.class_name}`;
    resultConfidence.innerHTML = `Уверенность: <strong>${(data.confidence * 100).toFixed(1)}%</strong>`;
    
    // Отображаем все вероятности
    probabilitiesDiv.innerHTML = '<h4>Распределение вероятностей:</h4>';
    
    const classNames = {
        'pered': 'Передняя часть',
        'zad': 'Задняя часть',
        'none': 'Вагон не обнаружен'
    };
    
    for (const [cls, prob] of Object.entries(data.probabilities)) {
        const percent = (prob * 100).toFixed(1);
        const isPredicted = cls === data.class;
        
        const probItem = document.createElement('div');
        probItem.className = 'prob-item';
        probItem.innerHTML = `
            <div class="prob-label">${classNames[cls] || cls}</div>
            <div class="prob-bar">
                <div class="prob-fill" style="width: ${percent}%; background: ${isPredicted ? 'linear-gradient(90deg, #667eea, #764ba2)' : '#cbd5e0'}">
                    ${percent}%
                </div>
            </div>
        `;
        probabilitiesDiv.appendChild(probItem);
    }
    
    // Показываем результаты
    resultsArea.style.display = 'block';
    
    // Прокручиваем к результатам
    resultsArea.scrollIntoView({ behavior: 'smooth' });
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.style.display = 'block';
    setTimeout(() => {
        errorMessage.style.display = 'none';
    }, 5000);
}

function hideError() {
    errorMessage.style.display = 'none';
}

// Проверка здоровья API при загрузке
async function checkHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        if (data.status === 'healthy') {
            console.log('✅ API готов к работе');
        } else {
            console.warn('⚠️ API не здоров:', data);
            showError('Сервис временно недоступен');
        }
    } catch (error) {
        console.error('❌ API недоступен:', error);
        showError('Не удалось подключиться к серверу');
    }
}

// Запускаем проверку при загрузке
checkHealth();