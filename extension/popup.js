// Remix image button logic
document.getElementById('remixImageBtn').addEventListener('click', async () => {
  const imageInput = document.getElementById('memeImageInput');
  const file = pastedImageFile || imageInput.files[0];
  if (!file) {
    updateResult('Please select or paste an image to remix.');
    return;
  }
  updateResult('Remixing meme image...');
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch('http://127.0.0.1:8000/remix_image', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    updateResult('Image Remix: ' + data.remix);
  } catch (error) {
    console.error('Error remixing meme image:', error);
    updateResult('Failed to remix meme image. Make sure the backend server is running.');
  }
});
// Handle image paste
const pasteImageArea = document.getElementById('pasteImageArea');
let pastedImageFile = null;
pasteImageArea.addEventListener('paste', (event) => {
  const items = event.clipboardData.items;
  for (let i = 0; i < items.length; i++) {
    if (items[i].type.indexOf('image') !== -1) {
      const file = items[i].getAsFile();
      pastedImageFile = file;
      // Show preview
      const reader = new FileReader();
      reader.onload = function(e) {
        pasteImageArea.innerHTML = `<img src="${e.target.result}" style="max-width:100%;max-height:120px;" />`;
      };
      reader.readAsDataURL(file);
      break;
    }
  }
});

// Modify explain image button to use pasted image if available
document.getElementById('explainImageBtn').addEventListener('click', async () => {
  const imageInput = document.getElementById('memeImageInput');
  const file = pastedImageFile || imageInput.files[0];
  if (!file) {
    updateResult('Please select or paste an image to explain.');
    return;
  }
  updateResult('Explaining meme image...');
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch('http://127.0.0.1:8000/explain_image', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    updateResult('Image Explanation: ' + data.explanation);
  } catch (error) {
    console.error('Error explaining meme image:', error);
    updateResult('Failed to explain meme image. Make sure the backend server is running.');
  }
});
// Image explain button logic
document.getElementById('explainImageBtn').addEventListener('click', async () => {
  const imageInput = document.getElementById('memeImageInput');
  const file = imageInput.files[0];
  if (!file) {
    updateResult('Please select an image to explain.');
    return;
  }
  updateResult('Explaining meme image...');
  try {
    const formData = new FormData();
    formData.append('file', file);
    const response = await fetch('http://127.0.0.1:8000/explain_image', {
      method: 'POST',
      body: formData
    });
    const data = await response.json();
    updateResult('Image Explanation: ' + data.explanation);
  } catch (error) {
    console.error('Error explaining meme image:', error);
    updateResult('Failed to explain meme image. Make sure the backend server is running.');
  }
});
// Function to update the result box
function updateResult(text) {
  document.getElementById('output').innerHTML = text; // Use innerHTML to allow for a loader later
}

// Event listeners for the buttons
document.getElementById('trendingBtn').addEventListener('click', async () => {
  updateResult('Fetching trending meme...');
  try {
    const response = await fetch('http://127.0.0.1:8000/trending');
    const data = await response.json();
    updateResult('Trending Meme: ' + data.trending_meme);
  } catch (error) {
    console.error('Error fetching trending meme:', error);
    updateResult('Failed to fetch trending meme. Make sure the backend server is running.');
  }
});

document.getElementById('explainBtn').addEventListener('click', async () => {
  const memeText = document.getElementById('memeInput').value;
  if (memeText) {
    updateResult('Explaining meme...');
    try {
      const response = await fetch(`http://127.0.0.1:8000/explain?meme=${encodeURIComponent(memeText)}`);
      const data = await response.json();
      updateResult('Explanation: ' + data.explanation);
    } catch (error) {
      console.error('Error explaining meme:', error);
      updateResult('Failed to explain meme. Make sure the backend server is running.');
    }
  } else {
    updateResult('Please enter a meme caption to explain.');
  }
});

document.getElementById('remixBtn').addEventListener('click', async () => {
 const memeText = document.getElementById('memeInput').value;
  if (memeText) {
    updateResult('Remixing meme...');
    try {
      const response = await fetch(`http://127.0.0.1:8000/remix?meme=${encodeURIComponent(memeText)}`);
      const data = await response.json();
      updateResult('Remix: ' + data.remix);
    } catch (error) {
      console.error('Error remixing meme:', error);
      updateResult('Failed to remix meme. Make sure the backend server is running.');
    }
  } else {
    updateResult('Please enter a meme caption to remix.');
  }
});