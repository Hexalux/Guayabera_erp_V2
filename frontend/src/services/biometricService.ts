import { hrService, RegistroAsistencia } from './hrService';
import dayjs from 'dayjs';

// Simulamos Local Agent o WebService local
const LOCAL_AGENT_URL = 'http://localhost:5000/api/fingerprint';

interface OfflineCheck {
  empleado_id: string;
  tipo: string;
  metodo: string;
  fecha_hora: string;
}

export const biometricService = {
  // Conecta con el agente local para leer una huella
  scanFingerprint: async (): Promise<string> => {
    try {
      // Intentamos llamar al hardware real a través del agente local
      const res = await fetch(`${LOCAL_AGENT_URL}/scan`);
      if (!res.ok) throw new Error("Hardware no responde");
      const data = await res.json();
      return data.template_base64; // Retorna el template capturado
    } catch (error) {
      console.warn("Agente biométrico local no disponible. Se simulará la huella.");
      // Simulación temporal para MVP/Desarrollo
      return new Promise(resolve => {
        setTimeout(() => resolve("base64_simulated_fingerprint_data_12345"), 1500);
      });
    }
  },

  // Guarda la checada (intenta Online, si falla va a Offline)
  clockInOrOut: async (empleado_id: string, tipo: string): Promise<void> => {
    const payload = {
      empleado_id,
      tipo,
      metodo: 'biometrico',
      fecha_hora: dayjs().toISOString()
    };

    if (navigator.onLine) {
      try {
        await hrService.checkAsistencia(payload);
        return;
      } catch (err) {
        console.warn("Fallo el envío al backend. Guardando offline...");
      }
    }
    
    // Modo Offline
    const queue: OfflineCheck[] = JSON.parse(localStorage.getItem('offline_checks') || '[]');
    queue.push(payload);
    localStorage.setItem('offline_checks', JSON.stringify(queue));
  },

  // Sincroniza la cola cuando vuelve el internet
  syncOfflineQueue: async (): Promise<number> => {
    const queue: OfflineCheck[] = JSON.parse(localStorage.getItem('offline_checks') || '[]');
    if (queue.length === 0) return 0;

    try {
      await hrService.syncAsistenciasOffline(queue);
      localStorage.removeItem('offline_checks');
      return queue.length;
    } catch (err) {
      console.error("Error sincronizando cola offline", err);
      return 0;
    }
  }
};

// Auto-Sincronización cuando regresa el internet
window.addEventListener('online', () => {
  console.log("Internet restaurado. Sincronizando asistencias...");
  biometricService.syncOfflineQueue().then(count => {
    if (count > 0) {
      // Emitiríamos un evento o usaríamos Toast de AntD pero aquí no hay contexto de UI
      console.log(`${count} checadas sincronizadas.`);
    }
  });
});
