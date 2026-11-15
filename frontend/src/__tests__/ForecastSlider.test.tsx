import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { ForecastSlider } from '../components/ForecastSlider';

describe('ForecastSlider', () => {
  const departureTime = '2026-11-16T08:00:00Z';

  it('renders in ETA mode by default with proper indicator', () => {
    const handleChange = vi.fn();
    render(
      <ForecastSlider
        departureTime={departureTime}
        forecastOffsetHours={null}
        onChangeOffset={handleChange}
      />
    );

    expect(screen.getByText(/TRUCK ETA MODE/i)).toBeInTheDocument();
    expect(screen.getByText(/Dynamic ETA per Checkpoint/i)).toBeInTheDocument();
  });

  it('renders offset mode when hours specified and allows resetting to ETA', () => {
    const handleChange = vi.fn();
    render(
      <ForecastSlider
        departureTime={departureTime}
        forecastOffsetHours={12}
        onChangeOffset={handleChange}
      />
    );

    expect(screen.getByText('+12h SNAPSHOT')).toBeInTheDocument();
    expect(screen.getByText(/Reset to ETA/i)).toBeInTheDocument();

    const resetButton = screen.getByText(/Reset to ETA/i);
    fireEvent.click(resetButton);
    expect(handleChange).toHaveBeenCalledWith(null);
  });

  it('triggers change when slider is dragged', () => {
    const handleChange = vi.fn();
    render(
      <ForecastSlider
        departureTime={departureTime}
        forecastOffsetHours={0}
        onChangeOffset={handleChange}
      />
    );

    const slider = screen.getByRole('slider');
    fireEvent.change(slider, { target: { value: '24' } });

    expect(handleChange).toHaveBeenCalledWith(24);
  });

  it('triggers change when quick jump button is clicked', () => {
    const handleChange = vi.fn();
    render(
      <ForecastSlider
        departureTime={departureTime}
        forecastOffsetHours={null}
        onChangeOffset={handleChange}
      />
    );

    const jumpButton = screen.getByText('+36h');
    fireEvent.click(jumpButton);

    expect(handleChange).toHaveBeenCalledWith(36);
  });
});
