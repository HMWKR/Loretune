const task = await taskSpace(91);
const page = task.page('p1');
await page.cdp('Emulation.setDeviceMetricsOverride', {width:1920,height:1080,deviceScaleFactor:1,mobile:false});
await page.waitForFunction(() => document.body.dataset.desktopShell === 'bounded');
await page.evaluate(() => new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve))));
console.log(await page.evaluate(() => [...document.querySelector('dialog[open]').querySelectorAll('[data-motion-field],[data-motion-property]')].map(input => {
  const rect = input.getBoundingClientRect();
  return {field:input.dataset.motionField || input.dataset.motionProperty, value:input.value,
    rect:[rect.x,rect.y,rect.width,rect.height],
    hit:document.elementFromPoint(rect.x+rect.width/2,rect.y+rect.height/2)?.outerHTML.slice(0,130)};
})));
console.log(await page.screenshot({path:'/Users/leesungmin/Desktop/Loretune/.omo/evidence/first-demo-20261028/rehearsal-motion-inputs.png'}));
