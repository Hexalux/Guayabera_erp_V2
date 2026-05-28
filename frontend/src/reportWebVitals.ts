const reportWebVitals = (onPerfEntry: any) => {
  if (onPerfEntry && onPerfEntry instanceof Function) {
    import('web-vitals').then((webVitals) => {
      // Usar la notación de corchetes para acceder a las propiedades dinámicamente
      // para evitar errores de TypeScript
      const getCLS = (webVitals as any).getCLS;
      const getFID = (webVitals as any).getFID;
      const getFCP = (webVitals as any).getFCP;
      const getLCP = (webVitals as any).getLCP;
      const getTTFB = (webVitals as any).getTTFB;

      getCLS && getCLS(onPerfEntry);
      getFID && getFID(onPerfEntry);
      getFCP && getFCP(onPerfEntry);
      getLCP && getLCP(onPerfEntry);
      getTTFB && getTTFB(onPerfEntry);
    }).catch((error) => {
      console.error('Error importing web-vitals:', error);
    });
  }
};

export default reportWebVitals;