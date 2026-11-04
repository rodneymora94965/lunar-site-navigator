/* Funciones puras del navegador: geometria, potencia y horizonte. Se prueban con tests/test_core_node.py. */
const CORE = (() => {
  const RAD = Math.PI / 180, R_KM = 1737.4, R_M = 1737400, AU_KM = 149597870.7, SUN_R_KM = 696000, S0 = 1361;
  function basis(latDeg, lonDeg) {
    const la = latDeg * RAD, lo = lonDeg * RAD, sl = Math.sin(la), cl = Math.cos(la), so = Math.sin(lo), co = Math.cos(lo);
    return { E: [-so, co, 0], N: [-sl * co, -sl * so, cl], U: [cl * co, cl * so, sl] };
  }
  /* Azimut (grados desde el norte hacia el este) y elevacion de un punto dado por su subpunto lunar y distancia. */
  function azEl(b, subLat, subLon, distKm) {
    const la = subLat * RAD, lo = subLon * RAD, c = Math.cos(la);
    const x = distKm * c * Math.cos(lo) - b.U[0] * R_KM, y = distKm * c * Math.sin(lo) - b.U[1] * R_KM, z = distKm * Math.sin(la) - b.U[2] * R_KM;
    const d = Math.hypot(x, y, z), up = x * b.U[0] + y * b.U[1] + z * b.U[2];
    const e = x * b.E[0] + y * b.E[1] + z * b.E[2], n = x * b.N[0] + y * b.N[1] + z * b.N[2];
    const az = Math.atan2(e, n) / RAD;
    return [az < 0 ? az + 360 : az, Math.asin(Math.max(-1, Math.min(1, up / d))) / RAD];
  }
  function interpHz(hz, az) { const n = hz.length, a = (((az % 360) + 360) % 360) * n / 360, i = Math.floor(a), f = a - i; return hz[i % n] * (1 - f) + hz[(i + 1) % n] * f; }
  function sunRadiusDeg(dAU) { return Math.atan(SUN_R_KM / (dAU * AU_KM)) / RAD; }
  /* Fraccion visible de un disco de radio r cuyo centro esta m grados sobre un horizonte recto. */
  function discFraction(m, r) {
    if (m >= r) return 1;
    if (m <= -r) return 0;
    const d = Math.abs(m) / r, seg = (Math.acos(d) - d * Math.sqrt(1 - d * d)) / Math.PI;
    return m >= 0 ? 1 - seg : seg;
  }
  /* Modelo simple: panel que sigue al Sol en azimut, vertical. P = S0 / d^2 * A * eficiencia * fraccion * cos(elev). */
  function powerW(dAU, frac, elDeg, area, eff) { return S0 / (dAU * dAU) * area * eff * frac * Math.max(0, Math.cos(elDeg * RAD)); }
  function longestFalse(mask, a, b) { let best = 0, cur = 0; for (let i = a; i < b; i++) { cur = mask[i] ? 0 : cur + 1; if (cur > best) best = cur; } return best; }
  function xyFromLatLon(lat, lon) { const rho = 2 * R_M * Math.tan((90 + lat) * RAD / 2), l = lon * RAD; return [rho * Math.sin(l), rho * Math.cos(l)]; }
  function latLonFromXY(x, y) { const rho = Math.hypot(x, y); return [-90 + 2 * Math.atan(rho / (2 * R_M)) / RAD, Math.atan2(x, y) / RAD]; }
  function bil(g, x, y) {
    const j = (x - g.x0) / g.d - 0.5, i = (g.y0 - y) / g.d - 0.5;
    if (!(i >= 0 && j >= 0 && i < g.h - 1 && j < g.w - 1)) return NaN;
    const i0 = Math.floor(i), j0 = Math.floor(j), fi = i - i0, fj = j - j0, k = i0 * g.w + j0, Z = g.Z;
    return Z[k] * (1 - fi) * (1 - fj) + Z[k + g.w] * fi * (1 - fj) + Z[k + 1] * (1 - fi) * fj + Z[k + g.w + 1] * fi * fj;
  }
  function zAt(dem, x, y) { const a = dem.fine ? bil(dem.fine, x, y) : NaN; return Number.isNaN(a) ? (dem.wide ? bil(dem.wide, x, y) : NaN) : a; }
  /* Mismo trazado que src/horizon2.py: rayos rectos en el plano polar con caida por curvatura r^2/2R. */
  function horizon(dem, x, y, hobs, naz, maxR) {
    const z0 = zAt(dem, x, y) + hobs, lam = Math.atan2(x, y), s = Math.sin(lam), c = Math.cos(lam), H = new Float32Array(naz);
    const fd = dem.fine ? dem.fine.d : dem.wide.d, wd = dem.wide ? dem.wide.d / 2 : fd, rays = [];
    for (let r = fd; r < 3000; r += fd) rays.push(r);
    for (let r = 3000; r < maxR; r += wd) rays.push(r);
    for (let k = 0; k < naz; k++) {
      const a = k * 2 * Math.PI / naz, dx = Math.cos(a) * s + Math.sin(a) * c, dy = Math.cos(a) * c - Math.sin(a) * s;
      let best = -Math.PI / 2, any = false;
      for (let m = 0; m < rays.length; m++) {
        const r = rays[m], z = zAt(dem, x + r * dx, y + r * dy);
        if (Number.isNaN(z)) continue;
        any = true;
        const t = (z - z0 - r * r / (2 * R_M)) / r;
        if (t > best) best = t;
      }
      H[k] = any ? Math.atan(best) / RAD : -90;
    }
    return H;
  }
  return { RAD, R_M, basis, azEl, interpHz, sunRadiusDeg, discFraction, powerW, longestFalse, xyFromLatLon, latLonFromXY, bil, zAt, horizon };
})();
if (typeof module !== 'undefined') module.exports = CORE;
