# PDF.js assets

Lege die Dateien `pdf.min.js` und `pdf.worker.min.js` aus dem PDF.js Release (z. B. Version 4.2.67) in dieses Verzeichnis, damit der Viewer ohne externe CDN-Abhängigkeiten funktioniert. Fehlen die Dateien oder sind sie durch die Content-Security-Policy blockiert, kann `window.pdfjsLib` nicht geladen werden und die Detailansicht bricht mit einer klaren Fehlermeldung ab, da kein Fallback-Viewer mehr genutzt wird.
