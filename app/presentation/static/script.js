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

// НОВЫЙ ЭЛЕМЕНТ: Поле ввода типа вагона
const wagonTypeInput = document.getElementById('wagonType');

let currentFile = null;

// API базовый URL
const API_URL = window.location.origin + '/api/v1';

// НОВАЯ ФУНКЦИЯ: Валидация типа вагона
function validateWagonType(type) {
    // Допустимые значения с большой буквы
    const validTypes = ['Крытый', 'Цистерна', 'Полувагон', 'Хоппер'];
    
    // Проверяем введенное значение
    if (!type || type.trim() === '') {
        return {
            isValid: false,
            message: 'Пожалуйста, введите тип вагона'
        };
    }
    
    // Удаляем лишние пробелы
    const trimmedType = type.trim();
    
    // Проверяем точное совпадение (с учетом регистра)
    if (validTypes.includes(trimmedType)) {
        return {
            isValid: true,
            message: null,
            value: trimmedType
        };
    }
    
    // Проверка с учетом регистра (если пользователь ввел с маленькой буквы)
    const lowerCaseValid = validTypes.map(v => v.toLowerCase());
    if (lowerCaseValid.includes(trimmedType.toLowerCase())) {
        // Находим правильное написание
        const correctValue = validTypes[lowerCaseValid.indexOf(trimmedType.toLowerCase())];
        return {
            isValid: false,
            message: `Неверный формат. Используйте: "${correctValue}" (с большой буквы)`
        };
    }
    
    return {
        isValid: false,
        message: `Неверное значение. Допустимые типы: ${validTypes.join(', ')}`
    };
}

// НОВАЯ ФУНКЦИЯ: Очистка стилей ошибки
function clearWagonTypeError() {
    wagonTypeInput.classList.remove('error');
}

// НОВАЯ ФУНКЦИЯ: Показать ошибку валидации
function showWagonTypeError(message) {
    wagonTypeInput.classList.add('error');
    showError(message);
}

// Обработчики событий
selectFileBtn.addEventListener('click', () => fileInput.click());
removeImageBtn.addEventListener('click', clearImage);
predictBtn.addEventListener('click', predictImage);
fileInput.addEventListener('change', handleFileSelect);

// НОВЫЙ ОБРАБОТЧИК: Очистка ошибки при вводе
wagonTypeInput.addEventListener('input', () => {
    clearWagonTypeError();
    hideError();
});

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
        clearWagonTypeError(); // Очищаем ошибку при новой загрузке
        wagonTypeInput.value = ''; // Очищаем поле ввода
    };
    reader.readAsDataURL(file);
}

function clearImage() {
    currentFile = null;
    fileInput.value = '';
    wagonTypeInput.value = ''; // Очищаем поле ввода
    previewArea.style.display = 'none';
    uploadArea.style.display = 'block';
    resultsArea.style.display = 'none';
    hideError();
    clearWagonTypeError();
}

async function predictImage() {
    if (!currentFile) {
        showError('Сначала выберите изображение');
        return;
    }
    
    // НОВАЯ ПРОВЕРКА: Валидация типа вагона
    const wagonType = wagonTypeInput.value;
    const validation = validateWagonType(wagonType);
    
    if (!validation.isValid) {
        showWagonTypeError(validation.message);
        wagonTypeInput.focus();
        return;
    }
    
    // Показываем загрузку
    loading.style.display = 'block';
    resultsArea.style.display = 'none';
    hideError();
    clearWagonTypeError();
    
    // Сохраняем введенный тип вагона для отображения
    const validatedWagonType = validation.value;
    
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
        
        // Отображаем результаты с типом вагона
        displayResults(data.data, validatedWagonType);
        
    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'Ошибка при отправке запроса');
    } finally {
        loading.style.display = 'none';
    }
}

// НОВАЯ ФУНКЦИЯ: Отображение результатов с типом вагона
function displayResults(data, wagonType) {
    const resultClass = document.getElementById('resultClass');
    const resultConfidence = document.getElementById('resultConfidence');
    const probabilitiesDiv = document.getElementById('probabilities');
    const wagonTypeDisplay = document.getElementById('wagonTypeDisplay');
    
    // Отображаем тип вагона
    wagonTypeDisplay.innerHTML = `
        <strong>Тип вагона:</strong> ${wagonType}
    `;
    wagonTypeDisplay.classList.remove('error');
    
    // Определяем эмодзи для класса
    let emoji = '';
    let classText = '';
    if (data.class === 'pered') {
        emoji = '🚂';
        classText = 'Передняя часть вагона';
    } else if (data.class === 'zad') {
        emoji = '🚂';
        classText = 'Задняя часть вагона';
    } else {
        emoji = '⭕';
        classText = 'Вагон не обнаружен';
    }
    
    // Отображаем основной результат
    resultClass.innerHTML = `${emoji} ${classText}<br><span style="font-size: 14px; color: #666;">${data.class_name}</span>`;
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