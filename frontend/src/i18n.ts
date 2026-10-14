export type Lang = "es" | "en";

const en = {
  tagline: "Chat with your documents",
  upload: "Drop a PDF here or click to choose",
  uploading: "Reading document…",
  urlPlaceholder: "…or paste an arXiv or PDF link",
  add: "Add",
  noDocs: "No documents yet. Add a PDF to start asking questions.",
  pages: "pages",
  failed: "Could not be read",
  ready: "Ready",
  processing: "Processing",
  remove: "Remove",
  pickDoc: "Pick a document on the left to start.",
  ask: "Ask something about this document…",
  send: "Send",
  stop: "Stop",
  sources: "Sources",
  page: "page",
  relevance: "relevance",
  noSources: "Sources for the answer appear here.",
  settings: "Answer engine",
  engineExtractive: "Extractive (no AI, no key)",
  engineExtractiveHelp: "Quotes the most relevant sentences from your document. Free and private.",
  engineAnthropic: "Anthropic (Claude)",
  engineOpenai: "OpenAI",
  engineHelp: "Writes a natural answer from the retrieved passages.",
  apiKey: "API key",
  keyHelp: "Kept in this browser tab only. It is sent to this Docuify server for each question and never stored.",
  model: "Model (optional)",
  close: "Close",
  stopped: "Stopped.",
  exampleTitle: "Try asking",
};

const es: typeof en = {
  tagline: "Conversa con tus documentos",
  upload: "Suelta un PDF aquí o haz clic para elegirlo",
  uploading: "Leyendo el documento…",
  urlPlaceholder: "…o pega un enlace de arXiv o a un PDF",
  add: "Agregar",
  noDocs: "Aún no hay documentos. Agrega un PDF para empezar a preguntar.",
  pages: "páginas",
  failed: "No se pudo leer",
  ready: "Listo",
  processing: "Procesando",
  remove: "Quitar",
  pickDoc: "Elige un documento a la izquierda para empezar.",
  ask: "Pregunta algo sobre este documento…",
  send: "Enviar",
  stop: "Detener",
  sources: "Fuentes",
  page: "página",
  relevance: "relevancia",
  noSources: "Aquí aparecen las fuentes de la respuesta.",
  settings: "Motor de respuestas",
  engineExtractive: "Extractivo (sin IA, sin llave)",
  engineExtractiveHelp: "Cita las frases más relevantes de tu documento. Gratis y privado.",
  engineAnthropic: "Anthropic (Claude)",
  engineOpenai: "OpenAI",
  engineHelp: "Redacta una respuesta natural a partir de los pasajes encontrados.",
  apiKey: "Llave de API",
  keyHelp: "Solo se guarda en esta pestaña del navegador. Se envía a este servidor de Docuify en cada pregunta y nunca se almacena.",
  model: "Modelo (opcional)",
  close: "Cerrar",
  stopped: "Detenido.",
  exampleTitle: "Prueba preguntando",
};

export type Messages = typeof en;
export const messages: Record<Lang, Messages> = { en, es };

export function detectLang(): Lang {
  const saved = localStorage.getItem("docuify.lang");
  if (saved === "es" || saved === "en") return saved;
  return navigator.language.toLowerCase().startsWith("es") ? "es" : "en";
}
