import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { TripForm } from '../components/TripForm';

describe('TripForm', () => {
  it('renders default input fields and preset buttons', () => {
    const handleSubmit = vi.fn();
    render(<TripForm onSubmit={handleSubmit} isLoading={false} />);

    expect(screen.getByLabelText(/Origin/i)).toHaveValue('Chicago, IL');
    expect(screen.getByLabelText(/Destination/i)).toHaveValue('Dallas, TX');
    expect(screen.getByLabelText(/Gross Weight/i)).toHaveValue(42000);
    expect(screen.getByRole('button', { name: /ANALYZE ROUTE/i })).toBeInTheDocument();
  });

  it('swaps origin and destination when swap button is clicked', () => {
    const handleSubmit = vi.fn();
    render(<TripForm onSubmit={handleSubmit} isLoading={false} />);

    const swapButton = screen.getByTitle(/Swap Origin and Destination/i);
    fireEvent.click(swapButton);

    expect(screen.getByLabelText(/Origin/i)).toHaveValue('Dallas, TX');
    expect(screen.getByLabelText(/Destination/i)).toHaveValue('Chicago, IL');
  });

  it('validates empty origin and destination', () => {
    const handleSubmit = vi.fn();
    render(<TripForm onSubmit={handleSubmit} isLoading={false} />);

    const originInput = screen.getByLabelText(/Origin/i);
    const destInput = screen.getByLabelText(/Destination/i);

    fireEvent.change(originInput, { target: { value: '' } });
    fireEvent.change(destInput, { target: { value: '' } });

    const submitBtn = screen.getByRole('button', { name: /ANALYZE ROUTE/i });
    fireEvent.click(submitBtn);

    expect(handleSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/Origin location is required/i)).toBeInTheDocument();
  });

  it('validates identical origin and destination', () => {
    const handleSubmit = vi.fn();
    render(<TripForm onSubmit={handleSubmit} isLoading={false} />);

    const destInput = screen.getByLabelText(/Destination/i);
    fireEvent.change(destInput, { target: { value: 'Chicago, IL' } });

    const submitBtn = screen.getByRole('button', { name: /ANALYZE ROUTE/i });
    fireEvent.click(submitBtn);

    expect(handleSubmit).not.toHaveBeenCalled();
    expect(screen.getByText(/Destination cannot match origin/i)).toBeInTheDocument();
  });

  it('submits valid form data with selected checkpoint interval', () => {
    const handleSubmit = vi.fn();
    render(<TripForm onSubmit={handleSubmit} isLoading={false} />);

    // Select 50 mi interval
    const interval50 = screen.getByText('50 mi');
    fireEvent.click(interval50);

    const submitBtn = screen.getByRole('button', { name: /ANALYZE ROUTE/i });
    fireEvent.click(submitBtn);

    expect(handleSubmit).toHaveBeenCalledTimes(1);
    const submittedData = handleSubmit.mock.calls[0][0];
    expect(submittedData.origin).toBe('Chicago, IL');
    expect(submittedData.destination).toBe('Dallas, TX');
    expect(submittedData.checkpoint_interval_miles).toBe(50);
    expect(submittedData.weight_lbs).toBe(42000);
  });
});
