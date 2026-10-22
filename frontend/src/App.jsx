import React from 'react';
import { useAuth } from './hooks/useAuth.js';
import { useTransactions } from './hooks/useTransactions.js';
import { LoginView } from './components/auth/LoginView.jsx';
import { DashboardView } from './components/dashboard/DashboardView.jsx';

export function App() {
  const {
    user,
    isAuthenticated,
    email,
    password,
    isLoading: isAuthLoading,
    error: authError,
    handleEmailChange,
    handlePasswordChange,
    handleLogin,
    handleLogout,
  } = useAuth();

  const {
    transactions,
    isLoading: isTransactionsLoading,
    error: transactionsError,
    amount,
    category,
    date,
    isSubmitting: isSubmittingTransaction,
    submitError: submitTransactionError,
    handleAmountChange,
    handleCategoryChange,
    handleDateChange,
    handleCreateTransaction,
  } = useTransactions(isAuthenticated);

  if (!isAuthenticated) {
    return (
      <LoginView
        email={email}
        password={password}
        isLoading={isAuthLoading}
        error={authError}
        onEmailChange={handleEmailChange}
        onPasswordChange={handlePasswordChange}
        onSubmit={handleLogin}
      />
    );
  }

  return (
    <DashboardView
      user={user}
      transactions={transactions}
      isLoadingTransactions={isTransactionsLoading}
      transactionsError={transactionsError}
      amount={amount}
      category={category}
      date={date}
      isSubmittingTransaction={isSubmittingTransaction}
      submitTransactionError={submitTransactionError}
      onAmountChange={handleAmountChange}
      onCategoryChange={handleCategoryChange}
      onDateChange={handleDateChange}
      onCreateTransaction={handleCreateTransaction}
      onLogout={handleLogout}
    />
  );
}
