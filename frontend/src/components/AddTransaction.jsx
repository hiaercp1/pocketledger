import { useState } from 'react';

/**
 * AddTransaction — F1 form for creating a new transaction.
 *
 * @prop {function(payload: {amount: string, description: string, category: string, date: string}): Promise<void>} onAdd
 *   Called with the validated payload on form submission. Should throw on API error.
 */
export default function AddTransaction({ onAdd }) {
  const today = new Date().toISOString().slice(0, 10);

  const [type, setType] = useState('income'); // 'income' | 'expense'
  const [amount, setAmount] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('');
  const [date, setDate] = useState(today);
  const [error, setError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // --- Validation ---
    const trimmedAmount = amount.trim();
    if (!trimmedAmount) {
      setError('Amount is required.');
      return;
    }
    // Accept numeric with up to 2 decimal places, no sign (sign comes from type toggle)
    const numericValue = trimmedAmount.replace(/\./g, '').replace(/^0+/, '') || '0';
    if (!/^\d+(\.\d{1,2})?$/.test(trimmedAmount) || numericValue === '0') {
      setError('Amount must be a positive number with at most 2 decimal places.');
      return;
    }
    if (!description.trim()) {
      setError('Description is required.');
      return;
    }
    if (!category.trim()) {
      setError('Category is required.');
      return;
    }
    if (!date) {
      setError('Date is required.');
      return;
    }

    // Sign: expense → negative
    const signedAmount = type === 'expense' ? `-${trimmedAmount}` : trimmedAmount;

    try {
      setSubmitting(true);
      await onAdd({
        amount: signedAmount,
        description: description.trim(),
        category: category.trim(),
        date,
      });
      // Clear on success
      setAmount('');
      setDescription('');
      setCategory('');
      setDate(today);
      setType('income');
    } catch (err) {
      setError(`Submission failed: ${err.message}`);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="add-form" onSubmit={handleSubmit} noValidate>
      {error && <p className="add-form__error">{error}</p>}

      <div className="add-form__type-toggle">
        <label className={`type-btn${type === 'income' ? ' type-btn--active type-btn--income' : ''}`}>
          <input
            type="radio"
            name="type"
            value="income"
            checked={type === 'income'}
            onChange={() => setType('income')}
          />
          Income
        </label>
        <label className={`type-btn${type === 'expense' ? ' type-btn--active type-btn--expense' : ''}`}>
          <input
            type="radio"
            name="type"
            value="expense"
            checked={type === 'expense'}
            onChange={() => setType('expense')}
          />
          Expense
        </label>
      </div>

      <div className="add-form__fields">
        <label className="field">
          <span className="field__label">Amount</span>
          <input
            className="field__input"
            type="text"
            inputMode="decimal"
            placeholder="0.00"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </label>

        <label className="field">
          <span className="field__label">Description</span>
          <input
            className="field__input"
            type="text"
            placeholder="What was this for?"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            maxLength={200}
            required
          />
        </label>

        <label className="field">
          <span className="field__label">Category</span>
          <input
            className="field__input"
            type="text"
            placeholder="e.g. Food, Salary"
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            maxLength={200}
            required
          />
        </label>

        <label className="field">
          <span className="field__label">Date</span>
          <input
            className="field__input"
            type="date"
            value={date}
            onChange={(e) => setDate(e.target.value)}
            required
          />
        </label>
      </div>

      <button className="btn btn--primary" type="submit" disabled={submitting}>
        {submitting ? 'Adding…' : 'Add Transaction'}
      </button>
    </form>
  );
}
