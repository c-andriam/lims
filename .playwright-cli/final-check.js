async page => {
 await page.goto('http://localhost:8080/senaite/samples/ar_add');
 const names = ['SampleCode','CodeArticle','Designation','ReceptionWeight','QuantityReceived','QuantityUnderAnalysis','TechSampleWeight','ReceptionTemperature','SampleCondition','PackagingCondition','Origin','SupplierCustomerDetail','Receptionist','Contract','EntryVoucher','AnalysisSheetNumber','DateReceived'];
 const required = await page.locator('tr[fieldName]').evaluateAll(rows => rows.filter(r => r.querySelector('.fieldRequired,.required')).map(r => r.getAttribute('fieldName')));
 for (const name of names) if (!required.includes(name)) throw new Error('Missing required marker: '+name);
 const res = await page.request.post('http://localhost:8080/senaite/samples/ajax_ar_add/submit', {form:{ar_count:'1'}});
 const empty = await res.json();
 if (!empty.errors || empty.redirect_to) throw new Error('False success');
 const counts = {};
 for (const path of ['/samples/view/folderitems','/trimeta-dashboard/folderitems']) {
  const response = await page.request.post('http://localhost:8080/senaite'+path,{data:{pagesize:1000,review_state:'all'}});
  const data = await response.json(); counts[path]={total:data.total, ids:data.folderitems.map(r=>r.id),sort:data.content_filter.sort_on};
  if (data.total!==6) throw new Error('Existing sample count changed');
 }
 return {requiredFields:names.length,emptyFormError:empty.errors.message,lists:counts};
}