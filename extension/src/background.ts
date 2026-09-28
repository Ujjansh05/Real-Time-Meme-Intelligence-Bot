chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: 'explain', title: 'Explain with Humour Hub', contexts: ['selection', 'image'] });
  chrome.contextMenus.create({ id: 'remix', title: 'Remix with Humour Hub', contexts: ['selection'] });
});

chrome.contextMenus.onClicked.addListener(async info => {
  if (!['explain', 'remix'].includes(info.menuItemId as string)) return;
  await chrome.storage.local.set({
    pendingContext: {
      action: info.menuItemId,
      text: (info.selectionText || '').slice(0, 4000),
      image: info.mediaType === 'image',
    },
  });
  await chrome.tabs.create({ url: chrome.runtime.getURL('app.html#explain') });
});
