import { render, screen } from '@testing-library/react';
import App from './App';

const nextRace = {
  next_race: { year: 2026, round: 21, raceName: 'Las Vegas Grand Prix', circuitName: 'Las Vegas Strip Street Circuit', date: '2026-11-22' },
  last_race: { year: 2026, round: 20, raceName: 'Brazilian Grand Prix' },
  quali_available: false,
  warnings: [],
  lineup: [{ driverRef: 'norris', name: 'Lando Norris', team: 'McLaren' }],
};

beforeEach(() => {
  global.fetch = jest.fn(() => Promise.resolve({ ok: true, json: () => Promise.resolve(nextRace) }));
});

test('renders the prediction home page with the next race', async () => {
  render(<App />);
  expect(screen.getByText(/F1 Predictions/i)).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Predict Winner/i })).toBeInTheDocument();
  expect(screen.getByRole('button', { name: /Race Order/i })).toBeInTheDocument();
  expect(await screen.findByText(/2026 Las Vegas Grand Prix/i)).toBeInTheDocument();
  expect(screen.getByText(/Results through the 2026 Brazilian Grand Prix/i)).toBeInTheDocument();
});
