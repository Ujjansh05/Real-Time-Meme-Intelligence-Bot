# Humour Hub store submission

This is the submission copy for the public Chrome and Microsoft Edge extension. Use a production ZIP built with `HUMOUR_HUB_API_URL` set to a working HTTPS backend. Do not upload the local preview ZIP, which points to `127.0.0.1`.

## Listing

- **Name:** Humour Hub
- **Short description:** Explain or remix memes with AI, edit original templates, and save your creations locally.
- **Single purpose:** Help people understand and create memes in their browser.
- **Category:** Entertainment
- **Language:** English listing; the AI response controls support English, Hindi, and Hinglish.
- **Website:** https://github.com/Ujjansh05/Real-Time-Meme-Intelligence-Bot
- **Support:** https://github.com/Ujjansh05/Real-Time-Meme-Intelligence-Bot/issues
- **Privacy policy:** https://github.com/Ujjansh05/Real-Time-Meme-Intelligence-Bot/blob/main/PRIVACY.md

### Full description

Humour Hub helps you understand a meme and make your own. Paste a caption or choose an image to request an AI explanation or three remixes in English, Hindi, or Hinglish. Choose an original template or upload an image, position captions in the editor, and download a PNG. Keep drafts, history, and favorites in your browser. Discovery cards show source links and observation times when trend data is available.

AI processing is optional and has a small daily free allowance. The editor, downloads, and local library work without AI. Only text or images you choose to submit are sent to the Humour Hub API and Cloudflare Workers AI, after you check the consent box. Humour Hub does not require an account, read browsing history, run ads, or use an analytics SDK. See the privacy policy for details.

### Permission explanations

- `storage`: keeps the anonymous session token, theme, service URL, and selected text that the user sends from a context menu until the workspace opens. Drafts and favorites use browser-local IndexedDB.
- `contextMenus`: adds Explain and Remix actions for text the user explicitly selects on a page. The selected text is placed in the extension workspace for review and is not sent to AI until the user consents and clicks an action.
- Required HTTPS host permission: connects to the Humour Hub API bundled into the production build for AI and trend requests.
- Optional HTTPS host permission: requested only for the exact custom API host the user enters if they self-host the backend. The extension does not request blanket site access at install time.
- Optional localhost permissions: allow a user to connect to a backend they run on their own computer.

### User data disclosure

For an AI request, the user-selected text or image is sent to the Humour Hub API and forwarded to Cloudflare Workers AI. Images and answers are not intentionally stored on the API server. Anonymous session and short-lived network identifiers are used in Upstash Redis for daily quotas. Drafts, favorites, history, and imported images stay in the browser's local storage unless the user exports them. Public trend data comes from cited sources. There are no ads or analytics SDKs. Refer to `PRIVACY.md` for the full notice and confirm these statements against the live deployment before submitting store privacy forms.

### Reviewer test instructions

1. Install the production ZIP and open the full workspace from the popup.
2. Open **Editor**, choose **Two moods**, add caption text, and download a PNG. This works with no account or API request.
3. Open **Library** to see saved drafts. Export and import are available locally.
4. For AI, enter a harmless sample caption, check the consent box, and click **Explain**. A daily quota applies, so a quota message may appear if the shared beta allowance has been used.
5. Open **Discovery** to inspect source links and observation times. A source can be marked unavailable when its external feed is down.

## Artwork and screenshots

The generated square master logo is at `docs/store-assets/icon-master.png`. The exact 128 × 128 store icon is `extension/icon-128.png`; the ZIP includes matching 16 and 48 pixel versions. The logo was derived from the earlier Humour Hub artwork, with the readable H mark retained and the inconsistent in-image name removed.

Capture genuine screenshots from the production extension after deployment. For Chrome, prepare at least one 1280 × 800 screenshot. Good views are the local editor with an original template and the popup with a sample caption. Keep user data and credentials out of screenshots. The Edge listing may also use 1280 × 800 screenshots. Do not show AI results or live trends as available unless they have been tested on the deployed service.

## Submission order

1. Rotate any credentials that appeared in old Git history, deploy the backend, and verify `GET /api/v1/status` plus one consented AI request.
2. Put its HTTPS origin in the GitHub Actions variable `HUMOUR_HUB_API_URL`, run **Verify and package**, and download the ZIP and SHA-256 checksum.
3. Load the production ZIP in clean Chrome and Edge profiles and follow the reviewer steps above.
4. Merge the release branch so the privacy URL points to the current policy on `main`.
5. Upload the production ZIP and listing materials to Microsoft Edge Partner Center. A registered owner account is required; registration currently has no fee. Submit for review.
6. If a Chrome Web Store developer account is available, upload the same ZIP to its dashboard, fill out the Listing, Privacy, Distribution, and Test instructions tabs, then submit for review. Chrome currently requires a one-time developer registration fee.
7. After approval, put the final store links in `README.md` and share those links with users. A GitHub Release can also host the ZIP for developer-mode installation.

Store review and public installation are not complete until the store accepts and publishes the submission. Review the current store forms and policies at submission time.
