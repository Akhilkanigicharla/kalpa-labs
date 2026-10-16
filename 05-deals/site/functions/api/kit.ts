// GET /api/kit?p=pay_…  → { state: pending | review | paid | invalid, copyUrl? }  (the thank-you page polls this)
import { deliveryStatus } from "../../src/lib/delivery";
import { envOf, noStore, type CfEnv } from "./_store";
export const onRequestGet = async ({ request, env }: { request: Request; env: CfEnv }) => {
  const p = new URL(request.url).searchParams.get("p") || "";
  return Response.json(await deliveryStatus(p, envOf(env)), { headers: noStore });
};
