/**
 * k6 load test: Full combined scenario.
 *
 * Custom metrics: error_rate, auth_duration, member_operations
 * Scenarios config with ramping VUs.
 */

import http from "k6/http";
import { check, group, sleep } from "k6";
import { Counter, Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.TARGET_URL || "http://localhost:8000";
const ADMIN_USER = __ENV.ADMIN_USER || "admin";
const ADMIN_PASS = __ENV.ADMIN_PASS || "admin123";

const errorRate = new Rate("error_rate");
const authDuration = new Trend("auth_duration");
const memberOperations = new Counter("member_operations");

export const options = {
  scenarios: {
    full_load: {
      executor: "ramping-vus",
      startVUs: 1,
      stages: [
        { duration: "10s", target: 5 },
        { duration: "20s", target: 10 },
        { duration: "10s", target: 0 },
      ],
    },
  },
  thresholds: {
    http_req_duration: ["p(95)<500"],
    error_rate: ["rate<0.1"],
    http_req_failed: ["rate<0.1"],
  },
};

export function setup() {
  const res = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ username: ADMIN_USER, password: ADMIN_PASS }),
    { headers: { "Content-Type": "application/json" } }
  );
  return { token: res.json("access_token") };
}

function authHeaders(data) {
  return {
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${data.token}`,
    },
  };
}

export default function (data) {
  // Auth
  group("Authentication", function () {
    const start = Date.now();
    const res = http.post(
      `${BASE_URL}/api/auth/login`,
      JSON.stringify({ username: ADMIN_USER, password: ADMIN_PASS }),
      { headers: { "Content-Type": "application/json" } }
    );
    authDuration.add(Date.now() - start);
    const ok = check(res, { "auth ok": (r) => r.status === 200 });
    errorRate.add(!ok);
  });

  // Members
  group("Members", function () {
    const res = http.get(`${BASE_URL}/api/members`, authHeaders(data));
    const ok = check(res, { "list members ok": (r) => r.status === 200 });
    errorRate.add(!ok);
    memberOperations.add(1);
  });

  // Projects
  group("Projects", function () {
    const res = http.get(`${BASE_URL}/api/projects`, authHeaders(data));
    const ok = check(res, { "list projects ok": (r) => r.status === 200 });
    errorRate.add(!ok);
  });

  // Health
  group("Health", function () {
    const res = http.get(`${BASE_URL}/api/health`);
    check(res, { "health ok": (r) => r.status === 200 });
  });

  sleep(1);
}
