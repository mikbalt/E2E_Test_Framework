/**
 * k6 load test: Member CRUD operations.
 *
 * Uses setup() to obtain auth token, group() blocks for organization.
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
  group("List Members", function () {
    const res = http.get(`${BASE_URL}/api/members`, authHeaders(data));
    check(res, {
      "list members 200": (r) => r.status === 200,
      "returns array": (r) => Array.isArray(r.json()),
    });
  });

  group("Create and Delete Member", function () {
    const name = `k6_${Date.now()}_${__VU}`;
    const createRes = http.post(
      `${BASE_URL}/api/members`,
      JSON.stringify({
        username: name,
        email: `${name}@test.com`,
        role: "viewer",
      }),
      authHeaders(data)
    );

    if (createRes.status === 201 || createRes.status === 200) {
      const memberId = createRes.json("id");
      if (memberId) {
        const deleteRes = http.del(
          `${BASE_URL}/api/members/${memberId}`,
          null,
          authHeaders(data)
        );
        check(deleteRes, {
          "delete member success": (r) => r.status === 200 || r.status === 204,
        });
      }
    }
  });

  group("Get Member by ID", function () {
    const res = http.get(`${BASE_URL}/api/members/1`, authHeaders(data));
    check(res, {
      "get member status ok": (r) => r.status === 200 || r.status === 404,
    });
  });

  sleep(1);
}
