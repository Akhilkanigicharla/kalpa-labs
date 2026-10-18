import * as Print from 'expo-print';
import { ExpoSpeechRecognitionModule as Speech } from 'expo-speech-recognition';
import * as React from 'react';
import { migrate } from '@/lib/jobcard/db';
import { memoryDb } from '@/lib/jobcard/test-db';
import { act, fireEvent, render, screen, waitFor } from '@/lib/test-utils';
import { RecordScreen } from './record-screen';
import { resetDbForTests } from './use-job';

const emit = (name: string, e: unknown) => act(() => require('expo-speech-recognition').__emit(name, e));
jest.mock('@/lib/storage', () => ({
  storage: { getString: jest.fn(), set: jest.fn() },
  getItem: (k: string) => (k === 'technician' ? { id: 't1', name: 'Ravi', business_name: 'Ravi Cooling', phone: '9000022222', gst_kind: 'unregistered' } : null),
}));

jest.mock('expo-crypto', () => ({ randomUUID: () => require('node:crypto').randomUUID() }));
jest.mock('react-native-safe-area-context', () => ({ useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }) }));

beforeEach(async () => { const db = memoryDb(); await migrate(db); resetDbForTests(db); });

it('speak offline → card with prices → save on the phone → bill shared', async () => {
  render(<RecordScreen online={false} />);
  expect(screen.getByTestId('offline')).toBeOnTheScreen();
  fireEvent.press(screen.getByTestId('mic'));
  await waitFor(() => expect(Speech.start).toHaveBeenCalledWith(expect.objectContaining({ requiresOnDeviceRecognition: true })));
  emit('result', { isFinal: false, results: [{ transcript: 'split AC gas refill 2500' }] });
  expect(screen.getByTestId('total')).toHaveTextContent('₹2,500');
  emit('result', { isFinal: true, results: [{ transcript: 'split AC gas refill 2500, capacitor 450, total 3000, customer Sita 9000033333' }] });
  emit('end', {});
  expect(screen.getByTestId('total')).toHaveTextContent('₹2,950');
  expect(screen.getByTestId('spoke-total')).toBeOnTheScreen();
  expect(screen.getByText('Sita')).toBeOnTheScreen();

  fireEvent.press(screen.getByTestId('save'));
  expect(await screen.findByTestId('saved')).toBeOnTheScreen();
  expect(screen.getByTestId('sync')).toHaveTextContent(/2/); // customer + job card wait for signal

  fireEvent.press(screen.getByTestId('bill'));
  await waitFor(() => expect(screen.getByTestId('saved')).toHaveTextContent(/JC\/\d\d-\d\d\/0001/));
  expect(Print.printToFileAsync).toHaveBeenCalled();
  expect(screen.getByTestId('sync')).toHaveTextContent(/3/);
});

it('an unheard price shows "₹ ?" and blocks the bill', async () => {
  render(<RecordScreen />);
  fireEvent.changeText(screen.getByTestId('note'), 'capacitor, gas refill 2500');
  expect(screen.getByTestId('price-needed')).toHaveTextContent(/Capacitor/);
  expect(screen.getByText('₹ ?')).toBeOnTheScreen();
  fireEvent.press(screen.getByTestId('save'));
  await waitFor(() => expect(screen.getByTestId('bill')).toBeDisabled());
});
