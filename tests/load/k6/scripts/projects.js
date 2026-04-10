/**
 * k6 load test: Project operations.
 */

import http from "k6/http";
import { check, group, sleep } from "k6";

const BASE_URL = __ENV.TARGET_URL || "http://localhost:8000";
const ADMIN_USER = __ENV.ADMIN_USER || "admin";
const ADMIN_PASS = __ENV.ADMIN_PASS || "admin123";

export const options = {
  vus: __ENV.K6_VUS ? parseInt(__ENV.K6_VUS) : 10,
  duration: __ENV.K6_DURATION || "30s",
  thresholds: {
    http_req_duration: ["p(95)<500"],
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
  group("List Projects", function () {
    const res = http.get(`${BASE_URL}/api/projects`, authHeaders(data));
    check(res, {
      "list projects 200": (r) => r.status === 200,
    });
  });

  group("Create Project", function () {
    const name = `k6_project_${Date.now()}_${__VU}`;
    const res = http.post(
      `${BASE_URL}/api/projects`,
      JSON.stringify({ name: name, description: "k6 load test project" }),
      authHeaders(data)
    );
    check(res, {
      "create project success": (r) => r.status === 200 || r.status === 201,
    });
  });

  group("List Roles", function () {
    const res = http.get(`${BASE_URL}/api/roles`, authHeaders(data));
    check(res, {
      "list roles ok": (r) => r.status === 200 || r.status === 404,
    });
  });

  sleep(1);
}
