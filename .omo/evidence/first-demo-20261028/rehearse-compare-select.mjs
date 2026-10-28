const fs = await import('node:fs/promises');
const out = '/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028';
const task = await taskSpace(91), page = task.page('p1');
await page.cdp('Emulation.setDeviceMetricsOverride',{width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await page.waitForFunction(() => document.body.dataset.desktopShell === 'bounded');
for (const index of [0,1]) {
  const snapshot = await page.snapshot();
  if (typeof snapshot !== 'string') throw new Error('Inspect snapshot result type before choosing a control');
  const refs = [...snapshot.matchAll(/button "재생" \[ref=(\d+)/g)].map(match => match[1]);
  console.log({stage:'native-comparison-control',index,playRefs:refs});
  if (refs.length !== 2) throw new Error('Inspect current native comparison controls');
  await page.click('@'+refs[index]);
  await page.waitForFunction(i => {const video=document.querySelectorAll('#compareDialog video')[i];return !video.paused && video.currentTime>1.2;},index,{timeout:8000});
  await page.keyboard.press('Space');
}
await page.screenshot({path:out+'/rehearsal-take-comparison.png'});
await fs.writeFile(out+'/rehearsal-comparison-playback.json',JSON.stringify(await page.evaluate(() => [...document.querySelectorAll('#compareDialog video')].map(v=>({src:v.currentSrc,time:v.currentTime,paused:v.paused}))),null,2));
await page.click('#compareDialog [data-close]');
await page.click('#takes [data-take="2"]');
await page.waitForFunction(() => !document.querySelector('#creatorTakeRights').hidden);
await page.fill('#creatorTakeRightsEvidence','직접 입력한 수정 문구와 플랫폼 모션 원본으로 제작한 시연 후보');
await page.click('#creatorTakeRightsSubmit');
await page.waitForFunction(() => document.querySelector('#creatorTakeRights').hidden);
await page.fill('#reviewReason','문구·크기·색·위치·표시시간 수정이 새 영상에 반영된 것을 비교했습니다.');
await page.selectOption('#takeDecision',{value:'approved'});
await page.click('#reviewTake');
await page.waitForFunction(() => document.querySelector('#creatorReviewEditor').hidden);
console.log({stage:'take2-reviewed'});
