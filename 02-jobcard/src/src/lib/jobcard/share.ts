// Bill → PDF on the phone (expo-print renders the bilingual HTML; the WebView shapes Telugu correctly)
// → the share sheet, where the technician picks WhatsApp and the customer.
import type { InvoiceMeta, Totals } from '@core/invoice.mjs';
import { invoiceHTML } from '@core/invoice.mjs';
import * as Print from 'expo-print';
import * as Sharing from 'expo-sharing';

export async function shareBill(meta: InvoiceMeta, totals: Totals, { qrSvg = '' } = {}): Promise<{ uri: string; shared: boolean }> {
  const { uri } = await Print.printToFileAsync({ html: invoiceHTML(meta, totals, { qrSvg }), width: 595, height: 842 });
  if (!(await Sharing.isAvailableAsync()))
    return { uri, shared: false };
  await Sharing.shareAsync(uri, { mimeType: 'application/pdf', UTI: 'com.adobe.pdf', dialogTitle: meta.number });
  return { uri, shared: true };
}
