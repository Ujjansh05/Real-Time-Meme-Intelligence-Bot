# Humour Hub privacy notice

Humour Hub is a browser extension for explaining and making memes. This notice describes the public beta.

## Content you choose to submit

The extension sends text or an image to the Humour Hub API only when you request an AI explanation or remix. The API forwards that content to Cloudflare Workers AI to produce the answer. The extension does not read your browsing history or automatically upload images from pages. Review Cloudflare's [Workers AI data usage policy](https://developers.cloudflare.com/workers-ai/platform/data-usage/) for its processing terms.

The API processes uploads in memory. It does not intentionally save submitted text, images, or AI answers on the server. Hosting providers may keep limited operational request logs. Do not submit private or sensitive material.

## Data stored on your device

Drafts, favorite results, recent results, and imported images remain in this browser's extension storage. You can delete individual entries or clear the library. Exporting a library file or PNG saves it where your browser downloads files. Removing the extension generally removes its local data unless you exported it.

## Guest access and limits

The API issues an anonymous session token. To enforce fair use, it temporarily stores a token identifier, request counts, and a short-lived network address identifier in Redis. These records expire automatically. The extension does not require a name or email address. There is no advertising tracker or analytics SDK in the extension.

## Live trends

The API may read public Wikipedia pageview counts, Reddit posts, and Bluesky posts. Trend cards link to their sources. Public posts and their metrics can be temporarily cached to calculate changes. Humour Hub does not request your social media account credentials.

## Contact and changes

Open an issue in the [project repository](https://github.com/Ujjansh05/Real-Time-Meme-Intelligence-Bot/issues) for privacy questions or deletion requests. Local entries can be deleted within the extension. This notice should be updated whenever data flows change.
