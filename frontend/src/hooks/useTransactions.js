import { useState, useEffect, useCallback } from 'react';
import { transactionService } from '../services/transactionService.js';

const getTodayIso = () => new Date().toISOString().slice(0, 10);

/**
 * Hook de estado para el listado y registro de transacciones del usuario.
 * Centraliza la carga y creación a través de `transactionService` sin mezclar estado en el JSX.
 */
export function useTransactions(enabled = true) {
  const [transactions, setTransactions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const [amount, setAmount] = useState('');
  const [category, setCategory] = useState('');
  const [date, setDate] = useState(getTodayIso);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState(null);

  const loadTransactions = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      const items = await transactionService.getTransactions();
      setTransactions(items);
    } catch (err) {
      setError(err.message || 'No se pudieron cargar las transacciones.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      loadTransactions();
    } else {
      setTransactions([]);
    }
  }, [enabled, loadTransactions]);

  const handleAmountChange = useCallback((event) => {
    setAmount(event.target.value);
  }, []);

  const handleCategoryChange = useCallback((event) => {
    setCategory(event.target.value);
  }, []);

  const handleDateChange = useCallback((event) => {
    setDate(event.target.value);
  }, []);

  const handleCreateTransaction = useCallback(
    async (event) => {
      event.preventDefault();
      setIsSubmitting(true);
      setSubmitError(null);

      try {
        const normalizedAmount = String(amount).replace(/\./g, '').replace(',', '.');
        await transactionService.createTransaction({
          amount: normalizedAmount,
          category,
          date,
        });
        setAmount('');
        setCategory('');
        await loadTransactions();
      } catch (err) {
        setSubmitError(err.message || 'No se pudo registrar el gasto.');
      } finally {
        setIsSubmitting(false);
      }
    },
    [amount, category, date, loadTransactions]
  );

  return {
    transactions,
    isLoading,
    error,
    amount,
    category,
    date,
    isSubmitting,
    submitError,
    handleAmountChange,
    handleCategoryChange,
    handleDateChange,
    handleCreateTransaction,
    reloadTransactions: loadTransactions,
  };
}
