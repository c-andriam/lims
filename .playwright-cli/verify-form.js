async page => {
  const fields = await page.locator('tr[fieldName]').evaluateAll(rows => rows.map(r => ({name:r.getAttribute('fieldName'), label:r.cells[0].innerText, required:!!r.querySelector('.required')})).filter(r => /SampleCode|CodeArticle|ReceptionWeight|DateReceived|AnalysisSheetNumber/.test(r.name)));
  console.log(JSON.stringify(fields));
  const response = await page.request.post('http://localhost:8080/senaite/samples/ajax_ar_add/submit', {form:{ar_count:'1','SampleCode-0':'TEST-INVALID-NOT-SAVED'}});
  const data = await response.json();
  if (!data.errors || data.redirect_to || !data.errors.fielderrors['DateReceived-0']) throw new Error('Required validation failed');
  console.log('PASS: real HTTP form endpoint rejects incomplete sample, with DateReceived error and no redirect');
  await page.getByRole('button', {name:'Enregistrer', exact:true}).click();
  await page.waitForTimeout(800);
  const messages = await page.locator('.portalMessage.alert-danger').filter({visible:true}).allTextContents();
  if (!messages.length) throw new Error('No visible error message'); return {fields, messages, url:page.url()};
  if (!page.url().includes('/ar_add')) throw new Error('Failed form unexpectedly redirected');
}