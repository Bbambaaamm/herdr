import { createMachineScene } from './machine-scene.js';
import { mountDashboard } from './dashboard-ui.js';

mountDashboard(createMachineScene);

// Standalone review builds are explicitly demo-only. Production has no preview flag.
if (document.documentElement.dataset.preview === 'true') {
  document.querySelector('#demo-toggle').click();
}