/**
 * k6 load test: Authentication flow.
 *
 * Custom metrics: login_failure_rate, login_duration
 * Thresholds: p(95) < 500ms
 */

import http from "k6/http";
import { check, sleep } from "k6";
import { Rate, Trend } from "k6/metrics";

const BASE_URL = __ENV.TARGET_URL || "http://localhost:8000";
const ADMIN_USER = __ENV.ADMIN_USER || "admin";
const ADMIN_PASS = __ENV.ADMIN_PASS || "admin123";

const loginFailureRate = new Rate("login_failure_rate");
const loginDuration = new Trend("login_duration");

export const options = {
  vus: __ENV.K6_VUS ? parseInt(__ENV.K6_VUS) : 10,
  duration: __ENV.K6_DURATION || "30s",
  thresholds: {
    http_req_duration: ["p(95)<500"],
    login_failure_rate: ["rate<0.1"],
  },
};

export default function () {
  // Successful login
  const loginStart = Date.now();
  const loginRes = http.post(
    `${BASE_URL}/api/auth/login`,
    JSON.stringify({ username: ADMIN_USER, password: ADMIN_PASS }),
    { headers: { "Content-Type": "application/json" } }
  );
  loginDuration.add(Date.now() - loginStart);

  const loginOk = check(loginRes, {
    "login status 200": (r) => r.status === 200,
    "has access_token": (r) => r.json("access_token") !== undefined,
  });
  loginFailureRate.add(!loginOk);

  // Health check
  const healthRes = http.get(`${BASE_URL}/api/health`);
  check(healthRes, {
    "health status 200": (r) => r.status === 200,
  });

  sleep(1);
}
