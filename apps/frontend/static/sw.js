// This is a minimal service worker that does nothing.
// It's here just to prevent 404 errors in the browser.
self.addEventListener("install", () => {
  self.skipWaiting();
});
