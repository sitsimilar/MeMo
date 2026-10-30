const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const src=fs.readFileSync('web/app.js','utf8');const project=src.slice(src.indexOf('function project('),src.indexOf('function drawFrame('));const scope={yaw:0,pitch:0,zoom:1};vm.createContext(scope);vm.runInContext(project,scope);
for(const z of [-1000,-500,-450])assert.equal(scope.project({x:0,y:0,z},800,600),null);
for(const z of [-449,0,10000]){let p=scope.project({x:0,y:0,z},800,600);assert(p.s>0&&Number.isFinite(p.x))}
scope.yaw=0.3;scope.pitch=0.2;assert.equal(scope.project({x:0,y:0,z:-1000},800,600),null);
let scheduled=0;scope.requestAnimationFrame=()=>scheduled++;scope.drawFrame=()=>{throw Error('injected renderer fault')};scope.points=[];const message={};scope.$=()=>message;
vm.runInContext(src.slice(src.indexOf('function draw(){'),src.indexOf('function hit(')),scope);scope.draw();assert.equal(scheduled,1);assert(message.textContent.includes('injected renderer fault'));
console.log('projection: behind/near clipping, valid projection, reviewed coordinates, animation reschedule passed (Node unit test, not browser)');
