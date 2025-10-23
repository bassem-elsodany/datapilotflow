import ReactDOM from 'react-dom/client';
import { enableFakeBackend } from './__backend';
import { App } from './app';

enableFakeBackend().then(() => {
  ReactDOM.createRoot(document.getElementById('root')!).render(<App />);
}).catch((error) => {
  console.error('❌ Failed to start app:', error);
});
