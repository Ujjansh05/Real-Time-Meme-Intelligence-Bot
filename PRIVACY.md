# Humour Hub privacy notice

Humour Hub is a browser extension for explaining and making memes. This notice describes the public beta.

## Content you choose to submit

The extension sends text or an image to the Humour Hub API only after you check the AI consent box and request an explanation or remix. The API uses the provider configured by its operator: Cloudflare Workers AI or Ollama running on the operator's own computer. The `/api/v1/status` response identifies the active provider. With Ollama, meme content reaches the operator's computer through the public API but is not forwarded to Cloudflare Workers AI. The extension does not read your browsing history or automatically upload images from pages. A right-click action can place selected page text into the extension for your review; it is not sent to AI automatically. If Cloudflare Workers AI is configured, review its [data usage policy](https://developers.cloudflare.com/workers-ai/platform/data-usage/) for processing terms.

The API processes uploads in memory. It does not intentionally save submitted text, images, or AI answers on the server. A public deployment may use an HTTPS tunnel or relay, such as Tailscale Funnel or Cloudflare Tunnel, to carry requests to the API. Hosting and relay providers may keep limited operational request logs. Do not submit private or sensitive material.

## Data stored on your device

Drafts, favorite results, recent results, and imported images remain in this browser's extension storage. You can delete individual entries or clear the library. Exporting a library file or PNG saves it where your browser downloads files. Removing the extension generally removes its local data unless you exported it.

## Guest access and limits

The API issues an anonymous session token. Public deployments use Redis to store short-lived keyed identifiers and request counts for fair-use limits; these records expire automatically. A local-only test can use process memory instead, which clears on restart. The extension does not require a name or email address. There is no advertising tracker or analytics SDK in the extension.

## Live trends

The API may read public Wikipedia pageview counts, Reddit posts, and Bluesky posts. Trend cards link to their sources. Public posts and their metrics can be temporarily cached to calculate changes. Humour Hub does not request your social media account credentials.

## Contact and changes

Open an issue in the [project repository](https://github.com/Ujjansh05/Real-Time-Meme-Intelligence-Bot/issues) for privacy questions or deletion requests. Local entries can be deleted within the extension. This notice should be updated whenever data flows change.
