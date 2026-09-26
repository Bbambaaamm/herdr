import * as THREE from 'three';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { createQuantumCore } from './machine-core.js';
import { createMachineDrone, createMachineCity } from './machine-entities.js';

const AGENTS = ['majak-hermes','majak-codex','quantlab-hermes','quantlab-codex'];
const vector = (x,y,z) => new THREE.Vector3(x,y,z);
const DRONE_STATE = {working:'working',blocked:'waiting_user',done:'complete',idle:'idle',unknown:'offline',offline:'offline'};
const DISCONNECTED = new Set(['offline','unavailable','unknown','disconnected']);

function safeLabelCenter(x, width, labelWidth, margin = 12) {
  const inset = Math.min(width / 2, labelWidth / 2 + margin);
  return Math.max(inset, Math.min(width - inset, x));
}

function visibleDroneSpread(aspect, fov, distance, scale, width) {
  const halfWidth = Math.tan(fov * Math.PI / 360) * distance * aspect;
  const labelMargin = 24 / width * halfWidth * 2;
  // Include the full machine silhouette and the greatest cosmetic X displacement.
  const available = Math.max(0, halfWidth - 1.4 * scale - .18 - labelMargin);
  return Math.min(aspect < 1 ? 2.48 : Math.min(5.35, aspect * 2.58), available);
}

