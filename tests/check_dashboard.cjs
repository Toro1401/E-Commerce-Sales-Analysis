const fs=require('fs'),vm=require('vm'),assert=require('assert');
for(const [kind,path] of [['ecommerce',require('path').join(__dirname,'../dashboard/index.html')]]){
 const html=fs.readFileSync(path,'utf8');
 const data=html.match(/<script id="payload" type="application\/json">([\s\S]*?)<\/script>/)[1];
 const code=html.match(/<\/script><script>([\s\S]*?)<\/script>/)[1];
 const elements={};
 function element(tag){return {_id:'',value:'',textContent:'',innerHTML:'',style:{},children:[],get id(){return this._id},set id(x){this._id=x;elements[x]=this},append(child){this.children.push(child)},get selectedOptions(){return this.children.filter(c=>String(c.value)===String(this.value))},click(){}}}
 const document={getElementById(id){return elements[id]||(elements[id]=element('div'))},createElement:element};
 document.getElementById('payload').textContent=data;
 const context=vm.createContext({document,Intl,console,setTimeout,Blob,URL});
 vm.runInContext(code,context,{timeout:5000});
 const cards=()=>document.getElementById('cards').innerHTML;
 if(kind==='ecommerce'){
  document.getElementById('period').value='all';vm.runInContext('draw()',context);
  assert(cards().includes('96,478'));
  assert(cards().includes('13.221.498'));
  document.getElementById('category').value='health_beauty';vm.runInContext('draw()',context);
  assert(cards().includes('Unavailable for category selection'));
  document.getElementById('state').value='SP';vm.runInContext('draw()',context);
  assert(document.getElementById('table').innerHTML.includes('SP'));
 }else{
  assert(document.getElementById('year').value===2025);
  const before=cards();document.getElementById('search').value='NONEXISTENT';vm.runInContext('draw()',context);
  assert.equal(cards(),before);assert(!document.getElementById('table').innerHTML.includes('<td>'));
  document.getElementById('year').value=2017;vm.runInContext('draw()',context);
  assert(cards().includes('Unavailable'));
  assert(document.getElementById('scope').textContent.includes('11 observed months'));
  assert(document.getElementById('hours').innerHTML.includes('Sun'));
 }
 console.log(kind+': JavaScript and filter checks passed');
}
