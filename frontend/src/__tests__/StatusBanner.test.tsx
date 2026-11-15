import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { StatusBanner } from '../components/StatusBanner';

describe('StatusBanner', () => {
  it('renders error message and details', () => {
    render(
      <StatusBanner
        message="Location not found"
        detail="Please verify the city or postal code."
      />
    );

    expect(screen.getByText('Location not found')).toBeInTheDocument();
    expect(screen.getByText('Please verify the city or postal code.')).toBeInTheDocument();
  });

  it('calls onDismiss when close button is clicked', () => {
    const handleDismiss = vi.fn();
    render(
      <StatusBanner
        message="Route failure"
        onDismiss={handleDismiss}
      />
    );

    const closeBtn = screen.getByTitle('Dismiss');
    fireEvent.click(closeBtn);
    expect(handleDismiss).toHaveBeenCalledTimes(1);
  });
});
