// GET /api/kit-guide?p=pay_…  → the buyer's stamped PDF guide (only for a paid order)
import { deliveryStatus, stampedGuide } from "../../src/lib/delivery";
import { envOf, noStore, type CfEnv } from "./_store";
export const onRequestGet = async ({ request, env }: { request: Request; env: CfEnv }) => {
  const p = new URL(request.url).searchParams.get("p") || ""; const e = envOf(env);
  const s = await deliveryStatus(p, e);
  if (s.state !== "paid") return new Response("Not available", { status: 404, headers: noStore });
  const order = JSON.parse((await e.store.get(`pay:${p}`))!);
  const pdf = await stampedGuide({ kit: s.kit, tier: s.tier, email: order.email, paymentId: p });
  return new Response(pdf, { headers: { ...noStore, "Content-Type": "application/pdf", "Content-Disposition": `attachment; filename="${s.kit}-guide.pdf"` } });
};
