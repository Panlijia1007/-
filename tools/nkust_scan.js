// 掃描高科大教學平台：行事曆事件 + 各課未繳作業。帳密取自環境變數 NKUST_USER / NKUST_PASS，不輸出密碼、不存 session。
const { chromium } = require('playwright');
const BASE = 'https://elearning.nkust.edu.tw';
(async () => {
  const b = await chromium.launch(); const ctx = await b.newContext(); const p = await ctx.newPage();
  const J = async u => { const r = await p.request.get(BASE + u); try { return await r.json(); } catch { return {}; } };
  const login = async () => {
    await p.goto(BASE + '/moocs/#/home', { waitUntil: 'networkidle', timeout: 60000 });
    if ((await J('/api/v1/me/information')).data) return true;
    await p.locator('button:visible', { hasText: /Login|登入/ }).first().click();
    await p.waitForSelector('#account', { state: 'visible' });
    await p.fill('#account', process.env.NKUST_USER); await p.fill('#password', process.env.NKUST_PASS);
    const resp = p.waitForResponse(r => r.url().includes('/api/v1/auth/login'), { timeout: 20000 }).catch(() => null);
    // 點登入對話框裡的送出按鈕（與帳密欄位同一個 form）
    const submit = p.locator('form:has(#password) button[type=submit]');
    if (await submit.count()) await submit.first().click(); else await p.locator('#password').press('Enter');
    const lr = await resp;
    console.error('login request', lr ? lr.status() : 'not sent');
    await p.waitForTimeout(3000);
    return !!(await J('/api/v1/me/information')).data;
  };
  let ok = false; for (let i = 0; i < 3 && !ok; i++) { ok = await login(); if (!ok) await p.waitForTimeout(5000); }
  if (!ok) { console.log(JSON.stringify({ error: 'login failed' })); process.exit(1); }
  const seen = new Set();
  const out = { scanned_at: new Date().toISOString(), calendar: [], assignments: [] };
  const now = new Date();
  for (let k = 0; k < 3; k++) {            // 本月 + 未來兩個月
    const d = new Date(now.getFullYear(), now.getMonth() + k, 1); const y = d.getFullYear(), m = d.getMonth() + 1;
    for (const day of (await J(`/api/v1/me/calendar/day?year=${y}&month=${m}`)).data?.day || [])
      for (const e of (await J(`/api/v1/me/calendar/day/event?year=${y}&month=${m}&day=${day}`)).data?.list || [])
        out.calendar.push({ subject: e.subject, begin: e.begin_time, end: e.end_time, course: e.source });
  }
  let courses = []; for (let off = 0; off < 90; off += 15) { const c = await J(`/api/v1/courses?offset=${off}&size=15&purpose=learn&sort=new&apply_status=registered&direction=desc&keyword=`); courses = courses.concat(c.data || []); if (!(c.data || []).length) break; }
  const open = courses.filter(c => c.course_status === 'open' && c.todo);
  const sem = open.map(c => (c.name.match(/^(\d{4})_/) || [])[1]).filter(Boolean).sort().pop();            // 最新學期代碼，例如 1151
  for (const c of open.filter(c => c.name.startsWith(sem))) {
    await p.request.post(`${BASE}/api/v1/courses/${c.course_id}/log`, { data: {} });
    const got = await J('/api/v1/assignment');
    for (const a of got?.data?.list || []) { if (a.course_id !== c.course_id || seen.has(a.exam_id)) continue; seen.add(a.exam_id);
      out.assignments.push({ course: a.course_name, title: a.title, begin: a.answer_begin_time, close: a.answer_close_time,
        submitted: a.answer_process !== 'none', reupload_until: a.reuploadable ? a.reupload_close_time : null }); }
  }
  console.log(JSON.stringify(out, null, 1)); await b.close();
})();
