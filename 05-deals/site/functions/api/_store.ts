// Cloudflare KV as the order log (free tier). Binding name: KITS_KV (set in Cloudflare Pages → Settings → Functions).
import type { Env, Store } from "../../src/lib/delivery";
export interface CfEnv { KITS_KV?: { get(k: string): Promise<string | null>; put(k: string, v: string): Promise<void> }; RAZORPAY_WEBHOOK_SECRET?: string; KIT_COPY_URLS?: string }
export function envOf(cf: CfEnv): Env {
  const kv = cf.KITS_KV;
  const store: Store = kv ? { get: (k) => kv.get(k), put: (k, v) => kv.put(k, v) } : { get: async () => null, put: async () => { throw new Error("KITS_KV binding missing"); } };
  return { RAZORPAY_WEBHOOK_SECRET: cf.RAZORPAY_WEBHOOK_SECRET, KIT_COPY_URLS: cf.KIT_COPY_URLS, store };
}
export const noStore = { "Cache-Control": "no-store", "X-Robots-Tag": "noindex" };