export function createMachineScene(canvas, fallback) {
  const renderer = new THREE.WebGLRenderer({canvas, antialias:true, powerPreference:'high-performance'});
  const low = innerWidth < 760 || (navigator.deviceMemory && navigator.deviceMemory <= 4);
  let pixelRatio = Math.min(devicePixelRatio, low ? 1 : 1.5);
  renderer.setPixelRatio(pixelRatio);
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.2;
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x101516);
  scene.fog = new THREE.FogExp2(0x202728, .032);
  const camera = new THREE.PerspectiveCamera(35, 1, .1, 90);
  camera.position.set(.35,.55,13.8);
  camera.lookAt(0,.35,0);
  const pmrem = new THREE.PMREMGenerator(renderer);
  const environment = new RoomEnvironment();
  const envTexture = pmrem.fromScene(environment,.08).texture;
  scene.environment = envTexture;
  scene.environmentIntensity = .72;
  environment.dispose(); pmrem.dispose();
  scene.add(new THREE.HemisphereLight(0xbac8cf,0x271707,1.25));
  const key = new THREE.DirectionalLight(0xd0dae0,4.5); key.position.set(-5,7,8);scene.add(key);
  const fill = new THREE.DirectionalLight(0xd1a776,1.5);fill.position.set(5,1,6);scene.add(fill);
  const rim = new THREE.DirectionalLight(0xffb457,6);rim.position.set(4,6,-6);scene.add(rim);
  const bottom = new THREE.PointLight(0xf78d27,13,14,2);bottom.position.set(-1,-3,3);scene.add(bottom);
  const core = createQuantumCore({low});
  const corePivot = new THREE.Group();corePivot.position.set(0,.42,-.35);corePivot.add(core.group);scene.add(corePivot);
  const city = createMachineCity({low});scene.add(city.group);
  const drones = new Map();
  for(const [index,id] of AGENTS.entries()) {
    const drone=createMachineDrone({kind:id.endsWith('hermes')?'hermes':'codex',seed:index+71,low});
    drone.group.userData.agentId=id; drone.base=vector(0,0,0);drone.id=id;drone.status='offline';
    drone.group.traverse(object=>{object.userData.agentId=id;});scene.add(drone.group);drones.set(id,drone);
  }
  // No pre-baked communication: this geometry is visible exclusively in explicit demo events.
  const linkGeometry = new THREE.BufferGeometry();linkGeometry.setAttribute('position',new THREE.BufferAttribute(new Float32Array(65*3),3));
  const link = new THREE.Line(linkGeometry,new THREE.LineBasicMaterial({color:0x89ddb0,transparent:true,opacity:.32}));link.visible=false;scene.add(link);
  const packets = new THREE.InstancedMesh(new THREE.SphereGeometry(.028,6,4),new THREE.MeshBasicMaterial({color:0xbfffc7}),12);packets.visible=false;scene.add(packets);
  const packetMatrix=new THREE.Matrix4(), packetScale=vector(1,1,1), packetQ=new THREE.Quaternion();
  const composer = new EffectComposer(renderer);composer.addPass(new RenderPass(scene,camera));
  const bloom = new UnrealBloomPass(new THREE.Vector2(1,1),.38,.38,1.18);composer.addPass(bloom);composer.addPass(new OutputPass());
  let state='offline', reduced=matchMedia('(prefers-reduced-motion: reduce)').matches,active=true,lost=false,dirty=true;
  let demo={enabled:false,state:'idle',target:'majak-codex'},focus=null,select=()=>{},inspection=0;
  let clockTime=0,lastTime=0,frame=0,slowFrames=0,adapted=false;
  let pointerX=0,pointerY=0;
  let activity={running:0,pending:0,blocked:0,workingAgents:0,activeAgent:null};
  const raycaster=new THREE.Raycaster(),mouse=new THREE.Vector2(),projected=new THREE.Vector3();
  const visibleDrone=id=>{const drone=drones.get(id);return drone?.group.visible?drone:null;};
  function failScene(error) {
    if(lost)return;
    lost=true;cancelAnimationFrame(frame);frame=0;fallback.hidden=false;
    canvas.dispatchEvent(new CustomEvent('scene-unavailable',{bubbles:true}));
    if(error)console.error('Machine City renderer unavailable',error);
  }
  const resize=()=>{
    if(lost)return;
    try{
      const {width,height}=canvas.getBoundingClientRect();if(!width||!height)return;
      camera.aspect=width/height;camera.position.z=camera.aspect<1?17.6:13.8;camera.updateProjectionMatrix();camera.updateMatrixWorld();
      renderer.setSize(width,height,false);composer.setSize(width,height);
      const scale=camera.aspect<1?.48:.7;
      const direction=camera.getWorldDirection(vector(0,0,0));
      [...drones.values()].forEach((drone,i)=>{
        const z=i%2===0?.5:1.05;
        const spread=visibleDroneSpread(camera.aspect,camera.fov,Math.max(.1,camera.position.z-z-.25),scale,width);
        const centerX=camera.position.x+(z-camera.position.z)/direction.z*direction.x;
        drone.base.set(centerX+(i<2?-spread:spread),i%2===0?2.15:-1.1,z);
        drone.group.scale.setScalar(scale);drone.group.position.copy(drone.base);
      });dirty=true;
    }catch(error){failScene(error);}
  };
  const ro=new ResizeObserver(resize);ro.observe(canvas);
  canvas.addEventListener('pointermove',e=>{const r=canvas.getBoundingClientRect();pointerX=(e.clientX-r.left)/r.width-.5;pointerY=(e.clientY-r.top)/r.height-.5;});
  canvas.addEventListener('pointerleave',()=>{pointerX=0;pointerY=0;});
  canvas.addEventListener('click',e=>{
    if(lost||!active)return;
    const r=canvas.getBoundingClientRect();if(!r.width||!r.height)return;
    mouse.set((e.clientX-r.left)/r.width*2-1,-(e.clientY-r.top)/r.height*2+1);
    raycaster.setFromCamera(mouse,camera);
    const hit=raycaster.intersectObjects([...drones.values()].filter(d=>d.group.visible).map(d=>d.group),true).find(intersection=>{
      for(let object=intersection.object;object;object=object.parent)if(!object.visible)return false;
      return Boolean(visibleDrone(intersection.object.userData.agentId));
    });
    if(hit)select(hit.object.userData.agentId);
  });
  canvas.addEventListener('webglcontextlost',event=>{event.preventDefault();failScene();});
  // A clean reload rebuilds GPU resources; existing data remains accessible without that reload.
  canvas.addEventListener('webglcontextrestored',()=>{fallback.hidden=false;});
  document.addEventListener('visibilitychange',()=>{lastTime=0;dirty=true;});
  function projectLabels() {
    scene.updateMatrixWorld();camera.updateMatrixWorld();
    const rect=canvas.getBoundingClientRect();if(!rect.width||!rect.height)return;
    for(const [id,drone] of drones){
      const button=document.querySelector(`#film-view [data-agent="${id}"]`);if(!button||!drone.group.visible)continue;
      drone.group.getWorldPosition(projected);projected.y-=.78*drone.group.scale.x;projected.project(camera);
      const parentRect=button.offsetParent?.getBoundingClientRect()||rect;
      const x=safeLabelCenter((projected.x*.5+.5)*rect.width,rect.width,button.offsetWidth);
      button.style.setProperty('--agent-x',`${rect.left-parentRect.left+x}px`);
      button.style.setProperty('--agent-y',`${rect.top-parentRect.top+(-projected.y*.5+.5)*rect.height}px`);
    }
  }
  function draw(now){
    frame=0;
    if(lost)return;
    try{
    if(document.hidden||!active||(reduced&&!dirty)){frame=requestAnimationFrame(draw);return;}
    const delta=lastTime?Math.min((now-lastTime)/1000,.08):1/60;lastTime=now;
    if(!reduced)clockTime+=delta;
    const t=reduced?0:clockTime;
    const coreStill=reduced||DISCONNECTED.has(state);
    corePivot.rotation.y=inspection?inspection:(coreStill?0:t*.028+pointerX*.11);
    corePivot.rotation.x=coreStill?0:-pointerY*.07+Math.sin(t*.17)*.025;
    const workingAgents=[...drones.values()].filter(drone=>drone.group.visible&&drone.status==='working').length;
    core.update({time:t,state,reduced,delta,activity:{...activity,workingAgents}});city.update({time:t,reduced});
    let i=0;for(const drone of drones.values()){
      const phase=i*1.83;
      const droneState=demo.enabled?(drone.id===demo.target?state:'idle'):DRONE_STATE[drone.status]||'offline';
      drone.group.position.copy(drone.base);
      if(!reduced&&!DISCONNECTED.has(droneState)){drone.group.position.x+=Math.sin(t*.24+phase)*.18;drone.group.position.y+=Math.sin(t*.37+phase)*.15;drone.group.position.z+=Math.cos(t*.22+phase)*.25;}
      drone.group.rotation.y=drone.base.x<0?.3:-.3;
      drone.update({time:t,state:droneState,reduced,delta});i++;
    }
    const liveTarget=activity.activeAgent?visibleDrone(activity.activeAgent):[...drones.values()].find(drone=>drone.group.visible&&['working','blocked'].includes(drone.status));
    const communicationTarget=demo.enabled?visibleDrone(demo.target):liveTarget;
    const communicationState=demo.enabled?state:((state==='waiting_user'||(activity.blocked||0)>0||communicationTarget?.status==='blocked')?'waiting_user':'working');
    const communication=Boolean(communicationTarget&&(demo.enabled?['delegating','waiting_result','complete','tool'].includes(state):['working','waiting_user'].includes(communicationState)));
    link.visible=communication;packets.visible=communication&&communicationState!=='waiting_user';
    if(communication){
      const end=communicationTarget.group.position;
      const curve=new THREE.QuadraticBezierCurve3(vector(end.x<0?-1.55:1.55,.5,.6),vector(end.x*.56,end.y-.42,2.05),end.clone());
      const points=curve.getPoints(64);linkGeometry.setFromPoints(points);
      const linkColor=communicationState==='waiting_user'?0xff7864:(end.x<0?0xffb657:0x73f2df);
      link.material.color.setHex(linkColor);packets.material.color.setHex(linkColor);
      link.material.opacity=communicationState==='waiting_user'?.2:.43;
      for(let n=0;n<12;n++){let f=reduced?(n+1)/13:(t*(.3+Math.min(activity.running||0,2)*.08)+n/12)%1;if(demo.enabled&&state==='complete')f=1-f;packetMatrix.compose(curve.getPoint(f),packetQ,packetScale);packets.setMatrixAt(n,packetMatrix);}packets.instanceMatrix.needsUpdate=true;
    }
    projectLabels();
    composer.render();
    dirty=false;
    if(!reduced&&delta>.048)slowFrames++;else slowFrames=Math.max(0,slowFrames-1);
    if(slowFrames>90&&!adapted){pixelRatio=1;renderer.setPixelRatio(1);composer.setPixelRatio(1);bloom.enabled=false;adapted=true;resize();}
    }catch(error){failScene(error);return;}
    if(!lost)frame=requestAnimationFrame(draw);
  }
  resize();if(!lost)frame=requestAnimationFrame(draw);
  const inspect=document.querySelector('#inspect-model');
  inspect?.addEventListener('click',()=>{inspection=inspection===0?.6:inspection===.6?1.2:0;inspect.textContent=inspection===0?'Prohlédnout jádro':inspection===.6?'Jádro ze tří čtvrtin':'Jádro z boku';dirty=true;});
  return {
    setState(next){if(state!==next){state=next;dirty=true;}},setReduced(value){reduced=value;dirty=true;lastTime=0;},
    setActive(value){active=value;dirty=true;lastTime=0;if(value)resize();},setGaze(){},
    setActivity(value){activity={...activity,...value};core.setActivity(activity);dirty=true;},
    setAgents(rows){for(const drone of drones.values()){const row=rows.find(r=>(r.id||r.agent)===drone.id);drone.status=row?.status||'offline';drone.group.visible=Boolean(row)&&row.visible!==false;}if(!visibleDrone(focus))focus=null;if(!visibleDrone(demo.target))demo.target=null;dirty=true;},
    focusAgent(id){focus=visibleDrone(id)?id:null;dirty=true;},setDemo(value){demo={...demo,...value};if(!visibleDrone(demo.target))demo.target=null;dirty=true;},onSelect(callback){select=callback;},
    diagnostics(){return {geometry:'true-3d',state,reduced,active,contextLost:lost,quality:adapted?'adaptive-low':low?'low':'high',core:core.diagnostics(),drones:[...drones.values()].map(d=>({id:d.id,position:d.group.position.toArray(),...d.diagnostics()})),drawCalls:renderer.info.render.calls,triangles:renderer.info.render.triangles};},
    quality:low?'Úsporná':'Vysoká',
    dispose(){cancelAnimationFrame(frame);ro.disconnect();scene.traverse(o=>{o.geometry?.dispose();if(o.material){for(const m of Array.isArray(o.material)?o.material:[o.material])m.dispose();}});envTexture.dispose();composer.dispose();renderer.dispose();}
  };
}
