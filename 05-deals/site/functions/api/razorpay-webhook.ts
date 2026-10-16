// POST /api/razorpay-webhook  (Razorpay Dashboard → Webhooks → this URL; events: payment.captured, order.paid)
import { handleWebhook } from "../../src/lib/delivery";
import { envOf, noStore, type CfEnv } from "./_store";
export const onRequestPost = async ({ request, env }: { request: Request; env: CfEnv }) => {
  const raw = await request.text(); // the RAW body: signatures are over these exact bytes
  const r = await handleWebhook(raw, request.headers.get("x-razorpay-signature") || "", request.headers.get("x-razorpay-event-id") || "", envOf(env));
  return new Response(r.result, { status: r.status, headers: noStore });
};
