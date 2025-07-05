// src/pdfWorker.js
import * as pdfjsLib from 'pdfjs-dist/legacy/build/pdf';
import workerSrc from 'pdfjs-dist/build/pdf.worker?url';

pdfjsLib.GlobalWorkerOptions.workerSrc = workerSrc;

export default pdfjsLib;
