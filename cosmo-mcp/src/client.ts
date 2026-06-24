/**
 * Client HTTP pour l'API REST ERPNext cosmo_erp.
 * Gère l'authentification API Key, les retries et les erreurs.
 */
import axios, { AxiosInstance, AxiosError } from 'axios';
import { ErpNextResponse } from './types';

const MAX_RETRIES = 3;
const RETRY_DELAY_MS = 1000;

class ErpNextClient {
  private client: AxiosInstance;
  private baseUrl: string;

  constructor() {
    const url = process.env.ERPNEXT_URL;
    const apiKey = process.env.ERPNEXT_API_KEY;
    const apiSecret = process.env.ERPNEXT_API_SECRET;

    if (!url || !apiKey || !apiSecret) {
      throw new Error(
        'Variables manquantes : ERPNEXT_URL, ERPNEXT_API_KEY, ERPNEXT_API_SECRET'
      );
    }

    this.baseUrl = url.replace(/\/$/, '');

    this.client = axios.create({
      baseURL: this.baseUrl,
      headers: {
        Authorization: `token ${apiKey}:${apiSecret}`,
        'Content-Type': 'application/json',
        Accept: 'application/json',
        Expect: '',  // désactive Expect: 100-continue rejeté par Nginx
      },
      timeout: 30000,
    });
  }

  /**
   * Appelle un endpoint cosmo_erp via POST /api/method/cosmo_erp.cosmo_erp.api.main.<method>
   */
  async call<T = unknown>(
    method: string,
    params: Record<string, unknown> = {}
  ): Promise<T> {
    const url = `/api/method/cosmo_erp.cosmo_erp.api.main.${method}`;
    let lastError: Error | null = null;

    for (let attempt = 1; attempt <= MAX_RETRIES; attempt++) {
      try {
        const response = await this.client.post<ErpNextResponse<T>>(url, params);
        return response.data.message as T;
      } catch (err) {
        const axiosErr = err as AxiosError<{ exc?: string; message?: string; _error_message?: string }>;
        lastError = this._parseError(axiosErr, method);

        // Pas de retry sur les erreurs client (4xx)
        if (axiosErr.response?.status && axiosErr.response.status < 500) {
          throw lastError;
        }

        if (attempt < MAX_RETRIES) {
          await this._sleep(RETRY_DELAY_MS * attempt);
        }
      }
    }
    throw lastError!;
  }

  private _parseError(err: AxiosError<{ exc?: string; message?: string; _error_message?: string }>, method: string): Error {
    if (err.response) {
      const data = err.response.data;
      const msg =
        data?._error_message ||
        data?.message ||
        `Erreur ERPNext ${err.response.status} sur ${method}`;
      return new Error(msg);
    }
    if (err.request) {
      return new Error(`ERPNext inaccessible — vérifier ERPNEXT_URL (${method})`);
    }
    return new Error(`Erreur réseau inattendue (${method}): ${err.message}`);
  }

  private _sleep(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }
}

// Singleton
let _client: ErpNextClient | null = null;

export function getClient(): ErpNextClient {
  if (!_client) {
    _client = new ErpNextClient();
  }
  return _client;
}

export { ErpNextClient };
