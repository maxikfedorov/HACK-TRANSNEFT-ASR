document.addEventListener('DOMContentLoaded', () => {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('audioFile');
    const fileInfo = document.getElementById('fileInfo');
    const fileName = document.getElementById('fileName');
    const removeFile = document.getElementById('removeFile');
    const processButton = document.getElementById('processButton');
    const spinner = processButton.querySelector('.spinner-border');
    const buttonText = processButton.querySelector('.button-text');

    // Drag and Drop handlers
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.add('drag-over');
        });
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => {
            dropZone.classList.remove('drag-over');
        });
    });

    dropZone.addEventListener('drop', handleDrop);
    fileInput.addEventListener('change', handleFileSelect);
    removeFile.addEventListener('click', handleFileRemove);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }

    function handleFileSelect(e) {
        const files = e.target.files;
        handleFiles(files);
    }

    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (file.type.startsWith('audio/')) {
                showFileInfo(file);
                uploadFile(file);
            } else {
                showNotification('Пожалуйста, выберите аудиофайл', 'error');
            }
        }
    }

    function showFileInfo(file) {
        fileName.textContent = file.name;
        fileInfo.classList.remove('d-none');
        dropZone.querySelector('.drop-zone-content').classList.add('d-none');
    }

    function handleFileRemove(e) {
        e.stopPropagation();
        fileInput.value = '';
        fileInfo.classList.add('d-none');
        dropZone.querySelector('.drop-zone-content').classList.remove('d-none');
        processButton.disabled = true;
    }

    async function uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        try {
            const response = await fetch('http://localhost:5000/upload-audio', {
                method: 'POST',
                body: formData
            });

            if (response.ok) {
                showNotification('Файл успешно загружен', 'success');
                processButton.disabled = false;
            } else {
                showNotification('Ошибка при загрузке файла', 'error');
            }
        } catch (error) {
            showNotification('Ошибка сервера', 'error');
            console.error('Error:', error);
        }
    }

    processButton.addEventListener('click', async () => {
        setLoadingState(true);

        try {
            const response = await fetch('http://localhost:5000/transcribe-audio', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ filename: '' })
            });

            if (response.ok) {
                const data = await response.json();
                displayResults(data);
                showNotification('Обработка завершена успешно', 'success');
            } else {
                showNotification('Ошибка при обработке файла', 'error');
            }
        } catch (error) {
            showNotification('Ошибка сервера', 'error');
            console.error('Error:', error);
        } finally {
            setLoadingState(false);
        }
    });

    function setLoadingState(isLoading) {
        processButton.disabled = isLoading;
        if (isLoading) {
            spinner.classList.remove('d-none');
            buttonText.textContent = 'Обработка...';
        } else {
            spinner.classList.add('d-none');
            buttonText.textContent = 'Обработать файл';
        }
    }

    function displayResults(data) {
        const resultDiv = document.getElementById('result');
        const resultFileName = document.getElementById('resultFileName');
        const transcriptionText = document.getElementById('transcriptionText');
        const formalizedData = document.getElementById('formalizedData');

        resultFileName.textContent = data.transcription.audio_file_name;
        transcriptionText.textContent = data.transcription.text;

        formalizedData.innerHTML = Object.entries(data.formalized_data)
            .reverse() // добавляем reverse() перед map
            .map(([key, value]) => `
        <tr>
            <td class="fw-medium">${formatKey(key)}</td>
            <td>${value}</td>
        </tr>
    `).join('');


        resultDiv.classList.remove('d-none');
        resultDiv.classList.add('show');
        resultDiv.scrollIntoView({ behavior: 'smooth' });
    }

    function formatKey(key) {
        return key.split('_')
            .map(word => word.charAt(0).toUpperCase() + word.slice(1))
            .join(' ');
    }

    function showNotification(message, type) {
        const backgroundColor = type === 'success' ? '#4caf50' : '#f44336';

        Toastify({
            text: message,
            duration: 3000,
            gravity: "top",
            position: "right",
            backgroundColor,
            stopOnFocus: true,
            className: "notification"
        }).showToast();
    }
});
