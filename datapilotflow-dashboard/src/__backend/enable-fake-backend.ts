import { app } from '@/config';

export async function enableFakeBackend() {
  if (!app.fakeBackend) {
    return;
  }

  try {
    const { worker } = await import('./handlers');

    // `worker.start()` returns a Promise that resolves
    // once the Service Worker is up and ready to intercept requests.
    await worker.start({ 
      onUnhandledRequest: 'bypass',
      serviceWorker: {
        url: '/mockServiceWorker.js',
      },
    });
  } catch (error) {
    console.error('❌ Failed to start fake backend:', error);
  }
}
