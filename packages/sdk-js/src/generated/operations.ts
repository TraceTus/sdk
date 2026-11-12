/**
 * Generated from apps/api/openapi.json. Do not edit by hand: run
 * `pnpm --filter @tracetus/sdk generate`.
 *
 * Which method and which path each operation name means. The types in
 * `openapi.ts` say what goes in and what comes out; this says where to send it.
 */

export interface OperationRoute {
  method: string;
  path: string;
  /** What the route answers on success, from the document. */
  media: string;
}

export const OPERATIONS: Readonly<Record<string, OperationRoute>> = {
  "connectors.addDevice": { method: "POST", path: "/v1/connectors/{id}/devices", media: "application/json" },
  "connectors.create": { method: "POST", path: "/v1/connectors", media: "application/json" },
  "connectors.disable": { method: "POST", path: "/v1/connectors/{id}/disable", media: "application/json" },
  "connectors.list": { method: "GET", path: "/v1/connectors", media: "application/json" },
  "connectors.listDevices": { method: "GET", path: "/v1/connectors/{id}/devices", media: "application/json" },
  "connectors.removeDevice": { method: "DELETE", path: "/v1/connectors/{id}/devices/{deviceId}", media: "application/json" },
  "health.get": { method: "GET", path: "/health", media: "application/json" },
  "metrics.get": { method: "GET", path: "/v1/metrics", media: "text/plain" },
  "privateContent.create": { method: "POST", path: "/v1/private-content", media: "application/json" },
  "privateContent.erase": { method: "DELETE", path: "/v1/private-content/{id}", media: "application/json" },
  "privateContent.get": { method: "GET", path: "/v1/private-content/{id}", media: "application/json" },
  "privateContent.list": { method: "GET", path: "/v1/private-content", media: "application/json" },
  "records.create": { method: "POST", path: "/v1/records", media: "application/json" },
  "records.createBatch": { method: "POST", path: "/v1/records/batch", media: "application/json" },
  "records.get": { method: "GET", path: "/v1/records/{id}", media: "application/json" },
  "verify.get": { method: "GET", path: "/v1/verify/{id}", media: "application/json" },
};
