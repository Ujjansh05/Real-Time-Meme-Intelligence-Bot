chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "explainMeme",
    title: "Explain with Meme Bot",
    contexts: ["selection"]
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "explainMeme") {
    const meme = info.selectionText;
    chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: (memeText) => alert("Selected meme: " + memeText),
      args: [meme]
    });
  }
});