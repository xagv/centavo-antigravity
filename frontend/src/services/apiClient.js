const API_BASE_URLS = {
  auth: import.meta.env?.VITE_AUTH_SERVICE_URL || '',
  transactions: import.meta.env?.VITE_TRANSACTIONS_SERVICE_URL || '',
};

let authToken = null;

export function setAuthToken(token) {
  authToken = token;
}

export function getAuthToken() {
  return authToken;
}

/**
 * Cliente HTTP centralizado para las llamadas a los microservicios de Centavo.
 * Evita el uso de fetch/axios sueltos dentro de los componentes.
 */
export async function requestService(serviceName, endpoint, options = {}) {
  const baseUrl = API_BASE_URLS[serviceName];
  if (baseUrl === undefined) {
    throw new Error(`Servicio desconocido: ${serviceName}`);
  }

  const headers = {
    'Content-Type': 'application/json',
    ...(authToken ? { Authorization: `Bearer ${authToken}` } : {}),
    ...(options.headers || {}),
  };

  const response = await fetch(`${baseUrl}${endpoint}`, {
    ...options,
    headers,
  });

  if (!response.ok) {
    throw new Error(`Error ${response.status} al comunicarse con ${serviceName}`);
  }

  return response.json();
}
