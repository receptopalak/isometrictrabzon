import * as THREE from 'three';
import { OrbitControls } from 'three/addons/controls/OrbitControls.js';

const BOX=[39.725,41.001,39.737,41.010];
const ORIGIN=[(BOX[0]+BOX[2])/2,(BOX[1]+BOX[3])/2];
const MX=111320*Math.cos(ORIGIN[1]*Math.PI/180), MZ=111132;
const W=(BOX[2]-BOX[0])*MX, D=(BOX[3]-BOX[1])*MZ;
const $=id=>document.getElementById(id);
const point=(lon,lat)=>new THREE.Vector2((lon-ORIGIN[0])*MX,-(lat-ORIGIN[1])*MZ);
let terrain=null,geojson=null,displayObjects=[],pickable=[],selected=null;
const scene=new THREE.Scene();
scene.background=new THREE.Color('#132b34');
scene.fog=new THREE.FogExp2('#132b34',0.00038);
const renderer=new THREE.WebGLRenderer({antialias:true,preserveDrawingBuffer:true});
renderer.setPixelRatio(Math.min(devicePixelRatio||1,2));
renderer.setSize(innerWidth,innerHeight);
renderer.outputColorSpace=THREE.SRGBColorSpace;
renderer.toneMapping=THREE.ACESFilmicToneMapping;
renderer.toneMappingExposure=1.4;
$('scene').appendChild(renderer.domElement);
let viewSize=1360;
const camera=new THREE.OrthographicCamera(-viewSize*innerWidth/innerHeight/2,viewSize*innerWidth/innerHeight/2,viewSize/2,-viewSize/2,0.1,10000);
const controls=new OrbitControls(camera,renderer.domElement);
controls.enableDamping=true;controls.dampingFactor=0.075;
controls.maxPolarAngle=Math.PI*.49;
controls.minDistance=60;controls.maxDistance=5500;
controls.screenSpacePanning=true;
scene.add(new THREE.HemisphereLight(0xcceaf0,0x31484c,2.1));
const sun=new THREE.DirectionalLight(0xffe8c2,3.2);
sun.position.set(-450,1000,570);scene.add(sun);
const fill=new THREE.DirectionalLight(0x78afca,0.85);
fill.position.set(360,450,-550);scene.add(fill);
const group=new THREE.Group();scene.add(group);
function status(s,bad=false){$('status').textContent=s;$('status').style.color=bad?'#f8b5aa':'#c6dcd3';}
function heightAt(lon,lat){
 if(!terrain||!$('terrain').checked)return 0;
 const [w,s,e,n]=terrain.bbox;const X=terrain.width-1,Y=terrain.height-1;
 const px=Math.max(0,Math.min(X,(lon-w)/(e-w)*X)),py=Math.max(0,Math.min(Y,(n-lat)/(n-s)*Y));
 const x=Math.floor(px),y=Math.floor(py),xx=Math.min(X,x+1),yy=Math.min(Y,y+1);
 const a=px-x,b=py-y,z=terrain.values_m;
 return ((z[y][x]*(1-a)+z[y][xx]*a)*(1-b)+(z[yy][x]*(1-a)+z[yy][xx]*a)*b)-terrain.min_m;
}
function resetCamera(){
 const h=terrain&&$('terrain').checked?(terrain.max_m-terrain.min_m)*.35:10;
 camera.position.set(1500,1350+h,1500);
 controls.target.set(0,h,0);
 camera.zoom=Math.max(.65,Math.min(1.65,innerWidth/1100));
 camera.updateProjectionMatrix();controls.update();
}
function clear(){
 for(const o of [...group.children]){group.remove(o);o.traverse(obj=>{obj.geometry?.dispose();if(obj.material)(Array.isArray(obj.material)?obj.material:[obj.material]).forEach(m=>m.dispose());});}
 displayObjects=[];pickable=[];selected=null;$('pick').textContent='Bir binaya tıklayıp kaynak bilgilerini incele.';
}
function plane(){
 const grid=terrain&&$('terrain').checked?Math.min(terrain.width,129):2;
 const rows=terrain&&$('terrain').checked?Math.min(terrain.height,129):2;
 const g=new THREE.PlaneGeometry(W,D,grid-1,rows-1);
 g.rotateX(-Math.PI/2);
 const pos=g.attributes.position,cols=[];
 const lo=new THREE.Color('#325e59'),hi=new THREE.Color('#8c9f76');
 for(let i=0;i<pos.count;i++){
  const x=pos.getX(i),z=pos.getZ(i),lon=ORIGIN[0]+x/MX,lat=ORIGIN[1]-z/MZ;
  const h=heightAt(lon,lat);pos.setY(i,h);
  const t=Math.max(0,Math.min(1,h/210));const c=lo.clone().lerp(hi,t);
  cols.push(c.r,c.g,c.b);
 }
 g.setAttribute('color',new THREE.Float32BufferAttribute(cols,3));
 g.computeVertexNormals();
 const m=new THREE.Mesh(g,new THREE.MeshStandardMaterial({vertexColors:true,side:THREE.DoubleSide,roughness:1}));
 group.add(m);
}
function ringToShape(ring){
 const shape=new THREE.Shape();
 ring.forEach(([lon,lat],i)=>{const p=point(lon,lat);if(i===0)shape.moveTo(p.x,-p.y);else shape.lineTo(p.x,-p.y);});
 shape.closePath();return shape;
}
function centroid(ring){
 let lon=0,lat=0,n=0;for(const p of ring){lon+=p[0];lat+=p[1];n++;}
 return [lon/n,lat/n];
}
function makeBuilding(feature,index){
 const g=feature.geometry;if(!g||g.type!=='Polygon'||!g.coordinates?.[0]||g.coordinates[0].length<4)return false;
 const ring=g.coordinates[0],props=feature.properties||{};
 const explicit=Number.parseFloat(String(props.height||'').replace(',','.'));
 const levels=Number.parseFloat(String(props['building:levels']??props.num_floors??'').replace(',','.'));
 const known=Number.isFinite(explicit)&&explicit>1||Number.isFinite(levels)&&levels>0;
 const h=Number.isFinite(explicit)&&explicit>1?explicit:Number.isFinite(levels)&&levels>0?levels*3.1+1:12;
 const [lon,lat]=centroid(ring),base=heightAt(lon,lat);
 try{
  const geo=new THREE.ExtrudeGeometry(ringToShape(ring),{depth:Math.max(2,Math.min(h,350)),bevelEnabled:false,curveSegments:1});
  geo.rotateX(-Math.PI/2);
  const colors=['#e0d7c1','#d5c3af','#acc2be','#b4ae9f','#e0bfa7','#d0b7a5'];
  const mat=new THREE.MeshStandardMaterial({color:colors[index%colors.length],roughness:0.86,metalness:0});
  const mesh=new THREE.Mesh(geo,mat);mesh.position.y=base+0.15;
  mesh.userData={feature,height:h,known,normalColor:mat.color.getHex()};
  group.add(mesh);pickable.push(mesh);
  if($('edges').checked){
   const edges=new THREE.LineSegments(new THREE.EdgesGeometry(geo,20),new THREE.LineBasicMaterial({color:0x253c43,transparent:true,opacity:.43}));
   edges.position.y=mesh.position.y;edges.userData.isOutline=true;group.add(edges);
  }
  return known?'known':'estimated';
 }catch(e){console.warn('Bina geometrisi oluşturulamadı:',feature.id,e);return false;}
}
function makeRoad(f){
 const coords=f.geometry?.coordinates;if(!Array.isArray(coords)||coords.length<2)return false;
 const tag=f.properties?.highway||'';
 const hw=/^(motorway|trunk|primary|secondary)$/.test(tag);
 const width=hw?10:/^(tertiary|residential|unclassified)$/.test(tag)?6:3;
 const mat=new THREE.MeshBasicMaterial({color:hw?'#b49a7e':'#718f8d',side:THREE.DoubleSide,transparent:true,opacity:.93,depthWrite:false});
 for(let i=1;i<coords.length;i++){
  const a=point(...coords[i-1]),b=point(...coords[i]);
  const dir=b.clone().sub(a);if(dir.length()<.08)continue;
  const n=new THREE.Vector2(-dir.y,dir.x).normalize().multiplyScalar(width/2);
  const g=new THREE.BufferGeometry(),p=[];
  const v=[a.clone().add(n),a.clone().sub(n),b.clone().add(n),b.clone().sub(n)];
  for(const [j,k,l] of [[0,1,2],[1,3,2]])for(const z of [v[j],v[k],v[l]]){
   const lon=ORIGIN[0]+z.x/MX,lat=ORIGIN[1]-z.y/MZ;
   p.push(z.x,heightAt(lon,lat)+.8,z.y);
  }
  g.setAttribute('position',new THREE.Float32BufferAttribute(p,3));
  g.computeVertexNormals();group.add(new THREE.Mesh(g,mat));
 }
 return true;
}
function makePark(f){
 const r=f.geometry?.coordinates?.[0];if(!Array.isArray(r)||r.length<4)return false;
 const mat=new THREE.MeshBasicMaterial({color:f.properties?.natural==='water'?'#437b83':'#558568',transparent:true,opacity:.86,side:THREE.DoubleSide,depthWrite:false});
 try{
  const shape=ringToShape(r),g=new THREE.ShapeGeometry(shape);g.rotateX(-Math.PI/2);
  const [lon,lat]=centroid(r);const m=new THREE.Mesh(g,mat);
  m.position.y=heightAt(lon,lat)+.5;group.add(m);return true;
 }catch{return false;}
}
function renderData(data){
 if(!data?.features||!Array.isArray(data.features))throw Error('GeoJSON FeatureCollection gerekli');
 clear();plane();
 const roads=data.features.filter(f=>f.geometry?.type==='LineString'&&f.properties?.highway);
 const greens=data.features.filter(f=>f.geometry?.type==='Polygon'&&!f.properties?.building);
 const buildings=data.features.filter(f=>f.geometry?.type==='Polygon'&&f.properties?.building&&f.properties.building!=='no');
 greens.forEach(makePark);let roadCount=0;roads.forEach(f=>{if(makeRoad(f))roadCount++;});
 let count=0,known=0;
 buildings.forEach((f,i)=>{const v=makeBuilding(f,i);if(v){count++;if(v==='known')known++;}});
 $('building-count').textContent=count.toLocaleString('tr-TR');
 $('road-count').textContent=roadCount.toLocaleString('tr-TR');
 $('height-count').textContent=known.toLocaleString('tr-TR');
 $('elev-count').textContent=terrain&&$('terrain').checked?Math.round(terrain.max_m-terrain.min_m)+' m':'—';
 resetCamera();status(count+' gerçek bina oturumu yüklendi. '+(count-known)+' binanın yüksekliği tahmini.'+(terrain?' Arazi: açık yükseklik verisi.':' Düz arazi.'));
}
async function readJSON(path,required=false){
 const r=await fetch(path,{cache:'no-store'});
 if(!r.ok){if(required)throw Error(path+' bulunamadı (HTTP '+r.status+')');return null;}
 return r.json();
}
async function load(){
 status('Açık Trabzon verileri yükleniyor…');
 try{
  const [data,t]=await Promise.all([readJSON('./data/trabzon.geojson',true),readJSON('./data/terrain.json')]);
  terrain=t&&Array.isArray(t.bbox)&&t.bbox.every((v,i)=>Math.abs(v-BOX[i])<1e-7)?t:null;
  geojson=data;renderData(data);
 }catch(e){status('Gerçek bina verisi yüklenemedi. GitHub Actions / Pages yayınını kontrol edin: '+e.message,true);console.error(e);}
}
const picker=new THREE.Raycaster(),mouse=new THREE.Vector2();
renderer.domElement.addEventListener('pointerup',event=>{
 if(event.button!==0)return;
 const rect=renderer.domElement.getBoundingClientRect();
 mouse.set((event.clientX-rect.left)/rect.width*2-1,-(event.clientY-rect.top)/rect.height*2+1);
 picker.setFromCamera(mouse,camera);
 const hit=picker.intersectObjects(pickable,false)[0];
 if(selected)selected.material.color.setHex(selected.userData.normalColor);
 selected=hit?.object||null;
 if(!selected){$('pick').textContent='Bir binaya tıklayıp kaynak bilgilerini incele.';return;}
 selected.material.color.set('#f3ae71');
 const {feature,height,known}=selected.userData;
 const id=feature.properties?.osm_id||feature.id||'?';
 $('pick').textContent='OSM bina: '+id+' · '+height.toFixed(1)+' m · '+(known?'Kaynakta yükseklik / kat bilgisi var':'Yükseklik tahminidir');
});
$('reset').addEventListener('click',resetCamera);
$('reload').addEventListener('click',load);
$('edges').addEventListener('change',()=>group.traverse(o=>{if(o.userData?.isOutline)o.visible=$('edges').checked;}));
$('terrain').addEventListener('change',()=>{if(geojson)renderData(geojson);});
$('capture').addEventListener('click',()=>{
 renderer.render(scene,camera);const a=document.createElement('a');
 a.download='isometric-trabzon-meydan.png';a.href=renderer.domElement.toDataURL('image/png');a.click();
});
$('loadfile').addEventListener('click',()=>$('file').click());
$('file').addEventListener('change',async e=>{
 const file=e.target.files?.[0];if(!file)return;
 try{renderData(JSON.parse(await file.text()));$('mode').textContent='Yüklenen GeoJSON';}
 catch(err){status('Dosya okunamadı: '+err.message,true);}
});
addEventListener('resize',()=>{
 renderer.setSize(innerWidth,innerHeight);
 const a=innerWidth/innerHeight;camera.left=-viewSize*a/2;camera.right=viewSize*a/2;camera.top=viewSize/2;camera.bottom=-viewSize/2;
 camera.updateProjectionMatrix();
});
function animate(){requestAnimationFrame(animate);controls.update();renderer.render(scene,camera);}
window.isometricTrabzon={camera,renderer,controls,point,heightAt};
resetCamera();animate();load();
