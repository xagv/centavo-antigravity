import { requestService } from './apiClient.js';

/**
 * Capa de servicio para consultar y gestionar transacciones en `transactions-service`.
 */
export const transactionService = {
  async getTransactions() {
    const data = await requestService('transactions', '/transactions', {
      method: 'GET',
    });
    return Array.isArray(data) ? data : [];
  },

  async createTransaction({ amount, category, date }) {
    return requestService('transactions', '/transactions', {
      method: 'POST',
      body: JSON.stringify({
        amount: Number(amount),
        category,
        date,
      }),
    });
  },
};
