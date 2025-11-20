// Tab Switching Logic
const tabs = document.querySelectorAll('.tab');
const tabContents = document.querySelectorAll('.tab-content');

tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    // Remove active class from all tabs and contents
    tabs.forEach(t => t.classList.remove('active'));
    tabContents.forEach(c => c.classList.remove('active'));

    // Add active class to clicked tab and corresponding content
    tab.classList.add('active');
    const targetId = tab.getAttribute('data-tab') + '-tab';
    document.getElementById(targetId).classList.add('active');
  });
});

// UI Helper Functions
const outputArea = document.getElementById('output');
const resultText = document.getElementById('resultText');
const loader = document.getElementById('loader');
const placeholder = document.querySelector('.placeholder');

function showLoader() {
  placeholder.style.display = 'none';
  resultText.style.display = 'none';
  loader.style.display = 'block';
}

function hideLoader() {
  loader.style.display = 'none';
  resultText.style.display = 'block';
}

function updateResult(text, isError = false) {
  hideLoader();
  if (isError) {
    resultText.innerHTML = `<span style="color: #ef4444;">${text}</span>`;
  } else {
    resultText.innerText = text;
  }
}

// Image Handling
const dropZone = document.getElementById('dropZone');
const imageInput = document.getElementById('memeImageInput');
const imagePreview = document.getElementById('imagePreview');
let selectedImageFile = null;

// Handle file selection via input
imageInput.addEventListener('change', (e) => {
  if (e.target.files && e.target.files[0]) {
    handleImageFile(e.target.files[0]);
  }
});

// Handle paste events (Ctrl+V)
document.addEventListener('paste', (event) => {
  // Only handle paste if we are on the image tab or if the user explicitly pasted into the drop zone
  // But for better UX, let's just capture any image paste if the extension is open
  const items = event.clipboardData.items;
  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) {
      const file = items[i].getAsFile();
      handleImageFile(file);
      // Switch to image tab if not active
      document.querySelector('[data-tab="image"]').click();
      break;
    }
  }
});

// Handle Drag & Drop
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('dragover');
});

dropZone.addEventListener('dragleave', () => {
  dropZone.classList.remove('dragover');
});

dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('dragover');
  if (e.dataTransfer.files && e.dataTransfer.files[0]) {
    handleImageFile(e.dataTransfer.files[0]);
  }
});

function handleImageFile(file) {
  selectedImageFile = file;
  const reader = new FileReader();
  reader.onload = function(e) {
    imagePreview.src = e.target.result;
    imagePreview.style.display = 'block';
    // Hide the text prompt in dropzone for cleaner look
    dropZone.querySelector('p').style.display = 'none';
  };
  reader.readAsDataURL(file);
}

// API Interaction Logic
const BASE_URL = 'http://127.0.0.1:8000';

async function callApi(endpoint, method = 'GET', body = null) {
  showLoader();
  try {
    const options = { method };
    if (body) {
      options.body = body;
    }
    
    const response = await fetch(`${BASE_URL}${endpoint}`, options);
    if (!response.ok) {
      throw new Error(`Server error: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    updateResult('Failed to connect to backend. Is it running?', true);
    throw error;
  }
}

// Buttons
document.getElementById('trendingBtn').addEventListener('click', async () => {
  try {
    const data = await callApi('/trending');
    updateResult('🔥 Trending: ' + data.trending_meme);
  } catch (e) {}
});

document.getElementById('explainBtn').addEventListener('click', async () => {
  const text = document.getElementById('memeInput').value.trim();
  if (!text) {
    updateResult('Please enter some text to explain.', true);
    return;
  }
  try {
    const data = await callApi(`/explain?meme=${encodeURIComponent(text)}`);
    updateResult(data.explanation);
  } catch (e) {}
});

document.getElementById('remixBtn').addEventListener('click', async () => {
  const text = document.getElementById('memeInput').value.trim();
  if (!text) {
    updateResult('Please enter some text to remix.', true);
    return;
  }
  try {
    const data = await callApi(`/remix?meme=${encodeURIComponent(text)}`);
    updateResult(data.remix);
  } catch (e) {}
});

document.getElementById('explainImageBtn').addEventListener('click', async () => {
  if (!selectedImageFile) {
    updateResult('Please upload or paste an image first.', true);
    return;
  }
  const formData = new FormData();
  formData.append('file', selectedImageFile);
  
  try {
    const data = await callApi('/explain_image', 'POST', formData);
    updateResult(data.explanation);
  } catch (e) {}
});

document.getElementById('remixImageBtn').addEventListener('click', async () => {
  if (!selectedImageFile) {
    updateResult('Please upload or paste an image first.', true);
    return;
  }
  const formData = new FormData();
  formData.append('file', selectedImageFile);
  
  try {
    const data = await callApi('/remix_image', 'POST', formData);
    updateResult(data.remix);
  } catch (e) {}
});