// Test double: records start/stop calls and lets a test fire recogniser events.
type Handler = (e: any) => void;
const handlers: Record<string, Handler[]> = {};
export const ExpoSpeechRecognitionModule = {
  requestPermissionsAsync: jest.fn(async () => ({ granted: true })),
  start: jest.fn(),
  stop: jest.fn(),
};
export function useSpeechRecognitionEvent(name: string, fn: Handler) {
  (handlers[name] ??= []).push(fn); // every render registers; emit() calls the latest one
}
export function __emit(name: string, e: any) {
  const list = handlers[name] || [];
  if (list.length)
    list[list.length - 1](e);
}
